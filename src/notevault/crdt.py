"""RGA (Replicated Growable Array) text CRDT.

Every character gets a unique id (lamport counter, site). An insert names
the id of the character it goes after; concurrent inserts after the same
character are ordered by id, larger first. Deletes leave tombstones. Any
two replicas that have applied the same set of operations, in any causal
order, hold the same text.

Ops that arrive before their dependency are buffered until it shows up, so
the network layer doesn't need to deliver in order.
"""

from __future__ import annotations

from dataclasses import dataclass

Id = tuple[int, str]  # (counter, site); compared lexicographically
ROOT: Id = (0, "")


@dataclass(frozen=True)
class Insert:
    id: Id
    after: Id
    char: str


@dataclass(frozen=True)
class Delete:
    target: Id


Op = Insert | Delete


@dataclass
class _Elem:
    id: Id
    char: str
    deleted: bool = False


class TextDoc:
    def __init__(self, site: str):
        if not site:
            raise ValueError("site id must be non-empty")
        self.site = site
        self.clock = 0
        self.elems: list[_Elem] = []
        self.index: dict[Id, int] = {}   # id -> position in elems (rebuilt on insert)
        self.applied: set[Op] = set()
        self.pending: list[Op] = []

    # -------------------------------------------------------------- reading
    @property
    def text(self) -> str:
        return "".join(e.char for e in self.elems if not e.deleted)

    def _visible_ids(self) -> list[Id]:
        return [e.id for e in self.elems if not e.deleted]

    # -------------------------------------------------------- local editing
    def insert(self, pos: int, text: str) -> list[Op]:
        visible = self._visible_ids()
        if not 0 <= pos <= len(visible):
            raise IndexError(pos)
        after = visible[pos - 1] if pos else ROOT
        ops = []
        for ch in text:
            self.clock += 1
            op = Insert((self.clock, self.site), after, ch)
            self.apply(op)
            ops.append(op)
            after = op.id
        return ops

    def delete(self, pos: int, length: int = 1) -> list[Op]:
        visible = self._visible_ids()
        if pos < 0 or pos + length > len(visible):
            raise IndexError(pos)
        ops = [Delete(i) for i in visible[pos : pos + length]]
        for op in ops:
            self.apply(op)
        return ops

    # ------------------------------------------------------- remote merging
    def apply(self, op: Op) -> None:
        """Apply a local or remote op. Idempotent; out-of-order ops wait in a buffer."""
        if op in self.applied:
            return
        if not self._ready(op):
            if op not in self.pending:
                self.pending.append(op)
            return
        self._integrate(op)
        self.applied.add(op)
        # Applying one op can unblock others.
        progress = True
        while progress:
            progress = False
            for p in list(self.pending):
                if self._ready(p):
                    self.pending.remove(p)
                    if p not in self.applied:
                        self._integrate(p)
                        self.applied.add(p)
                    progress = True

    def _ready(self, op: Op) -> bool:
        if isinstance(op, Insert):
            return op.after == ROOT or op.after in self.index
        return op.target in self.index

    def _integrate(self, op: Op) -> None:
        if isinstance(op, Delete):
            self.elems[self.index[op.target]].deleted = True
            return
        self.clock = max(self.clock, op.id[0])
        pos = 0 if op.after == ROOT else self.index[op.after] + 1
        # Skip over concurrent inserts at the same spot that have larger ids
        # (and, implicitly, everything inserted after them, whose ids are larger still).
        while pos < len(self.elems) and self.elems[pos].id > op.id:
            pos += 1
        self.elems.insert(pos, _Elem(op.id, op.char))
        for i in range(pos, len(self.elems)):
            self.index[self.elems[i].id] = i
