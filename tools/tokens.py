#!/usr/bin/env python3
"""Read css/tokens.css and write tokens.json.

tokens.css is the source. This produces the machine-readable copy for
anything that cannot parse CSS — a Tailwind theme, an Authentik
blueprint, a Homepage configmap, a design tool.

    python3 tools/tokens.py            # write tokens.json
    python3 tools/tokens.py --check    # fail if tokens.json is stale

The --check form is what CI runs, so the two cannot drift.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS = ROOT / "css" / "tokens.css"
JSON = ROOT / "tokens.json"

# --hc-name: value;  — the value may run over several lines, which
# --hc-ground-image does, so it is read up to the next semicolon rather
# than to the end of the line.
#
# Read quote- and paren-aware, and that is not pedantry. The previous
# form was `(.+?);` — non-greedy to the first semicolon, blind to
# quotes. --hc-cubes-mask carried a data URI whose "image/svg+xml;utf8,"
# holds a semicolon, so this tool cut the value there and wrote
# `url("data:image/svg+xml` into tokens.json. Everything generated from
# that copy inherited the truncation, and an unclosed quote in CSS makes
# the parser swallow the rest of the stylesheet. The token no longer
# contains a semicolon, but a generator that cannot read one is a trap
# waiting for the next value.
NAME = re.compile(r"(--hc-[a-z0-9-]+)\s*:\s*")


def declarations(text):
    """Every --hc- declaration, respecting quotes and parentheses."""
    for m in NAME.finditer(text):
        i, depth, quote = m.end(), 0, None
        while i < len(text):
            c = text[i]
            if quote:
                if c == quote:
                    quote = None
            elif c in "\"'":
                quote = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == ";" and depth == 0:
                break
            elif c == "}" and depth == 0:
                break
            i += 1
        yield m.group(1), text[m.end():i]

GROUPS = [
    ("ground",   ("ground", "wash")),
    ("brand",    ("brass", "on-brass")),
    ("ink",      ("ink",)),
    ("surface",  ("pane", "hairline", "blur")),
    ("status",   ("ok", "warn", "danger", "info")),
    ("radius",   ("r-", "r:")),
    ("space",    ("space",)),
    ("type",     ("font", "text", "display", "weight", "track", "leading")),
    ("elevation",("shadow",)),
    ("motion",   ("dur", "ease")),
    ("layout",   ("wide", "measure", "gutter")),
    ("motif",    ("cubes", "iso", "flow", "rail")),
    ("focus",    ("focus",)),
]


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def group_for(name: str) -> str:
    tail = name[len("--hc-"):]
    for group, prefixes in GROUPS:
        for p in prefixes:
            if tail == p.rstrip(":-") or tail.startswith(p.rstrip(":")):
                return group
    return "other"


def collect() -> dict:
    text = strip_comments(CSS.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    seen: list[str] = []
    for name, value in declarations(text):
        if name in seen:
            print(f"ERROR: {name} is declared twice in css/tokens.css", file=sys.stderr)
            raise SystemExit(1)
        seen.append(name)
        out.setdefault(group_for(name), {})[name] = " ".join(value.split())
    return {g: out[g] for g in [g for g, _ in GROUPS] + ["other"] if g in out}


def main() -> int:
    data = collect()
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not JSON.exists():
            print("ERROR: tokens.json is missing — run tools/tokens.py", file=sys.stderr)
            return 1
        if JSON.read_text(encoding="utf-8") != rendered:
            print("ERROR: tokens.json does not match css/tokens.css."
                  " Run `python3 tools/tokens.py` and commit the result.", file=sys.stderr)
            return 1
        total = sum(len(v) for v in data.values())
        print(f"tokens.json matches css/tokens.css ({total} tokens)")
        return 0
    JSON.write_text(rendered, encoding="utf-8")
    total = sum(len(v) for v in data.values())
    print(f"wrote tokens.json ({total} tokens in {len(data)} groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
