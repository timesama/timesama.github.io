# make_refs.py\\

from pathlib import Path
import re

BIBFILE = Path("assets/Euromar2026/Euromar2026.bib")
OUTFILE = Path("_posts/2026-06-26-references-euromar-2026.md")

text = BIBFILE.read_text(encoding="utf-8")

entries = re.findall(r'@article\{.*?\n\}', text, re.DOTALL)

def field(name, entry):
    m = re.search(rf'{name}\s*=\s*\{{(.*?)\}}', entry, re.DOTALL)
    if m:
        return m.group(1).replace("\n", " ").strip()
    return ""

with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("""---
layout: post
title: "References Euromar 2026"
date: 2026-06-26
---

# References

""")

    for i, e in enumerate(entries, 1):
        authors = field("author", e)
        title = field("title", e)
        journal = field("journal", e)
        volume = field("volume", e)
        year = field("year", e)
        pages = field("pages", e)

        authors = authors.replace(" and ", "; ")

        f.write(
            f"{i}. **{authors}**\n"
            f"   *{title}*\n"
            f"   {journal} **{volume}** ({year}), {pages}.\n\n"
        )

print("Bibliography generated.")