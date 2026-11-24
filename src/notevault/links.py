"""[[Wiki links]] between notes, and the backlink index built from them."""

from __future__ import annotations

import re

# [[Target]] or [[Target|shown text]] or [[Target#Heading]]; not inside `code spans`.
LINK_RE = re.compile(r"\[\[([^\[\]|#\n]+)(?:#[^\[\]|\n]*)?(?:\|[^\[\]\n]*)?\]\]")
CODE_SPAN_RE = re.compile(r"(`+)(?:.|\n)*?\1")
FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)


def note_key(title: str) -> str:
    return " ".join(title.split()).casefold()


def outgoing_links(markdown: str) -> list[str]:
    text = FENCE_RE.sub("", markdown)
    text = CODE_SPAN_RE.sub("", text)
    seen, out = set(), []
    for m in LINK_RE.finditer(text):
        key = note_key(m.group(1))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


class LinkIndex:
    def __init__(self):
        self.outgoing: dict[str, list[str]] = {}

    def update(self, title: str, markdown: str) -> None:
        self.outgoing[note_key(title)] = outgoing_links(markdown)

    def remove(self, title: str) -> None:
        self.outgoing.pop(note_key(title), None)

    def backlinks(self, title: str) -> list[str]:
        key = note_key(title)
        return sorted(src for src, targets in self.outgoing.items() if key in targets and src != key)

    def broken(self) -> dict[str, list[str]]:
        return {src: [t for t in ts if t not in self.outgoing]
                for src, ts in self.outgoing.items() if any(t not in self.outgoing for t in ts)}
