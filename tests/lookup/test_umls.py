from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = MetaThesaurus(rklopfer_api_key)


def test_find_umls_old_back():
    cui = find_umls(api, 'SNOMEDCT_US', '450807008')
    print(cui)
    assert cui == 'C4517971'
    # assert cui == 'C3472551'


def test_find_umls_funky():
    concept = find_umls(api, 'SNOMEDCT_US', '282024004')
    assert concept
