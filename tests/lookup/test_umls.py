from typing import Dict

import pytest

import utilities
from umlsrat.lookup import umls


@pytest.mark.parametrize(
    ["kwargs", "expected_cuis"],
    [
        # Entire back of trunk
        (dict(source_vocab="SNOMEDCT_US", source_ui="450807008"), ["C3472551"]),
        # Entire lumbosacral junction of vertebral column
        (dict(source_vocab="SNOMEDCT_US", source_ui="282024004"), ["C0559890"]),
        # Closed fracture of left wrist
        (dict(source_vocab="SNOMEDCT_US", source_ui="10937761000119101"), ["C3887398"]),
        # Coronary arteriosclerosis (disorder)
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="53741008"),
            ["C0010054", "C1956346", "C0010068"],
        ),
        # Right
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="24028007"),
            ["C0450415", "C0205090"],
        ),
    ],
)
def test_get_cuis_for(api, kwargs, expected_cuis):
    cui = umls.get_cuis_for(api, **kwargs)
    assert cui == expected_cuis


@pytest.mark.parametrize(
    ("kwargs", "expected_cuis"),
    (
        (dict(cui="C0559890"), ["C0574025", "C0559887"]),
        (dict(cui="C3472551"), ["C0460009"]),
        (dict(cui="C3887398"), ["C3886880", "C4281104", "C0009044"]),
        # (dict(cui="C1956346"), []),
        (
            dict(cui="C0009044"),
            ["C0016644", "C0272588", "C0178316", "C0016659", "C0029509"],
        ),
        (
            dict(cui="C0450415"),
            ["C0205093", "C0332191", "C0205089", "C1180190", "C0441987"],
        ),
        # (
        # Descriptors
        #     dict(cui='C0282354'),
        #     []
        # )
    ),
)
def test_get_broader_concepts(api, kwargs, expected_cuis):
    assert "cui" in kwargs
    cui_list = list(umls.get_broader_cuis(api, **kwargs))

    assert cui_list
    cui_set = set(cui_list)
    assert len(cui_set) == len(cui_list), "Result should not return duplicates"
    assert kwargs["cui"] not in cui_set

    assert cui_list == expected_cuis

    # DEBUG map to names
    source = umls.get_concept_name(api, kwargs["cui"])
    actual = utilities.map_cuis_to_names(api, cui_list)
    expected = utilities.map_cuis_to_names(api, expected_cuis)
    assert actual == expected, f"Got wrong concepts for '{source}'"


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (dict(term="Room air", max_results=1, strict_match=False), ["Room Air"]),
        (
            dict(term="Anticoagulant", max_results=1, strict_match=False),
            ["Anticoagulants"],
        ),
        (
            dict(term="Anticoagulant", max_results=1, strict_match=True),
            ["Anticoagulants"],
        ),
        # This would solve our back problem, but alas it does not work...
        # (dict(term="Entire back", max_results=1, strict_match=False), 'Back'),
        (
            dict(
                term="Protein-calorie malnutrition", max_results=1, strict_match=False
            ),
            ["Protein-Energy Malnutrition"],
        ),
    ),
)
def test_term_search(api, kwargs, expected_names):
    result = umls.term_search(api, **kwargs)
    assert result
    concepts = result.pop("concepts")
    names = [_["name"] for _ in concepts]
    assert names == expected_names


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
