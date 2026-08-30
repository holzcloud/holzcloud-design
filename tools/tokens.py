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
# --hc-ground-image does, so it is matched up to the next semicolon
# rather than to the end of the line.
DECL = re.compile(r"(--hc-[a-z0-9-]+)\s*:\s*(.+?);", re.S)

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
    for name, value in DECL.findall(text):
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
