import pytest

from umlsrat.lookup.lookup_desc import find_synonyms, get_synonyms


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(cui="C0011119"),
            [
                "Decompression Sickness",
                "Sickness, Decompression",
                "Bends",
                "The bends",
                "bending",
                "bend",
                "Caisson Disease",
                "Caisson Diseases",
                "Diseases, Caisson",
                "Disease, Caisson",
                "caissons disease",
                "caisson; disease",
                "chokes",
                "choke",
                "choking",
                "aerobullosis",
                "disease divers",
                "DIVER DISEASE",
                "Compressed-air disease",
                "Compressed air disease",
                "Rapture of the deep syndrome",
                "Effects of caisson disease [decompression sickness]",
                "Caisson disease [decompression sickness]",
                "Diver's palsy or paralysis",
                "Divers' palsy or paralysis",
                "Bends (disorder)",
                "disease (or disorder); compressed air",
                "disease (or disorder); caisson",
                "diver's squeeze; compression",
                "compression; diver's squeeze",
                "decompression; disease",
                "disease (or disorder); decompression",
                "diver's palsy, paralysis or squeeze",
                "diver's; paralysis",
                "decompression sickness (diagnosis)",
            ],
        ),
        (
            dict(cui="C0011119", normalize=True),
            [
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
            ],
        ),
        (dict(cui="C4554554"), ["Faint - appearance", "Faint"]),
        (
            dict(cui="C0034500"),
            [
                "Raccoons",
                "Raccoon",
                "Procyon",
                "Procyon, NOS",
                "Procyons",
                "Genus Procyon (organism)",
                "Genus Procyon",
            ],
        ),
        (
            dict(cui="C0034500", normalize=True),
            ["raccoons", "raccoon", "procyon", "procyons", "genus procyon"],
        ),
    ),
)
def test_get_synonyms(api, kwargs, expected_names):
    names = get_synonyms(api, **kwargs)
    assert names == expected_names


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            dict(source_vocab="CPT", concept_id="44950"),
            [
                "Appendectomy",
                "Appendectomies",
                "Appendectomy, NOS",
                "Excision of appendix",
                "Excision of appendix, NOS",
                "appendix excision",
                "Appendix: Excision",
                "Primary appendectomy",
                "Appendicectomy",
                "Appendicectomy, NOS",
                "appendicectomies",
                "Excision of appendix (procedure)",
                "Excision Procedures on the Appendix",
                "appendectomy procedures",
                "appendectomy procedure",
                "appendectomy (treatment)",
                "Removal of appendix",
            ],
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", normalize=True),
            [
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
            ],
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", language="SPA"),
            [
                "apendicectomía",
                "Apendectomía",
                "resección del apéndice",
                "resección del apéndice (procedimiento)",
                "resección del apéndice íleocecal",
            ],
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", language="FRE"),
            ["Appendicectomie"],
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", language="GER"),
            ["Appendektomie"],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44"),
            [
                "Infection of amputation stump, left lower extremity",
                "Infection of amputation stump of left lower limb",
                "infection of amputation stump of left lower extremity (diagnosis)",
                "Infection of amputation stump of left leg",
                "Infection of amputation stump of left lower limb (disorder)",
                "Infection of amputation stump of left lower extremity",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", normalize=True),
            [
                "infection of amputation stump left lower extremity",
                "infection of amputation stump of left lower limb",
                "infection of amputation stump of left lower extremity",
                "infection of amputation stump of left leg",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", language="SPA"),
            [
                "infección de muñón de amputación de extremidad inferior izquierda",
                "infección de muñón de amputación de extremidad inferior izquierda "
                "(trastorno)",
                "infección de muñón de amputación de miembro inferior izquierdo",
            ],
        ),
        (
            dict(
                source_vocab="ICD10CM",
                concept_id="T87.44",
                language="SPA",
                normalize=True,
            ),
            [
                "infección de muñón de amputación de extremidad inferior izquierda",
                "infección de muñón de amputación de miembro inferior izquierdo",
            ],
        ),
        (
            dict(source_vocab="ICD9CM", concept_id="433.91", language="ENG"),
            [
                "Occlusion and stenosis of unspecified precerebral artery with cerebral "
                "infarction",
                "Unspecified precerebral artery, with cerebral infarction",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="R06", language="ENG"),
            "Abnormal respiratory system physiology",
        ),
    ),
)
def test_find_synonyms(api, kwargs, expected):
    syns = find_synonyms(api, **kwargs)
    if isinstance(expected, str):
        assert expected in syns
    else:
        assert syns == expected
