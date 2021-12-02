from umlsrat.vocab_info import get_vocab_info, validate_abbrev


def test_get_info():
    info = get_vocab_info('SNOMEDCT_US')
    assert info

def test_validate_valid():
    validate_abbrev('msh')