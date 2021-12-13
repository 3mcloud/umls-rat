from typing import Dict

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls, term_search

rklopfer_api_key = "cf4e9f8f-a40c-4225-94e9-24ca9282b887"
api = MetaThesaurus(rklopfer_api_key)


def test_find_umls_old_back(api):
    cui = find_umls(api, "SNOMEDCT_US", "450807008")
    assert cui == "C4517971"


def test_find_umls_funky(api):
    concept = find_umls(api, "SNOMEDCT_US", "282024004")
    assert concept == "C5546171"


def do_search(api, term: str) -> Dict:
    search_result = term_search(api, term)
    if search_result:
        return search_result["concepts"].pop(0)


def test_search(api):
    c1 = do_search(api, "Room air")
    assert c1
    c2 = do_search(api, "Room Air")
    assert c2
    c3 = do_search(api, "Room air (substance)")
    assert c3
    c4 = do_search(api, "Anticoagulant")
    assert c4

    assert c1 == c2
    assert c1 == c3
    assert c4
