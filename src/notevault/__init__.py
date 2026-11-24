"""notevault: local-first Markdown notes that sync without losing a word."""

from .crdt import Delete, Insert, TextDoc
from .links import LinkIndex, outgoing_links

__all__ = ["TextDoc", "Insert", "Delete", "LinkIndex", "outgoing_links"]
