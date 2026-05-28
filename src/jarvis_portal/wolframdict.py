from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, TextIO

_NUMBER_RE = re.compile(
    r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:\*\^[+-]?\d+|[eE][+-]?\d+)?"
)
_IDENT_RE = re.compile(r"[A-Za-z$][A-Za-z0-9$]*")


@dataclass(frozen=True)
class _Token:
    type: str
    value: str
    position: int


def load(fp: TextIO) -> dict[str, Any]:
    return loads(fp.read())


def loads(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    parser = _Parser(_tokenize(text))
    value = parser.parse()
    if not isinstance(value, dict):
        raise TypeError("Wolfram document must be an Association.")
    return value


def dump(obj: Any, fp: TextIO, indent: int = 2) -> None:
    fp.write(dumps(obj, indent=indent))


def dumps(obj: Any, indent: int = 2) -> str:
    return _format_value(obj, indent=indent, level=0)


def _tokenize(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    position = 0
    length = len(text)
    while position < length:
        char = text[position]
        if char.isspace():
            position += 1
            continue
        if text.startswith("(*", position):
            position = _skip_comment(text, position)
            continue
        if text.startswith("<|", position):
            tokens.append(_Token("ASSOC_OPEN", "<|", position))
            position += 2
            continue
        if text.startswith("|>", position):
            tokens.append(_Token("ASSOC_CLOSE", "|>", position))
            position += 2
            continue
        if text.startswith("->", position):
            tokens.append(_Token("ARROW", "->", position))
            position += 2
            continue
        if char == "{":
            tokens.append(_Token("LIST_OPEN", char, position))
            position += 1
            continue
        if char == "}":
            tokens.append(_Token("LIST_CLOSE", char, position))
            position += 1
            continue
        if char == ",":
            tokens.append(_Token("COMMA", char, position))
            position += 1
            continue
        if char == '"':
            token, position = _read_string(text, position)
            tokens.append(token)
            continue

        number = _NUMBER_RE.match(text, position)
        if number is not None:
            value = number.group(0)
            tokens.append(_Token("NUMBER", value, position))
            position = number.end()
            continue

        ident = _IDENT_RE.match(text, position)
        if ident is not None:
            value = ident.group(0)
            tokens.append(_Token("IDENT", value, position))
            position = ident.end()
            continue

        raise ValueError(f"Unexpected character at position {position}: {char!r}")
    tokens.append(_Token("EOF", "", position))
    return tokens


def _skip_comment(text: str, start: int) -> int:
    depth = 1
    position = start + 2
    while position < len(text):
        if text.startswith("(*", position):
            depth += 1
            position += 2
            continue
        if text.startswith("*)", position):
            depth -= 1
            position += 2
            if depth == 0:
                return position
            continue
        position += 1
    raise ValueError(f"Unterminated comment at position {start}")


def _read_string(text: str, start: int) -> tuple[_Token, int]:
    chars: list[str] = []
    position = start + 1
    while position < len(text):
        char = text[position]
        if char == '"':
            return _Token("STRING", "".join(chars), start), position + 1
        if char == "\\":
            position += 1
            if position >= len(text):
                raise ValueError(f"Unterminated escape sequence at position {start}")
            escaped = text[position]
            chars.append(
                {
                    '"': '"',
                    "\\": "\\",
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "b": "\b",
                    "f": "\f",
                }.get(escaped, escaped)
            )
        else:
            chars.append(char)
        position += 1
    raise ValueError(f"Unterminated string at position {start}")


class _Parser:
    def __init__(self, tokens: list[_Token]) -> None:
        self._tokens = tokens
        self._index = 0

    def parse(self) -> Any:
        value = self._parse_value()
        self._expect("EOF")
        return value

    def _parse_value(self) -> Any:
        token = self._current()
        if token.type == "ASSOC_OPEN":
            return self._parse_association()
        if token.type == "LIST_OPEN":
            return self._parse_list()
        if token.type == "STRING":
            self._advance()
            return token.value
        if token.type == "NUMBER":
            self._advance()
            return _parse_number(token.value)
        if token.type == "IDENT":
            self._advance()
            return _parse_ident(token.value)
        raise ValueError(f"Expected Wolfram value at position {token.position}.")

    def _parse_association(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        self._expect("ASSOC_OPEN")
        if self._accept("ASSOC_CLOSE"):
            return payload
        while True:
            key = self._expect("STRING").value
            self._expect("ARROW")
            payload[key] = self._parse_value()
            if self._accept("COMMA"):
                if self._current().type == "ASSOC_CLOSE":
                    break
                continue
            break
        self._expect("ASSOC_CLOSE")
        return payload

    def _parse_list(self) -> list[Any]:
        payload: list[Any] = []
        self._expect("LIST_OPEN")
        if self._accept("LIST_CLOSE"):
            return payload
        while True:
            payload.append(self._parse_value())
            if self._accept("COMMA"):
                if self._current().type == "LIST_CLOSE":
                    break
                continue
            break
        self._expect("LIST_CLOSE")
        return payload

    def _accept(self, token_type: str) -> bool:
        if self._current().type == token_type:
            self._advance()
            return True
        return False

    def _expect(self, token_type: str) -> _Token:
        token = self._current()
        if token.type != token_type:
            raise ValueError(
                f"Expected {token_type} at position {token.position}, got {token.type}."
            )
        self._advance()
        return token

    def _current(self) -> _Token:
        return self._tokens[self._index]

    def _advance(self) -> None:
        self._index += 1


def _parse_number(value: str) -> int | float:
    normalized = value.replace("*^", "e")
    if any(marker in normalized for marker in (".", "e", "E")):
        return float(normalized)
    return int(normalized)


def _parse_ident(value: str) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    if value == "Null":
        return None
    return value


def _format_value(value: Any, *, indent: int, level: int) -> str:
    if isinstance(value, dict):
        return _format_dict(value, indent=indent, level=level)
    if isinstance(value, (list, tuple)):
        return _format_list(value, indent=indent, level=level)
    if isinstance(value, str):
        return _format_string(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "Null"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _format_float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not Wolfram serializable.")


def _format_dict(value: dict[Any, Any], *, indent: int, level: int) -> str:
    if not value:
        return "<||>"
    current_indent = " " * (indent * level)
    child_indent = " " * (indent * (level + 1))
    lines = ["<|"]
    items = list(value.items())
    for index, (key, item) in enumerate(items):
        suffix = "," if index < len(items) - 1 else ""
        rendered = _format_value(item, indent=indent, level=level + 1)
        lines.append(f"{child_indent}{_format_string(str(key))} -> {rendered}{suffix}")
    lines.append(f"{current_indent}|>")
    return "\n".join(lines)


def _format_list(value: list[Any] | tuple[Any, ...], *, indent: int, level: int) -> str:
    if not value:
        return "{}"
    if _is_scalar_sequence(value):
        rendered = [_format_value(item, indent=indent, level=level) for item in value]
        return "{ " + ", ".join(rendered) + " }"
    current_indent = " " * (indent * level)
    child_indent = " " * (indent * (level + 1))
    lines = ["{"]
    items = list(value)
    for index, item in enumerate(items):
        suffix = "," if index < len(items) - 1 else ""
        rendered = _format_value(item, indent=indent, level=level + 1)
        lines.append(f"{child_indent}{rendered}{suffix}")
    lines.append(f"{current_indent}}}")
    return "\n".join(lines)


def _is_scalar_sequence(value: list[Any] | tuple[Any, ...]) -> bool:
    return all(not isinstance(item, (dict, list, tuple)) for item in value)


def _format_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\f", "\\f")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("Non-finite floats are not Wolfram serializable.")
    if value == 0:
        return "0.0"
    magnitude = abs(value)
    text = format(value, ".17g")
    if magnitude < 0.001 or magnitude > 1_000_000:
        return _format_scientific_number(value)
    if "." not in text:
        return f"{text}.0"
    return text


def _format_scientific_number(value: float) -> str:
    mantissa, exponent = format(value, ".17e").split("e", maxsplit=1)
    mantissa = mantissa.rstrip("0").rstrip(".")
    return f"{mantissa}*^{int(exponent)}"
