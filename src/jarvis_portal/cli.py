from __future__ import annotations

import argparse
import json
import pprint
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml

from jarvis_portal import __version__, create_default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jportal",
        description="Jarvis-Portal YAML inspection and IO adapter utility.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="path to a YAML input file",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="print Jarvis-Portal version and exit",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write the parsed dictionary to a file instead of stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of Python dictionary syntax",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit compact JSON; only valid with --json",
    )
    parser.add_argument(
        "--formats",
        action="store_true",
        help="list registered built-in adapter formats and exit",
    )
    return parser


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


def render_mapping(payload: dict[str, Any], *, as_json: bool = False, compact: bool = False) -> str:
    if as_json:
        if compact:
            return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return pprint.pformat(payload, sort_dicts=False)


def render_formats() -> str:
    registry = create_default_registry()
    lines = ["Jarvis-Portal adapter formats:"]
    lines.append(f"  input: {', '.join(registry.available_formats('input'))}")
    lines.append(f"  output: {', '.join(registry.available_formats('output'))}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"Jarvis-Portal {__version__}")
        return 0

    if args.formats:
        print(render_formats())
        return 0

    if not args.file:
        parser.error("the following arguments are required: file")

    if args.compact and not args.json:
        parser.error("--compact is only valid with --json")

    try:
        payload = load_yaml_dict(args.file)
        rendered = render_mapping(payload, as_json=args.json, compact=args.compact)
        if args.output:
            output_path = Path(args.output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except Exception as exc:
        print(f"[jportal] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
