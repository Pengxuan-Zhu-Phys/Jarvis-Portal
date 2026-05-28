from __future__ import annotations

import ast
import json
import math
import operator
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from jarvis_portal import IOContext, __version__, create_default_registry

DIM = "\033[2m"
RESET = "\033[0m"
CDOT = "·"


def render_help() -> str:
    return "\n".join(
        [
            "usage:",
            "  jportal file",
            "  jportal man",
            "  jportal -h",
            "  jportal -v",
            "",
            "positional arguments:",
            "  file  run a YAML file and print observables",
            "  man   show the manual; use 'jportal man' for format topics",
            "",
            "options:",
            "  -h, --help     show this help message and exit",
            "  -v, --version  print Jarvis-Portal version and exit",
        ]
    )


def _print_usage_error(message: str) -> int:
    print(f"jportal: error: {message}", file=sys.stderr)
    print("usage: jportal file | jportal man | jportal -h | jportal -v", file=sys.stderr)
    return 2


def load_yaml_dict(path: str | Path) -> dict[str, Any]:
    input_path = Path(path).expanduser()
    if not input_path.exists():
        raise FileNotFoundError(f"YAML file not found: {input_path}")
    if not input_path.is_file():
        raise IsADirectoryError(f"YAML path is not a file: {input_path}")

    with input_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise TypeError("YAML top-level document must be a mapping so jportal can return a dict.")
    return payload


def render_observables(observables: dict[str, Any]) -> str:
    return json.dumps(observables, ensure_ascii=False, indent=2)


def evaluate_runtime_expression(expression: str, values: Mapping[str, Any]) -> Any:
    names = {"Pi": math.pi, "pi": math.pi, "PI": math.pi, **dict(values)}
    node = ast.parse(expression, mode="eval")
    return _eval_expression_node(node.body, names)


def _eval_expression_node(node: ast.AST, names: Mapping[str, Any]) -> Any:
    binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in names:
            raise ValueError(f"Unknown expression symbol: {node.id}")
        return names[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
        return binary_ops[type(node.op)](
            _eval_expression_node(node.left, names),
            _eval_expression_node(node.right, names),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
        return unary_ops[type(node.op)](_eval_expression_node(node.operand, names))
    raise ValueError(f"Unsupported expression syntax: {ast.unparse(node)}")


def _cdots(count: int, *, dim: bool) -> str:
    marker = CDOT * count
    if dim:
        return f"{DIM}{marker}{RESET}"
    return marker


def render_manual(topic: str | None = None, *, dim_markers: bool = False) -> str:
    if topic is None:
        registry = create_default_registry()
        return "\n".join(
            [
                "Jarvis-Portal manual",
                "",
                "Supported formats:",
                f"  input: {', '.join(registry.available_formats('input'))}",
                f"  output: {', '.join(registry.available_formats('output'))}",
                "",
                "Format manuals:",
                "  csv",
                "  dat",
                "  json",
                "  tsv",
                "  wolfram",
                "",
                "Usage:",
                "  jportal file",
                "  jportal man",
                "  jportal man json",
                "  jportal man csv",
                "  jportal man tsv",
                "  jportal man dat",
                "  jportal man wolfram",
                "  jportal -h",
                "  jportal -v",
            ]
        )

    normalized = str(topic).strip().casefold()
    if normalized == "json":
        d1 = _cdots(1, dim=dim_markers)
        d2 = _cdots(2, dim=dim_markers)
        d4 = _cdots(4, dim=dim_markers)
        d6 = _cdots(6, dim=dim_markers)
        d8 = _cdots(8, dim=dim_markers)
        d10 = _cdots(10, dim=dim_markers)
        return "\n".join(
            [
                "JSON format manual",
                "",
                "YAML shape:",
                "  ┌─ YAML ─────────────────────────────",
                "  │ observables:",
                f"  │ {d2}x: 1.0",
                f"  │ {d2}y: 2.0",
                "  │",
                "  │ input:",
                f"  │ {d2}- name: params",
                f"  │ {d4}path: input.json",
                f"  │ {d4}type: JSON",
                f"  │ {d4}actions:",
                f"  │ {d6}- type: Dump",
                f"  │ {d8}variables:",
                f"  │ {d10}- {{ name: \"xx\", expression: \"x * Pi\" }}",
                f"  │ {d10}- {{ name: \"yy\", expression: \"y * Pi\" }}",
                (
                    f"  │ {d10}- {{ name: \"cx\", expression: \"(x + y) * Pi\", "
                    'entry: "test.config.x" }'
                ),
                "  │",
                "  │ output:",
                f"  │ {d2}- name: observables",
                f"  │ {d4}path: output.json",
                f"  │ {d4}type: JSON",
                f"  │ {d4}variables:",
                f"  │ {d6}- {{ name: \"z\" }}",
                f"  │ {d6}- {{ name: \"likelihood\", entry: \"fit.loglike\" }}",
                "  └───────────────────────────────────",
                "",
                "Note:",
                f"  {d1} means one indentation space. Replace {d1} with spaces before use.",
                "  Top-level observables supplies runtime values for input expressions.",
                "",
                "Observables contract:",
                "  Returns the flat observable dictionary directly.",
                "  Output variables contribute name: value items.",
                "  Plain input variables are written to files and do not become observables.",
                "  Expression input variables return their evaluated name: value items.",
                "  A file spec name is returned only when save: true.",
                "  Saved file spec names map to resolved absolute paths.",
                "",
                "Screen output:",
                "  {",
                '    "xx": 3.141592653589793,',
                '    "yy": 6.283185307179586,',
                '    "cx": 9.42477796076938,',
                '    "z": 42.0,',
                '    "likelihood": -1.25',
                "  }",
            ]
        )

    if normalized in {"csv", "tsv", "dat"}:
        return _render_table_manual(normalized, dim_markers=dim_markers)

    if normalized == "wolfram":
        d1 = _cdots(1, dim=dim_markers)
        d2 = _cdots(2, dim=dim_markers)
        d4 = _cdots(4, dim=dim_markers)
        d6 = _cdots(6, dim=dim_markers)
        d8 = _cdots(8, dim=dim_markers)
        d10 = _cdots(10, dim=dim_markers)
        return "\n".join(
            [
                "Wolfram format manual",
                "",
                "File type: Wolfram Language Association (.wl)",
                "",
                "YAML shape:",
                "  ┌─ YAML ─────────────────────────────",
                "  │ observables:",
                f"  │ {d2}x: 1.0",
                f"  │ {d2}y: 2.0",
                "  │",
                "  │ input:",
                f"  │ {d2}- name: params",
                f"  │ {d4}path: input.wl",
                f"  │ {d4}type: Wolfram",
                f"  │ {d4}actions:",
                f"  │ {d6}- type: Dump",
                f"  │ {d8}variables:",
                f"  │ {d10}- {{ name: \"xx\", expression: \"x * Pi\" }}",
                f"  │ {d10}- {{ name: \"mass\", entry: \"SMParameters.HiggsMass\" }}",
                (
                    f"  │ {d10}- {{ name: \"bb\", expression: \"x / y\", "
                    'entry: "BranchingFractions.bb" }'
                ),
                "  │",
                "  │ output:",
                f"  │ {d2}- name: observables",
                f"  │ {d4}path: output.wl",
                f"  │ {d4}type: Wolfram",
                f"  │ {d4}variables:",
                f"  │ {d6}- {{ name: \"entropy\", entry: \"LinearEntropy\" }}",
                f"  │ {d6}- {{ name: \"BR_bb\", entry: \"Channels.0.BR\" }}",
                "  └───────────────────────────────────",
                "",
                "Note:",
                f"  {d1} means one indentation space. Replace {d1} with spaces before use.",
                "  Wolfram entries use the same dotted paths as JSON.",
                "  Numeric path parts index lists only when the current value is a list.",
                "",
                "Observables contract:",
                "  Returns the flat observable dictionary directly.",
                "  Missing output entries return null in the printed JSON.",
                "  Input variables with expression return their evaluated name: value items.",
                "  A file spec name is returned only when save: true.",
            ]
        )

    raise ValueError(f"Unknown manual topic: {topic}")


def _render_table_manual(topic: str, *, dim_markers: bool = False) -> str:
    format_name = topic.upper()
    extension = topic
    separator = {
        "csv": "comma-separated",
        "tsv": "tab-separated",
        "dat": "whitespace-separated",
    }[topic]
    header_value = "false" if topic == "dat" else "true"
    input_columns_line = 'columns: [mass, coupling, config]' if topic == "dat" else None
    output_columns_line = 'columns: [chi2, mass, fit_loglike]' if topic == "dat" else None
    comment_line = 'comment: "#"' if topic == "dat" else None

    d1 = _cdots(1, dim=dim_markers)
    d2 = _cdots(2, dim=dim_markers)
    d4 = _cdots(4, dim=dim_markers)
    d6 = _cdots(6, dim=dim_markers)
    d8 = _cdots(8, dim=dim_markers)
    d10 = _cdots(10, dim=dim_markers)
    input_extra = []
    output_extra = []
    if input_columns_line is not None:
        input_extra.append(f"  │ {d4}{input_columns_line}")
    if output_columns_line is not None:
        output_extra.append(f"  │ {d4}{output_columns_line}")
    if comment_line is not None:
        input_extra.append(f"  │ {d4}{comment_line}")
        output_extra.append(f"  │ {d4}{comment_line}")

    return "\n".join(
        [
            f"{format_name} format manual",
            "",
            f"Table type: {separator}",
            "",
            "YAML shape:",
            "  ┌─ YAML ─────────────────────────────",
            "  │ observables:",
            f"  │ {d2}x: 1.0",
            f"  │ {d2}y: 2.0",
            "  │",
            "  │ input:",
            f"  │ {d2}- name: params",
            f"  │ {d4}path: input.{extension}",
            f"  │ {d4}type: {format_name}",
            f"  │ {d4}header: {header_value}",
            *(input_extra if topic == "dat" else []),
            f"  │ {d4}actions:",
            f"  │ {d6}- type: Dump",
            f"  │ {d8}variables:",
            f"  │ {d10}- {{ name: \"var_mass\", expression: \"x * Pi\", column: \"mass\" }}",
            (
                f"  │ {d10}- {{ name: \"var_config\", expression: \"(x + y) * Pi\", "
                'column: "config" }'
            ),
            "  │",
            "  │ output:",
            f"  │ {d2}- name: observables",
            f"  │ {d4}path: output.{extension}",
            f"  │ {d4}type: {format_name}",
            f"  │ {d4}header: {header_value}",
            *(output_extra if topic == "dat" else []),
            f"  │ {d4}variables:",
            f"  │ {d6}- {{ name: \"chi2\", row: 0 }}",
            f"  │ {d6}- {{ name: \"best_mass\", column: \"mass\", row: 0 }}",
            f"  │ {d6}- {{ name: \"loglike\", column: \"fit_loglike\" }}",
            "  └───────────────────────────────────",
            "",
            "Note:",
            f"  {d1} means one indentation space. Replace {d1} with spaces before use.",
            "  Input variables must specify column explicitly; name is only an identifier.",
            "  Output column defaults to name when column is omitted.",
            "  Omitting row reads the whole column; one-cell columns are returned as scalars.",
            "  Missing output columns or rows are omitted from the observable dictionary.",
        ]
    )


def _merge_observables(target: dict[str, Any], source: dict[str, Any]) -> None:
    for name, value in source.items():
        if name in target:
            raise ValueError(f"Duplicate observable name: {name}")
        target[name] = value


async def run_adapter_spec(
    payload: dict[str, Any],
    *,
    project_root: Path,
    runtime_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = create_default_registry()
    values = dict(runtime_values or {})
    context = IOContext(
        project_root=str(project_root.resolve()),
        evaluate_expression=evaluate_runtime_expression,
        runtime_values=values,
    )
    observables: dict[str, Any] = {}
    has_specs = False

    for write_spec in _spec_list(payload, "input"):
        has_specs = True
        adapter = registry.get(write_spec["type"], "input")
        _merge_observables(observables, await adapter.write_input(context, write_spec, values))

    for read_spec in _spec_list(payload, "output"):
        has_specs = True
        adapter = registry.get(read_spec["type"], "output")
        _merge_observables(observables, await adapter.read_output(context, read_spec))

    if not has_specs:
        raise ValueError("YAML must contain input or output.")
    return observables


def run_adapter_spec_sync(
    payload: dict[str, Any],
    *,
    project_root: Path,
    runtime_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    import asyncio

    return asyncio.run(
        run_adapter_spec(payload, project_root=project_root, runtime_values=runtime_values)
    )


def payload_to_observables(payload: dict[str, Any], *, project_root: Path) -> dict[str, Any]:
    if "input" in payload or "output" in payload:
        return run_adapter_spec_sync(
            payload,
            project_root=project_root,
            runtime_values=_runtime_observables(payload),
        )
    jarvis_hep_io = extract_jarvis_hep_io(payload)
    if jarvis_hep_io is not None:
        return run_adapter_spec_sync(
            jarvis_hep_io,
            project_root=project_root,
            runtime_values=_runtime_observables(payload),
        )
    if "observables" in payload:
        observables = payload["observables"]
        if not isinstance(observables, dict):
            raise TypeError("observables must be a mapping.")
        return observables
    raise ValueError("YAML must contain observables, input, or output.")


def _runtime_observables(payload: dict[str, Any]) -> dict[str, Any]:
    observables = payload.get("observables")
    if observables is None:
        return {}
    if not isinstance(observables, dict):
        raise TypeError("observables must be a mapping.")
    return observables


def _spec_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list of Jarvis-HEP file specs.")
    for item in value:
        if not isinstance(item, dict):
            raise TypeError(f"{key} items must be mappings.")
    return value


def extract_jarvis_hep_io(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]] | None:
    calculators = payload.get("Calculators")
    if not isinstance(calculators, dict):
        return None
    modules = calculators.get("Modules")
    if not isinstance(modules, list):
        return None

    collected: dict[str, list[dict[str, Any]]] = {"input": [], "output": []}
    for module in modules:
        if not isinstance(module, dict):
            continue
        execution = module.get("execution")
        if not isinstance(execution, dict):
            continue
        collected["input"].extend(_spec_list(execution, "input"))
        collected["output"].extend(_spec_list(execution, "output"))

    if collected["input"] or collected["output"]:
        return collected
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if args in (["-h"], ["--help"]):
        print(render_help())
        return 0

    if args in (["-v"], ["--version"]):
        print(f"Jarvis-Portal {__version__}")
        return 0

    if not args:
        return _print_usage_error("the following arguments are required: file")

    if args[0].startswith("-"):
        return _print_usage_error(f"unrecognized arguments: {' '.join(args)}")

    try:
        if args[0] == "man":
            if len(args) > 2:
                return _print_usage_error(f"unexpected argument: {' '.join(args[2:])}")
            print(
                render_manual(
                    args[1] if len(args) == 2 else None,
                    dim_markers=sys.stdout.isatty(),
                )
            )
            return 0

        if len(args) > 1:
            return _print_usage_error(f"unexpected argument: {' '.join(args[1:])}")

        target = args[0]
        payload = load_yaml_dict(target)
        observables = payload_to_observables(
            payload,
            project_root=Path(target).expanduser().parent,
        )
        print(render_observables(observables))
    except Exception as exc:
        print(f"[jportal] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
