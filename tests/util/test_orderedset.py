import pytest

from umlsrat.util.orderedset import UniqueFIFO, FIFO


def basic_tests(q):
    q.push_all(range(3))
    q.push(3)

    assert 0 in q
    assert -1 not in q

    previous = 99
    while q:
        peeked = q.peek()
        popped = q.pop()
        assert peeked == popped
        assert popped < previous


def test_unique_fifo():
    q = UniqueFIFO(range(3))
    q.push_all(range(3))
    q.remove(0)
    assert 0 not in q
    with pytest.raises(KeyError):
        q.remove(-1)
    assert repr(q) == str(q) == "[1, 2]"
    basic_tests(UniqueFIFO())


def test_fifo():
    q = FIFO(range(3))
    q.push_all(range(3))
    assert repr(q) == str(q) == "[0, 1, 2, 0, 1, 2]"
    basic_tests(FIFO())
