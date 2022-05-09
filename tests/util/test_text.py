import random
from typing import List

import pytest

from umlsrat.util import text


@pytest.mark.parametrize(
    ["text_str", "expected"], [("Faint - appearance", ["faint", "appearance"])]
)
def test_norm_tokenize(text_str, expected):
    assert text.norm_tokenize(text_str) == expected


def run_hammingish(source: str, target: str):
    val = text.hammingish(text.norm_tokenize(source), text.norm_tokenize(target))
    return val


@pytest.mark.parametrize(
    ("source", "targets"),
    (
        (
            "this is a test",
            ["this", "this is a slice of cheese", "this is some cheese", "cheese"],
        ),
    ),
)
def test_hammingish(source: str, targets: List[str]):
    rng = random.Random(234908723)
    # shuffle targets
    shuffled = rng.sample(targets, len(targets))

    # reorder according to hammingish distance from source
    def sort_key(tgt):
        return run_hammingish(source, tgt)

    ordered = sorted(shuffled, key=sort_key)

    assert ordered == targets
