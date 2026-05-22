from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any, Iterable

from jarvis_portal.context import IOContext


class TsvAdapter:
    format_name = "TSV"
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
        columns, rows, _source = _read_tsv_table(path, spec, context=context)
        observables: dict[str, Any] = {}

        for operation in _iter_write_operations(spec, data, context=context):
            column = operation["column"]
            row_index = _row_index(operation.get("row", 0))
            column_index = _ensure_column(columns, rows, column, header=_has_header(spec))
            _ensure_row(rows, row_index, len(columns))

            value = operation.get("value")
            rows[row_index][column_index] = _to_cell(value)
            if operation.get("observable"):
                observables[str(operation["name"])] = value

        content = _render_tsv_table(columns, rows, header=_has_header(spec))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        _save_copy_if_requested(context, spec, path, content)
        if spec.get("save", False) and "name" in spec:
            observables[str(spec["name"])] = str(path.resolve())
        return observables

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        path = context.path(spec["path"])
        columns, rows, source = _read_tsv_table(path, spec, context=context)
        observables: dict[str, Any] = {}

        for variable in spec.get("variables", []):
            name = str(variable["name"])
            column = variable.get("column", name)
            column_index = _column_index(columns, rows, column)
            if column_index is None:
                continue

            if "row" in variable:
                row_index = _row_index(variable["row"])
                if row_index < 0 or row_index >= len(rows):
                    continue
                if column_index >= len(rows[row_index]):
                    continue
                observables[name] = _parse_cell(rows[row_index][column_index])
                continue

            values = [_parse_cell(row[column_index]) for row in rows if column_index < len(row)]
            if not values:
                continue
            observables[name] = values[0] if len(values) == 1 else values

        if source is None:
            source = _render_tsv_table(columns, rows, header=_has_header(spec))
        _save_copy_if_requested(context, spec, path, source, output_default_temp=True)
        if spec.get("save", False) and "name" in spec:
            observables[str(spec["name"])] = str(path.resolve())
        return observables


def _read_tsv_table(
    path: Path,
    spec: dict[str, Any],
    *,
    context: IOContext | None = None,
) -> tuple[list[str], list[list[str]], str | None]:
    if not path.exists():
        _log_error(context, f"File not found: {path}")
        return _columns_from_spec(spec), [], None

    source = path.read_text(encoding="utf-8")
    if not source.strip():
        return _columns_from_spec(spec), [], source

    parsed_rows = [list(row) for row in csv.reader(StringIO(source), delimiter="\t")]
    if _has_header(spec):
        if parsed_rows:
            return [str(item) for item in parsed_rows[0]], parsed_rows[1:], source
        return _columns_from_spec(spec), [], source
    return _columns_from_spec(spec), parsed_rows, source


def _render_tsv_table(columns: list[str], rows: list[list[str]], *, header: bool) -> str:
    width = len(columns) if columns else max((len(row) for row in rows), default=0)
    normalized_rows = [_padded(row, width) for row in rows]
    stream = StringIO()
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    if header:
        writer.writerow(_padded(columns, width))
    writer.writerows(normalized_rows)
    return stream.getvalue()


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
            yield _operation_from_variable(variable, data, context=context)


def _operation_from_variable(
    variable: dict[str, Any],
    data: dict[str, Any],
    *,
    context: IOContext,
) -> dict[str, Any]:
    if "column" not in variable:
        raise ValueError("TSV input variables require an explicit 'column'.")

    name = variable["name"]
    observable = False
    if "expression" in variable:
        value = _evaluate_expression(context, str(variable["expression"]), data)
        observable = True
    else:
        value = data.get(name, "MISSING_VALUE")

    item = {
        "name": name,
        "value": value,
        "column": variable["column"],
        "observable": observable,
    }
    if "row" in variable:
        item["row"] = variable["row"]
    return item


def _evaluate_expression(context: IOContext, expression: str, data: dict[str, Any]) -> Any:
    if context.evaluate_expression is None:
        raise ValueError(
            "TSV input variable uses 'expression', but IOContext.evaluate_expression is not set."
        )
    return context.evaluate_expression(expression, data)


def _has_header(spec: dict[str, Any]) -> bool:
    return bool(spec.get("header", True))


def _columns_from_spec(spec: dict[str, Any]) -> list[str]:
    return [str(item) for item in spec.get("columns", [])]


def _ensure_column(
    columns: list[str],
    rows: list[list[str]],
    column: Any,
    *,
    header: bool,
) -> int:
    if isinstance(column, int):
        if column < 0:
            raise ValueError("TSV column index must be non-negative.")
        while len(columns) <= column:
            columns.append(f"column_{len(columns)}")
        for row in rows:
            _pad_in_place(row, len(columns))
        return column

    text = str(column)
    if text in columns:
        return columns.index(text)
    if not header and not columns:
        raise ValueError("TSV string columns require header: true or explicit columns.")
    columns.append(text)
    for row in rows:
        _pad_in_place(row, len(columns))
    return len(columns) - 1


def _column_index(columns: list[str], rows: list[list[str]], column: Any) -> int | None:
    if isinstance(column, int):
        if column < 0:
            return None
        width = max([len(columns), *(len(row) for row in rows)], default=0)
        return column if column < width else None

    text = str(column)
    if text not in columns:
        return None
    return columns.index(text)


def _ensure_row(rows: list[list[str]], row_index: int, width: int) -> None:
    if row_index < 0:
        raise ValueError("TSV row index must be non-negative.")
    while len(rows) <= row_index:
        rows.append([""] * width)
    _pad_in_place(rows[row_index], width)


def _row_index(value: Any) -> int:
    index = int(value)
    if index < 0:
        raise ValueError("TSV row index must be non-negative.")
    return index


def _pad_in_place(row: list[str], width: int) -> None:
    while len(row) < width:
        row.append("")


def _padded(row: list[str], width: int) -> list[str]:
    padded = list(row)
    _pad_in_place(padded, width)
    return padded


def _to_cell(value: Any) -> str:
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except ValueError:
            pass
    return str(value)


def _parse_cell(value: str) -> Any:
    text = str(value).strip()
    if text == "":
        return ""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
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
