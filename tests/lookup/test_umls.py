from typing import Dict

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls, term_search

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = MetaThesaurus(rklopfer_api_key)


def test_find_umls_old_back():
    cui = find_umls(api, 'SNOMEDCT_US', '450807008')
    assert cui == 'C4517971'


def test_find_umls_funky():
    concept = find_umls(api, 'SNOMEDCT_US', '282024004')
    assert concept == 'C5546171'


def do_search(term: str) -> Dict:
    search_result = term_search(api, term)
    if search_result:
        return search_result['concepts'].pop(0)


def test_search():
    c1 = do_search("Room air")
    assert c1
    c2 = do_search("Room Air")
    assert c2
    c3 = do_search("Room air (substance)")
    assert c3
    c4 = do_search("Anticoagulant")
    assert c4

    assert c1 == c2
    assert c1 == c3
    assert c4
