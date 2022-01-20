from umlsrat.vocabularies.vocab_tools import get_vocab_info, validate_vocab_abbrev


def test_get_info():
    info = get_vocab_info("snomed")
    assert info
    assert info == ("SNOMED CT, US Edition", "SNOMEDCT_US", "2021AB", "ENG", "9")


def test_validate_valid():
    assert validate_vocab_abbrev("snomed") == "SNOMEDCT_US"
    assert validate_vocab_abbrev("msh") == "MSH"
