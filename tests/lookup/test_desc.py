import pytest

from umlsrat.lookup.lookup_desc import find_synonyms, get_synonyms


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(cui="C0011119"),
            [
                "Caisson Diseases",
                "Decompression Sickness",
                "Diseases, Caisson",
                "Disease, Caisson",
                "Sickness, Decompression",
                "CAISSON DIS",
                "decompression sickness (diagnosis)",
                "Caisson disease",
                "Caisson disease [decompression sickness]",
                "Bends",
                "The bends",
                "Divers' palsy",
                "Compressed-air disease",
                "Divers' paralysis",
                "Bends (disorder)",
                "caisson; disease",
                "compression; diver's squeeze",
                "decompression; disease",
                "disease (or disorder); caisson",
                "disease (or disorder); compressed air",
                "disease (or disorder); decompression",
                "diver's squeeze; compression",
                "diver's; paralysis",
            ],
        ),
        (
            dict(cui="C0011119", normalize=True),
            [
                "caisson diseases",
                "decompression sickness",
                "diseases caisson",
                "disease caisson",
                "sickness decompression",
                "caisson dis",
                "caisson disease",
                "bends",
                "the bends",
                "divers' palsy",
                "compressed air disease",
                "divers' paralysis",
                "compression diver's squeeze",
                "decompression disease",
                "disease or disorder caisson",
                "disease or disorder compressed air",
                "disease or disorder decompression",
                "diver's squeeze compression",
                "diver's paralysis",
            ],
        ),
        (dict(cui="C4554554"), []),
        (
            dict(cui="C0034500"),
            [
                "Raccoon",
                "Raccoons",
                "Procyons",
                "Procyon",
                "Genus Procyon",
                "Genus Procyon (organism)",
            ],
        ),
    ),
)
def test_get_synonyms(api, kwargs, expected_names):
    names = get_synonyms(api, **kwargs)
    assert names == expected_names


@pytest.mark.parametrize(
    ("kwargs", "expected_syns"),
    (
        (
            dict(source_vocab="CPT", concept_id="44950"),
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
            dict(source_vocab="CPT", concept_id="44950", language="SPA"),
            ["Apendicectomía", "Apendectomía"],
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
                "infection of amputation stump of left lower extremity",
                "infection of amputation stump of left lower extremity (diagnosis)",
                "Infection of amputation stump of left lower limb",
                "Infection of amputation stump of left leg",
                "Infection of amputation stump of left lower limb (disorder)",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", normalize=True),
            [
                "infection of amputation stump left lower extremity",
                "infection of amputation stump of left lower extremity",
                "infection of amputation stump of left lower limb",
                "infection of amputation stump of left leg",
            ],
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", language="SPA"),
            [],
        ),
    ),
)
def test_find_synonyms(api, kwargs, expected_syns):
    syns = find_synonyms(api, **kwargs)
    # assert len(syns) == len(expected_syns)
    assert syns == expected_syns
