from typing import Dict

import pytest

from umlsrat.lookup import umls
from umlsrat.lookup.umls import term_search


@pytest.mark.parametrize(
    ["code_system", "code", "expected_cui"],
    [
        # Entire back of trunk
        ("SNOMEDCT_US", "450807008", "C3472551"),
        # Entire lumbosacral junction of vertebral column
        ("SNOMEDCT_US", "282024004", "C0559890"),
        # Closed fracture of left wrist
        ("SNOMEDCT_US", "10937761000119101", "C3887398"),
    ],
)
def test_get_cui_for(api, code_system, code, expected_cui):
    cui = umls.get_cui_for(api, code_system, code)
    assert cui == expected_cui


def test_include_flags(api):
    uri = "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    res = list(api.get_results(uri))

    include_uri = "https://uts-ws.nlm.nih.gov/rest/search/2021AB?includeObsolete=True&includeSuppressible=True&string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    include_res = list(api.get_results(include_uri))

    assert len(include_res) >= len(res)


@pytest.mark.parametrize(
    ["source_vocab", "concept_id", "allowable_labels", "expected_len"],
    [("MSH", "D002415", {"RN", "CHD"}, 1)],
)
def test_get_source_relations(
    api, source_vocab, concept_id, allowable_labels, expected_len
):
    relations = list(
        api.get_source_relations(
            source_vocab=source_vocab,
            concept_id=concept_id,
            includeRelationLabels=",".join(allowable_labels),
            language="ENG",
        )
    )
    # all resulting relation labels should appear in the "includeRelationLabels"
    for rel in relations:
        assert rel["relationLabel"] in allowable_labels

    # assert expected length
    assert len(relations) == expected_len


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


def test_search_idempotence(api):
    first = umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    second = umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    assert first == second


def test_pagination(api):
    results = api.search("star trek vs star wars", pageSize=25)
    assert not list(results)
    results = api.search("bone", pageSize=25, max_results=100)
    assert len(list(results)) == 100

    # x = list(umls.get_broader_concepts(api, 'C4517971'))
    # assert x
