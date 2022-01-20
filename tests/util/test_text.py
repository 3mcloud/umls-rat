import pytest

from umlsrat.util import text


@pytest.mark.parametrize(
    ["text_str", "expected"], [("Faint - appearance", ["faint", "appearance"])]
)
def test_norm_tokenize(text_str, expected):
    assert text.norm_tokenize(text_str) == expected
