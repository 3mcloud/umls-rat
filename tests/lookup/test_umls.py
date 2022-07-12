from typing import Dict

import pytest

import utilities
from umlsrat.lookup import lookup_umls


@pytest.mark.parametrize(
    ["kwargs", "expected_names"],
    [
        # Entire back of trunk
        (dict(source_vocab="SNOMEDCT_US", source_ui="450807008"), ["Entire back"]),
        # Entire lumbosacral junction of vertebral column
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="282024004"),
            ["Lumbosacral region of spine"],
        ),
        # Closed fracture of left wrist
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="10937761000119101"),
            ["Closed fracture of left wrist"],
        ),
        # Coronary arteriosclerosis (disorder)
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="53741008"),
            [
                "Coronary Arteriosclerosis",
                "Coronary Artery Disease",
                "Coronary heart disease",
            ],
        ),
        # Right
        (
            dict(source_vocab="SNOMEDCT_US", source_ui="24028007"),
            ["Lateral to the right", "Right"],
        ),
    ],
)
def test_get_cuis_for(api, kwargs, expected_names):
    cui_list = lookup_umls.get_cuis_for(api, **kwargs)

    source = api.get_source_concept(
        source_vocab=kwargs["source_vocab"], concept_id=kwargs["source_ui"]
    )
    source_name = source.get("name")
    actual_names = utilities.map_cuis_to_names(api, cui_list)
    assert actual_names == expected_names, f"Got wrong concepts for '{source_name}'"


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(cui="C0559890"),
            [
                "Lumbosacral region of spine structure",
                "Structure of inter-regional junction of vertebral column",
            ],
        ),
        (dict(cui="C3472551"), ["Back structure, including back of neck"]),
        (
            dict(cui="C3887398"),
            [
                "closed fracture of wrist",
                "Closed fracture of left upper limb",
                "Closed fracture of carpal bone",
                "Injury of left wrist",
            ],
        ),
        (
            dict(cui="C0009044"),
            [
                "Fracture of carpal bone",
                "Closed fracture of upper limb",
                "closed fracture of wrist",
                "Fracture of upper limb",
                "Fractures, Closed",
                "Unspecified site injury",
            ],
        ),
        (
            dict(cui="C0450415"),
            ["Lateral", "Binary anatomical coordinate"],
        ),
    ),
)
def test_get_broader_concepts(api, kwargs, expected_names):
    assert "cui" in kwargs
    cui_list = list(lookup_umls.get_broader_cuis(api, **kwargs))

    assert cui_list
    cui_set = set(cui_list)
    assert len(cui_set) == len(cui_list), "Result should not return duplicates"
    assert kwargs["cui"] not in cui_set

    # map to names
    source_name = lookup_umls.get_concept_name(api, kwargs["cui"])
    actual_names = utilities.map_cuis_to_names(api, cui_list)
    assert actual_names == expected_names, f"Got wrong concepts for '{source_name}'"


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(
                cui="C0003611",
                allowed_relations=("SY",),
                language="ENG",
            ),
            [],
        ),
        (
            dict(
                cui="C0003611",
                allowed_relations=("SY",),
                include_source_relations=True,
                language="ENG",
            ),
            ["Multiple Sclerosis", "Other gastrointestinal disorders"],
        ),
    ),
)
def test_get_related_cuis(api, kwargs, expected_names):
    cui_list = lookup_umls.get_related_cuis(api, **kwargs)

    cui_set = set(cui_list)
    assert len(cui_set) == len(cui_list), "Result should not return duplicates"
    assert kwargs["cui"] not in cui_set

    # map to names
    source_name = lookup_umls.get_concept_name(api, kwargs["cui"])
    actual_names = utilities.map_cuis_to_names(api, cui_list)
    assert actual_names == expected_names, f"Got wrong concepts for '{source_name}'"


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
        (
            dict(
                term="Protein-calorie malnutrition", max_results=1, strict_match=False
            ),
            ["Protein-Energy Malnutrition"],
        ),
        (
            dict(term="Furrycrackers", max_results=1, strict_match=False),
            [],
        ),
    ),
)
def test_term_search(api, kwargs, expected_names):
    result = lookup_umls.term_search(api, **kwargs)
    assert result
    concepts = result.pop("concepts")
    names = [_["name"] for _ in concepts]
    assert names == expected_names


def simple_search(api, term: str) -> Dict:
    search_result = lookup_umls.term_search(api, term)
    if search_result:
        return search_result["concepts"].pop(0)


def test_search_idempotence(api):
    first = lookup_umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    second = lookup_umls.term_search(
        api, term="Faint (qualifier value)", max_results=5, strict_match=True
    )
    assert first == second

    c1 = simple_search(api, "Room air")
    c2 = simple_search(api, "Room Air")
    c3 = simple_search(api, "Room air (substance)")
    assert c1 == c2 == c3
