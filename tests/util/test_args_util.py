import argparse

import pytest

from umlsrat.util import args_util


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", type=args_util.str2bool)
    return parser


def test_parser(parser):
    args = parser.parse_args(["--flag", "True"])
    assert args.flag
    args = parser.parse_args(["--flag", "no"])
    assert not args.flag

    with pytest.raises(SystemExit):
        parser.parse_args(["--flag", "waffles"])
