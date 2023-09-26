import pytest

from umlsrat.lookup.lookup_desc import find_synonyms, get_synonyms


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(cui="C0011119", normalize=True),
            {
                "decompression sickness",
                "sickness decompression",
                "bends",
                "the bends",
                "bending",
                "bend",
                "caisson disease",
                "caisson diseases",
                "diseases caisson",
                "disease caisson",
                "caissons disease",
                "chokes",
                "choke",
                "choking",
                "aerobullosis",
                "disease divers",
                "diver disease",
                "compressed air disease",
                "rapture of the deep syndrome",
                "effects of caisson disease",
                "diver's palsy or paralysis",
                "divers' palsy or paralysis",
                "disease or disorder compressed air",
                "disease or disorder caisson",
                "diver's squeeze compression",
                "compression diver's squeeze",
                "decompression disease",
                "disease or disorder decompression",
                "diver's palsy paralysis or squeeze",
                "diver's paralysis",
            },
        ),
        (dict(cui="C4554554"), {"Faint - appearance", "Faint"}),
        (
            dict(cui="C0034500"),
            {
                "Genus Procyon",
                "Genus Procyon (organism)",
                "Procyon",
                "Procyon, NOS",
                "Procyons",
                "Raccoon",
            },
        ),
        (
            dict(cui="C0034500", normalize=True),
            {"raccoons", "raccoon", "procyon", "procyons", "genus procyon"},
        ),
    ),
)
def test_get_synonyms(api, kwargs, expected_names):
    names = set(get_synonyms(api, **kwargs))
    assert names & expected_names == expected_names


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            dict(source_vocab="CPT", concept_id="44950", normalize=True),
            {
                "appendectomy",
                "appendectomies",
                "excision of appendix",
                "appendix excision",
                "primary appendectomy",
                "appendicectomy",
                "appendicectomies",
                "excision procedures on the appendix",
                "appendectomy procedures",
                "appendectomy procedure",
                "removal of appendix",
            },
        ),
        (
            dict(
                source_vocab="CPT", concept_id="44950", language="SPA", normalize=True
            ),
            {
                "apendectomía",
                "apendicectomía",
                "resección del apéndice",
                "resección del apéndice íleocecal",
            },
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", language="FRE"),
            {"Appendicectomie"},
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", language="GER"),
            {"Appendektomie"},
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", normalize=True),
            {
                "infection of amputation stump left lower extremity",
                "infection of amputation stump of left lower limb",
                "infection of amputation stump of left lower extremity",
                "infection of amputation stump of left leg",
            },
        ),
        (
            dict(
                source_vocab="ICD10CM",
                concept_id="T87.44",
                language="SPA",
                normalize=True,
            ),
            {
                "infección de muñón de amputación de extremidad inferior izquierda",
                "infección de muñón de amputación de miembro inferior izquierdo",
            },
        ),
        (
            dict(source_vocab="ICD9CM", concept_id="433.91", language="ENG"),
            {
                "Occlusion and stenosis of unspecified precerebral artery with cerebral "
                "infarction",
                "Unspecified precerebral artery, with cerebral infarction",
            },
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="R06", language="ENG"),
            "Abnormal respiratory system physiology",
        ),
    ),
)
def test_find_synonyms(api, kwargs, expected):
    syns = set(find_synonyms(api, **kwargs))
    if isinstance(expected, str):
        assert expected in syns
    else:
        assert syns == expected
