from typing import Dict

from umlsrat.lookup import umls
from umlsrat.lookup.umls import term_search
import pytest


@pytest.mark.parametrize(
    ["code_system", "code", "expected_cui"],
    [
        # # Entire back of trunk
        # ("SNOMEDCT_US", "450807008", "C4517971"),
        # # Entire lumbosacral junction of vertebral column
        # ("SNOMEDCT_US", "282024004", "C5546171"),
        # Closed fracture of left wrist
        ("SNOMEDCT_US", "10937761000119101", "C3887398"),
    ],
)
def test_get_cui_for(api, code_system, code, expected_cui):
    cui = umls.get_cui_for(api, code_system, code)
    assert cui == expected_cui


def do_search(api, term: str) -> Dict:
    search_result = term_search(api, term)
    if search_result:
        return search_result["concepts"].pop(0)


def test_term_search(api):
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


def test_pagination(api):
    results = api.search("star trek vs star wars", pageSize=25)
    assert not list(results)
    results = api.search("bone", pageSize=25, max_results=100)
    assert len(list(results)) == 100

    # x = list(umls.get_broader_concepts(api, 'C4517971'))
    # assert x


def test_new_lookup(api):
    ui = "450807008"

    old = umls.find_umls(api, source_vocab="snomed", concept_id=ui)
    new = umls.get_cui_for(api, source_vocab="snomed", concept_id=ui)
    assert old == new

    ui = "282024004"

    old = umls.find_umls(api, source_vocab="snomed", concept_id=ui)
    new = umls.get_cui_for(api, source_vocab="snomed", concept_id=ui)
    assert old == new


# def test_get_broader(api):
#     cui = "C1995000"
#     actual = list(umls.get_broader_concepts(api, cui=cui))
#     # ac = [api.get_concept(_) for _ in actual]
#     # updated = sorted(ac, key=lambda _:_["atomCount"])
#     # updated = [_["ui"] for _ in updated]
#     expected = ["C1720697", "C0581757", "C1280632", "C0817743", "C0460009", "C0004600"]
#     assert len(actual) == len(expected)
#     assert set(actual) == set(expected)
#     assert actual == expected
#
#
# def test_get_broader2(api):
#     cui = "C0460009"
#     actual = list(umls.get_broader_concepts(api, cui=cui))
#     expected = ["C0460005", "C2322636", "C0229960", "C0005898", "C0738568", "C1995000"]
#     assert len(actual) == len(expected)
#     assert set(actual) == set(expected)
#     assert actual == expected
