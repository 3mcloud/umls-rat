from typing import Dict, List, Optional

import pytest

import umlsrat.lookup.umls
from umlsrat.lookup import definitions


def extract_concept_names(concepts: List[Dict]) -> List[str]:
    return [_["name"] for _ in concepts]


def extract_definitions(concepts: List[Dict]) -> List[str]:
    defs = []
    for concept in concepts:
        for d in concept["definitions"]:
            defs.append(d)
    return [d["value"] for d in defs]


def find_single_mesh_def(api, snomed_code: str) -> Optional[str]:
    cuis = umlsrat.lookup.umls.get_cuis_for(api, "SNOMEDCT_US", snomed_code)
    assert cuis
    for cui in cuis:
        concepts = definitions.broader_definitions_bfs(
            api, cui, min_concepts=1, target_vocabs=("MSH",)
        )
        results = extract_definitions(concepts)
        if results:
            return results.pop(0)


@pytest.mark.parametrize(
    ["snomed_code", "expected_def"],
    [
        (
            "450807008",
            "The central part of the body to which the neck and limbs are attached.",
        ),
        ("10937761000119101", "Injuries to the wrist or the wrist joint."),
    ],
)
def test_single_mesh_def(api, snomed_code, expected_def):
    definition = find_single_mesh_def(api, snomed_code)
    assert definition == expected_def


"""
{source_vocab = "snomed",
        source_code: str = None,
        source_desc: str = None,
        min_concepts: int = 1,
        max_distance: int = 0,
        target_lang: str = "ENG",}
        """


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "a_definition"),
    (
        (
            dict(source_vocab="snomed", source_ui="282024004", target_lang="ENG"),
            ["Vertebral column"],
            "The spinal or vertebral column.",
        ),
        (
            dict(source_vocab="snomed", source_ui="48348007", target_lang="ENG"),
            ["Respiratory Sounds"],
            "Noises, normal and abnormal, heard on auscultation over any part of the RESPIRATORY TRACT.",
        ),
        (
            dict(
                source_vocab="snomed",
                source_ui="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
                source_desc="Room air (substance)",
                min_concepts=2,
            ),
            ["Room Air", "Air (substance)"],
            "Unmodified air as existing in the immediate surroundings.",
        ),
        (
            dict(source_desc="Cancer", target_lang="SPA"),
            ["Neoplasms"],
            "Crecimiento anormal y nuevo de tejido. Las neoplasias malignas muestran un mayor grado de anaplasia y tienen la propiedad de invasión y metástasis, comparados con las neoplasias benignas.",
        ),
        (
            dict(source_desc="Cancer"),
            ["Malignant Neoplasms"],
            "Uncontrolled growth of abnormal cells with potential for metastatic spread.",
        ),
        (
            # Right (qualifier value) (snomed/24028007)
            dict(
                source_vocab="snomed",
                source_ui="24028007",
                source_desc="Right (qualifier value)",
            ),
            ["Right", "Lateral", "Side"],
            "Being or located on or directed toward the side of the body to the east when facing north.",
        ),
        (
            # Protein-calorie malnutrition (disorder) (snomed/3371e7b7-f04a-40aa-83c2-3fb703539922)
            dict(
                source_vocab="snomed",
                source_ui="3371e7b7-f04a-40aa-83c2-3fb703539922",
                source_desc="Protein-calorie malnutrition (disorder)",
            ),
            ["Protein-Energy Malnutrition"],
            "A nutritional deficit that is caused by inadequate protein or calorie intake.",
        ),
        (
            # Anticoagulant (rxnorm/58798db8-1fb8-4655-9baf-c6d19d9d1ce9)
            dict(
                source_vocab="snomed",
                source_ui="58798db8-1fb8-4655-9baf-c6d19d9d1ce9",
                source_desc="Anticoagulant",
            ),
            ["Anticoagulants"],
            "Agents that prevent BLOOD CLOTTING.",
        ),
        (
            # Bipolar joint prosthesis (physical object) (snomed/c31fc990-0824-4d8e-962b-86f56b33e580)
            dict(
                source_vocab="snomed",
                source_ui="c31fc990-0824-4d8e-962b-86f56b33e580",
                source_desc="Bipolar joint prosthesis (physical object)",
            ),
            ["Joint Prosthesis (device)"],
            "Prostheses used to partially or totally replace a human or animal joint.",
        ),
        (
            # cannot find this one
            dict(
                source_vocab="snomed",
                source_ui="a209c041-2376-4482-8044-a724ed9cb8c1",
                source_desc="Faint (qualifier value)",
                target_lang="ENG",
                max_distance=1,
            ),
            [],
            None,
        ),
        (
            # This is clearly garbage...
            # Bipolar (qualifier value) (snomed/260994008)
            dict(
                source_vocab="snomed",
                source_ui="260994008",
                source_desc="Bipolar (qualifier value)",
            ),
            ["Vocabulary, Controlled", "Thesaurus", "Subject Headings"],
            "A finite set of values that represent the only allowed values for a data item. These values may be codes, text, or numeric. See also codelist.",
        ),
        (
            # Entire costovertebral angle of twelfth rib (body structure) (snomed/312886007)
            dict(
                source_vocab="snomed",
                source_ui="312886007",
                source_desc="Entire costovertebral angle of twelfth rib (body structure)",
            ),
            ["Back", "Bona fide anatomical line"],
            "The back or upper side of an animal.",
        ),
    ),
)
def test_find_defined_concepts(
    api, kwargs, expected_names: List[str], a_definition: str
):
    data = definitions.find_defined_concepts(api, **kwargs)
    names = extract_concept_names(data)
    assert names == expected_names
    if a_definition:
        assert a_definition in extract_definitions(data)
    else:
        assert not extract_definitions(data)


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "a_definition"),
    (
        (
            # no english definitions for "faint"
            dict(start_cui="C4554554", target_lang="ENG"),
            [],
            None,
        ),
        (
            # no definitions for "faint" in any language
            dict(start_cui="C4554554"),
            [],
            None,
        ),
        (
            dict(start_cui="C5397118", target_lang="ENG"),
            ["Oxygen Therapy Care", "Therapeutic procedure"],
            "Administration of oxygen and monitoring of its effectiveness",
        ),
    ),
)
def test_broader_definitions_bfs(api, kwargs, expected_names, a_definition):
    data = definitions.broader_definitions_bfs(api, **kwargs)
    names = extract_concept_names(data)
    assert names == expected_names
    if a_definition:
        assert a_definition in extract_definitions(data)
    else:
        assert not extract_definitions(data)


def test_max_distance(api):
    def do_find(d):
        return definitions.find_defined_concepts(
            api,
            "snomed",
            "182166001",
            "Entire acromioclavicular joint (body structure)",
            max_distance=d,
        )

    no_d = do_find(0)
    d_10 = do_find(10)

    assert no_d == d_10


def test_pretty_print(api):
    data = definitions.find_defined_concepts(
        api, source_vocab="snomed", source_ui="448169003"
    )

    pp = definitions.pretty_print_defs(data)
    assert (
        pp
        == """Felis catus
===========
1. The domestic cat, Felis catus.
2. The domesticated feline mammal, Felis catus, which is kept as a
house pet.
3. The domestic cat, Felis catus, of the carnivore family FELIDAE,
comprising over 30 different breeds. The domestic cat is descended
primarily from the wild cat of Africa and extreme southwestern Asia.
Though probably present in towns in Palestine as long ago as 7000
years, actual domestication occurred in Egypt about 4000 years ago."""
    )
