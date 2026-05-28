from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jarvis_portal import wolframdict
from jarvis_portal.context import IOContext


class WolframAdapter:
    format_name = "Wolfram"
    direction = "both"

    async def write_input(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await context.run_blocking(self._write_sync, context, spec, data)

    async def read_output(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        return await context.run_blocking(self._read_sync, context, spec)

    def _write_sync(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        path = context.path(spec["path"])
        payload = _read_wolfram_document(path, context=context)
        observables: dict[str, Any] = {}

        for operation in _iter_write_operations(
            spec,
            data,
            context=context,
        ):
            value = _to_wolfram_compatible(operation.get("value"))
            entry = operation.get("entry")
            name = operation.get("name")
            if operation.get("observable") and name:
                observables[str(name)] = value
            if entry:
                _set_nested(payload, str(entry), value)
            elif name:
                payload[str(name)] = value

        path.parent.mkdir(parents=True, exist_ok=True)
        wolfram_text = wolframdict.dumps(_to_wolfram_compatible(payload), indent=2)
        path.write_text(wolfram_text, encoding="utf-8")

        _save_copy_if_requested(context, spec, path, wolfram_text)
        if spec.get("save", False) and "name" in spec:
            observables[str(spec["name"])] = str(path.resolve())
        return observables

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        path = context.path(spec["path"])
        source = path.read_text(encoding="utf-8") if path.exists() else None
        payload = (
            _read_wolfram_document_from_text(source, path, context=context)
            if source is not None
            else _read_wolfram_document(path, context=context)
        )
        observables: dict[str, Any] = {}
        for variable in spec.get("variables", []):
            name = variable["name"]
            entry = variable.get("entry")
            observables[name] = _get_nested(payload, str(entry)) if entry else payload.get(name)

        if source is None:
            source = wolframdict.dumps(_to_wolfram_compatible(payload), indent=2)
        _save_copy_if_requested(context, spec, path, source, output_default_temp=True)
        if spec.get("save", False) and "name" in spec:
            observables[str(spec["name"])] = str(path.resolve())
        return observables


def _read_wolfram_document(path: Path, *, context: IOContext | None = None) -> dict[str, Any]:
    if not path.exists():
        _log_error(context, f"File not found: {path}")
        return {}
    text = path.read_text(encoding="utf-8")
    return _read_wolfram_document_from_text(text, path, context=context)


def _read_wolfram_document_from_text(
    text: str,
    path: Path,
    *,
    context: IOContext | None = None,
) -> dict[str, Any]:
    if not text.strip():
        return {}
    try:
        payload = wolframdict.loads(text)
    except ValueError:
        _log_error(context, f"Error decoding Wolfram Association from file: {path}")
        return {}
    if not isinstance(payload, dict):
        raise TypeError(f"Wolfram document must be an Association: {path}")
    return payload


def _iter_write_operations(
    spec: dict[str, Any],
    data: dict[str, Any],
    *,
    context: IOContext,
) -> Iterable[dict[str, Any]]:
    for action in spec.get("actions", []):
        if action.get("type") != "Dump":
            continue
        for variable in action.get("variables", []):
            yield _operation_from_variable(
                variable,
                data,
                context=context,
            )


def _operation_from_variable(
    variable: dict[str, Any],
    data: dict[str, Any],
    *,
    context: IOContext,
) -> dict[str, Any]:
    name = variable["name"]
    observable = False
    if "expression" in variable:
        value = _evaluate_expression(context, str(variable["expression"]), data)
        observable = True
    else:
        value = data.get(name, "MISSING_VALUE")

    item = {"name": name, "value": value, "observable": observable}
    if "entry" in variable:
        item["entry"] = variable["entry"]
    return item


def _evaluate_expression(context: IOContext, expression: str, data: dict[str, Any]) -> Any:
    if context.evaluate_expression is None:
        raise ValueError(
            "Wolfram input variable uses 'expression', but IOContext.evaluate_expression is not set."
        )
    return context.evaluate_expression(expression, data)


def _set_nested(payload: dict[str, Any], entry: str, value: Any) -> None:
    parts = [part for part in entry.split(".") if part]
    if not parts:
        raise ValueError("Wolfram entry path must not be empty.")
    current: Any = payload
    for part in parts[:-1]:
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:
                raise ValueError(
                    f"Wolfram entry '{entry}' uses non-numeric list index '{part}'."
                ) from exc
            if index < 0:
                raise ValueError(f"Wolfram entry '{entry}' uses negative list index '{part}'.")
            try:
                current = current[index]
            except IndexError as exc:
                raise ValueError(
                    f"Wolfram entry '{entry}' uses out-of-range list index '{part}'."
                ) from exc
            continue
        if not isinstance(current, dict):
            raise ValueError(f"Wolfram entry '{entry}' crosses non-Association key '{part}'.")
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, (dict, list)):
            raise ValueError(f"Wolfram entry '{entry}' crosses scalar key '{part}'.")
        current = next_value

    last = parts[-1]
    if isinstance(current, list):
        try:
            index = int(last)
        except ValueError as exc:
            raise ValueError(f"Wolfram entry '{entry}' cannot set list index '{last}'.") from exc
        if index < 0:
            raise ValueError(f"Wolfram entry '{entry}' uses negative list index '{last}'.")
        try:
            current[index] = value
        except IndexError as exc:
            raise ValueError(f"Wolfram entry '{entry}' cannot set list index '{last}'.") from exc
        return
    if not isinstance(current, dict):
        raise ValueError(f"Wolfram entry '{entry}' crosses non-Association target.")
    current[last] = value


def _get_nested(payload: dict[str, Any], entry: str) -> Any:
    current: Any = payload
    for part in [part for part in entry.split(".") if part]:
        if isinstance(current, list):
            try:
                index = int(part)
            except (ValueError, IndexError):
                return None
            if index < 0:
                return None
            try:
                current = current[index]
            except IndexError:
                return None
            continue
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
            continue
        return None
    return current


def _to_wolfram_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_wolfram_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_wolfram_compatible(item) for item in value]
    if hasattr(value, "tolist") and callable(value.tolist):
        return _to_wolfram_compatible(value.tolist())
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except ValueError:
            return value
    return value


def _save_copy_if_requested(
    context: IOContext,
    spec: dict[str, Any],
    source_path: Path,
    content: str,
    *,
    output_default_temp: bool = False,
) -> str | None:
    save = bool(spec.get("save", False))
    if not save and not output_default_temp:
        return None
    if context.sample_save_dir is None:
        return None

    base_dir = Path(context.sample_save_dir)
    if not save and output_default_temp:
        base_dir = base_dir / ".temp"
    base_dir.mkdir(parents=True, exist_ok=True)

    module = context.module or spec.get("module")
    filename = source_path.name if module is None else f"{source_path.name}@{module}"
    target = base_dir / filename
    target.write_text(content, encoding="utf-8")
    return str(target)


def _log_error(context: IOContext | None, message: str) -> None:
    logger = getattr(context, "logger", None)
    if logger is not None and hasattr(logger, "error"):
        logger.error(message)
