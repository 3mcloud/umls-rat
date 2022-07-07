import pytest

from umlsrat.lookup.lookup_syns import find_synonyms


@pytest.mark.parametrize(
    ("kwargs", "expected_syns"),
    (
        (
            dict(source_vocab="CPT", source_ui="44950"),
            [
                "Appendectomy",
                "Appendectomies",
                "Appendicectomy",
                "appendectomy (treatment)",
                "removal of appendix",
                "Excision of appendix",
                "Excision of appendix (procedure)",
            ],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="SPA"),
            ["Apendicectomía", "Apendectomía"],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="FRE"),
            ["Appendicectomie"],
        ),
        (
            dict(source_vocab="CPT", source_ui="44950", language="GER"),
            ["Appendektomie"],
        ),
        (
            dict(source_vocab="ICD10CM", source_ui="T87.44"),
            [
                "Infection of amputation stump, left lower extremity",
                "infection of amputation stump of left lower extremity",
                "infection of amputation stump of left lower extremity (diagnosis)",
                "Infection of amputation stump of left lower limb",
                "Infection of amputation stump of left leg",
                "Infection of amputation stump of left lower limb (disorder)",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", source_ui="T87.44", language="SPA"),
            [],
        ),
    ),
)
def test_find_synonyms(api, kwargs, expected_syns):
    syns = find_synonyms(api, **kwargs)
    assert syns == expected_syns
