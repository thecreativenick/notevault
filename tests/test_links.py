from notevault import LinkIndex, outgoing_links


def test_link_syntax():
    md = """See [[Project Ideas]] and [[project  ideas|again]] and [[Reading List#2026]].
Inline `[[not a link]]` is ignored.

```
[[also ignored]]
```
"""
    assert outgoing_links(md) == ["project ideas", "reading list"]


def test_backlinks_and_broken_links():
    idx = LinkIndex()
    idx.update("Home", "Start at [[Inbox]] or [[Archive]].")
    idx.update("Inbox", "Back to [[home]].")
    idx.update("Weekly", "Review [[Inbox]], link to self [[Weekly]].")
    assert idx.backlinks("inbox") == ["home", "weekly"]
    assert idx.backlinks("Weekly") == []
    assert idx.broken() == {"home": ["archive"]}
    idx.remove("Weekly")
    assert idx.backlinks("Inbox") == ["home"]
