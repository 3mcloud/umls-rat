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
            ["this is a slice of cheese", "this is some cheese", "this", "cheese"],
        ),
    ),
)
def test_hammingish_order(source: str, targets: List[str]):
    rng = random.Random(234908723)
    # shuffle targets
    shuffled = rng.sample(targets, len(targets))

    # reorder according to hammingish distance from source
    def sort_key(tgt):
        return run_hammingish(source, tgt)

    ordered = sorted(shuffled, key=sort_key)

    assert ordered == targets


@pytest.mark.parametrize(
    ("definition", "expected"),
    (
        ("Aggression towards oneself. [HPO:sdoelken]", "Aggression towards oneself."),
        (
            "Pathologically, this condition may be associated with LEUKOMALACIA, PERIVENTRICULAR. (From Dev Med Child Neurol 1998 Aug;40(8):520-7)",
            "Pathologically, this condition may be associated with LEUKOMALACIA, PERIVENTRICULAR.",
        ),
        (
            "This one is made up (as in not real). But, it must be cited! (Klopfer 2022)",
            "This one is made up (as in not real). But, it must be cited!",
        ),
    ),
)
def test_clean_definition(definition: str, expected: str):
    assert text.clean_definition_text(definition) == expected
