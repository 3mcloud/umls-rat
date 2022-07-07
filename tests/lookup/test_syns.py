import pytest

from umlsrat.lookup.lookup_syns import find_synonyms


@pytest.mark.parametrize(
    ("kwargs", "expected_syns"),
    (
        (
            dict(source_vocab="CPT", source_ui="44950"),
            ["Appendectomy", "Appendectomies", "Appendicectomy"],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="SPA"),
            ["Appendectomy", "Appendicectomy", "Apendicectomía", "Apendectomía"],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="FRE"),
            ["Appendectomy", "Appendicectomy", "Appendicectomie"],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="GER"),
            ["Appendectomy", "Appendicectomy", "Appendektomie"],
        ),
        (
            dict(source_vocab="ICD10CM", source_ui="T87.44"),
            [
                "Infection of amputation stump, left lower extremity",
                "infection of amputation stump of left lower extremity",
                "Infection of amputation stump of left lower limb",
            ],
        ),
    ),
)
def test_find_synonyms(api, kwargs, expected_syns):
    syns = find_synonyms(api, **kwargs)
    assert syns == expected_syns
