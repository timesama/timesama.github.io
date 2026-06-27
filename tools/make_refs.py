from pathlib import Path
import re
from pylatexenc.latex2text import LatexNodes2Text

BIBFILE = Path("assets/Euromar2026/Euromar2026.bib")
OUTFILE = Path("_posts/2026-06-26-references-euromar-2026.md")

latex2text = LatexNodes2Text().latex_to_text

text = BIBFILE.read_text(encoding="utf-8")

entries = re.findall(r'@article\{.*?\n\}', text, re.DOTALL)

def field(name, entry):
    pattern = rf'{name}\s*=\s*\{{'
    start = re.search(pattern, entry)
    if not start:
        return ""

    i = start.end()
    brace_level = 1
    value = []

    while i < len(entry) and brace_level > 0:
        c = entry[i]

        if c == "{":
            brace_level += 1
        elif c == "}":
            brace_level -= 1

        if brace_level > 0:
            value.append(c)

        i += 1

    return "".join(value).strip()

def clean(s):
    return latex2text(s)

with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("""---
layout: post
title: "References Euromar 2026"
date: 2026-06-26
---

# References

""")

    for i, e in enumerate(entries, 1):

        authors = clean(field("author", e))
        title = clean(field("title", e))
        journal = clean(field("journal", e))
        volume = field("volume", e)
        year = field("year", e)
        pages = field("pages", e)

        authors = authors.replace(" and ", "; ")

        f.write(
            f"{i}. **{authors}**\n"
            f"   *{title}*\n"
            f"   {journal} **{volume}** ({year}), {pages}.\n\n"
        )

print("Bibliography generated with proper Unicode.")