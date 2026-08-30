#!/usr/bin/env python3
"""Checks that hold this repository together.

1. Every var(--hc-…) used anywhere resolves to a token defined in
   css/tokens.css. A typo in a variable name is silent in CSS — the
   property is simply dropped — so nothing else would ever report it.
2. Braces balance in every stylesheet.
3. No raw colour outside css/tokens.css. A hex or rgb() literal in a
   component is how a design system stops being one.
4. Every stylesheet the specimen page links actually exists.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "css" / "tokens.css"

USE = re.compile(r"var\(\s*(--hc-[a-z0-9-]+)")
DEF = re.compile(r"^\s*(--hc-[a-z0-9-]+)\s*:", re.MULTILINE)
LINK = re.compile(r'<link[^>]+href="([^"]+\.css)"')
# Literal colours: hex, rgb(), rgba(), hsl(), oklch(). Named colours are
# not matched — `transparent`, `inherit` and `currentColor` are fine.
COLOUR = re.compile(r"(#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab)\s*\()")


def blank_comments(text: str) -> str:
    """Replace comments with spaces, keeping every newline.

    Deleting them instead would shift every offset after the first
    comment, and the line numbers this script reports would point at
    the wrong line — worse than not reporting one at all.
    """
    def blank(m: re.Match) -> str:
        return "".join("\n" if c == "\n" else " " for c in m.group(0))
    return re.sub(r"/\*.*?\*/", blank, text, flags=re.S)


def main() -> int:
    bad = 0
    if not TOKENS.exists():
        print("ERROR: css/tokens.css is missing")
        return 1

    defined = set(DEF.findall(blank_comments(TOKENS.read_text(encoding="utf-8"))))
    print(f"css/tokens.css defines {len(defined)} tokens")

    sheets = sorted(ROOT.glob("css/*.css")) + sorted(ROOT.glob("docs/*.css"))
    for sheet in sheets:
        rel = sheet.relative_to(ROOT)
        raw = sheet.read_text(encoding="utf-8")
        text = blank_comments(raw)

        for name in sorted(set(USE.findall(text))):
            if name not in defined:
                print(f"ERROR: {rel}: var({name}) is not defined in css/tokens.css")
                bad += 1

        if text.count("{") != text.count("}"):
            print(f"ERROR: {rel}: braces do not balance "
                  f"({text.count('{')} open, {text.count('}')} close)")
            bad += 1

        # Rule 3 applies to the files that build the interface, not to
        # the tokens that define the palette, not to the bridge (it hands
        # shadcn a few alpha values that exist nowhere else), and not to
        # the specimen page's own layout, which is not part of the system.
        if rel.as_posix() in {"css/components.css", "css/motif.css"}:
            for m in COLOUR.finditer(text):
                line = text[: m.start()].count("\n") + 1
                print(f"ERROR: {rel}:{line}: literal colour {m.group(1)!r} — "
                      f"add it to css/tokens.css and reference it with var()")
                bad += 1

    page = ROOT / "docs" / "index.html"
    if page.exists():
        for href in LINK.findall(page.read_text(encoding="utf-8")):
            if href.startswith("http"):
                continue
            target = (page.parent / href).resolve()
            if not target.exists():
                print(f"ERROR: docs/index.html links {href}, which does not exist")
                bad += 1
    else:
        print("ERROR: docs/index.html is missing")
        bad += 1

    if bad:
        print(f"\n{bad} problem(s)")
        return 1
    print(f"checked {len(sheets)} stylesheets — all clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
