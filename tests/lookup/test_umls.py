from typing import Dict

import pytest

from umlsrat.lookup import umls


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


@pytest.mark.parametrize(
    ("kwargs", "expected_name"),
    (
        (dict(term="Room air", max_results=1, strict_match=False), "Room Air"),
        (
            dict(term="Anticoagulant", max_results=1, strict_match=False),
            "Anticoagulants",
        ),
        # This would solve our back problem, but alas it does not work...
        # (dict(term="Entire back", max_results=1, strict_match=False), 'Back'),
        (
            dict(
                term="Protein-calorie malnutrition", max_results=1, strict_match=False
            ),
            "Protein-Energy Malnutrition",
        ),
    ),
)
def test_term_search(api, kwargs, expected_name):
    result = umls.term_search(api, **kwargs)
    assert result
    concepts = result.pop("concepts")
    names = [_["name"] for _ in concepts]
    assert expected_name in names


def simple_search(api, term: str) -> Dict:
    search_result = umls.term_search(api, term)
    if search_result:
        return search_result["concepts"].pop(0)


def test_search_idempotence(api):
    first = umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    second = umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    assert first == second

    c1 = simple_search(api, "Room air")
    c2 = simple_search(api, "Room Air")
    c3 = simple_search(api, "Room air (substance)")
    assert c1 == c2 == c3


@pytest.mark.parametrize(
    ("kwargs", "expected_cuis"),
    (
        # (dict(cui="C0559890"), {'C0559887', 'C0574025'}),
        # (dict(cui="C3472551"), {'C0460009'}),
        # (dict(cui="C3887398"), {'C3886880', 'C4281104', 'C0009044'}),
        (dict(cui="C0009044"), {}),
    ),
)
def test_get_broader_concepts(api, kwargs, expected_cuis):
    assert "cui" in kwargs
    result = list(umls.get_broader_concepts(api, **kwargs))
    assert result
    cuis = set(result)
    assert len(cuis) == len(result), "Result should not return duplicates"
    assert kwargs["cui"] not in cuis
    assert cuis == expected_cuis
