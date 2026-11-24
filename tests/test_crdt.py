import random

import pytest

from notevault import TextDoc


def sync(*docs, ops, rng=None):
    for d in docs:
        batch = list(ops)
        if rng:
            rng.shuffle(batch)  # arbitrary delivery order; the doc buffers until causal deps arrive
        for op in batch:
            d.apply(op)


def test_local_editing():
    d = TextDoc("a")
    d.insert(0, "hello world")
    d.delete(5, 6)
    d.insert(5, ", there")
    assert d.text == "hello, there"


def test_concurrent_inserts_same_spot_converge():
    a, b = TextDoc("a"), TextDoc("b")
    base = a.insert(0, "ac")
    sync(b, ops=base)
    ops_a = a.insert(1, "XX")
    ops_b = b.insert(1, "yy")
    sync(a, b, ops=ops_a + ops_b)
    assert a.text == b.text
    assert sorted(a.text) == sorted("acXXyy")
    # each side's run stays contiguous: no interleaving like "aXyXyc"
    assert a.text in ("aXXyyc", "ayyXXc")


def test_concurrent_delete_and_insert():
    a, b = TextDoc("a"), TextDoc("b")
    sync(b, ops=a.insert(0, "abcdef"))
    ops_a = a.delete(1, 4)        # removes "bcde"
    ops_b = b.insert(3, "123")    # inserts inside the deleted run
    sync(a, b, ops=ops_a + ops_b)
    assert a.text == b.text == "a123f"  # the concurrent insert survives


def test_duplicate_and_out_of_order_delivery():
    a, b = TextDoc("a"), TextDoc("b")
    ops = a.insert(0, "out of order")
    ops += a.delete(0, 4)
    for op in reversed(ops + ops):
        b.apply(op)
    assert b.text == a.text == "of order"
    assert b.pending == []


def test_rejects_bad_positions():
    d = TextDoc("a")
    with pytest.raises(IndexError):
        d.insert(1, "x")
    with pytest.raises(IndexError):
        d.delete(0)


@pytest.mark.parametrize("seed", range(30))
def test_fuzz_three_replicas_converge(seed):
    rng = random.Random(seed)
    docs = [TextDoc(s) for s in "xyz"]
    log = []
    for _round in range(8):
        new = []
        for d in docs:  # each replica edits offline
            for _ in range(rng.randint(0, 6)):
                n = len(d.text)
                if n and rng.random() < 0.35:
                    pos = rng.randrange(n)
                    new += d.delete(pos, rng.randint(1, min(3, n - pos)))
                else:
                    new += d.insert(rng.randint(0, n), rng.choice(["a", "bc", "def", "\n"]))
        log += new
        sync(*docs, ops=log, rng=rng)  # everyone exchanges everything, shuffled
        assert docs[0].text == docs[1].text == docs[2].text
