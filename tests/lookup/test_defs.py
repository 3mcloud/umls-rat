import argparse
from typing import List, Optional

import pytest

from umlsrat.lookup import lookup_defs, lookup_umls
from umlsrat.util import iterators


def find_single_mesh_def(api, snomed_code: str) -> Optional[str]:
    cuis = lookup_umls.get_cuis_for(api, "SNOMEDCT_US", snomed_code)
    assert cuis
    for cui in cuis:
        concepts = lookup_defs.definitions_bfs(
            api, cui, stop_on_found=True, target_vocabs=("MSH",)
        )
        results = iterators.extract_definitions(concepts)
        if results:
            return results.pop(0)


@pytest.mark.parametrize(
    ["snomed_code", "expected_def"],
    [
        (
            "450807008",
            "Anatomical areas of the body.",
        ),
        (
            "10937761000119101",
            "Fractures in which the break in bone is not accompanied by an external wound.",
        ),
        (
            "182166001",
            "The gliding joint formed by the outer extremity of the CLAVICLE and the "
            "inner margin of the ACROMION PROCESS of the SCAPULA.",
        ),
    ],
)
def test_single_mesh_def(api, snomed_code, expected_def):
    definition = find_single_mesh_def(api, snomed_code)
    assert definition == expected_def


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "expected_text"),
    (
        (
            dict(
                source_vocab="snomed",
                concept_id="450807008",
                broader=True,
                language="ENG",
            ),
            ["Back structure, including back of neck"],
            "subdivision of body proper, each instance of which has as its direct parts "
            "some back of neck and some back of trunk. Examples: There is only one back "
            "of body proper.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="10937761000119101",
                broader=True,
                language="ENG",
            ),
            ["Closed fracture of carpal bone"],
            "A traumatic break in one or more of the carpal bones that does not involve a "
            "break in the adjacent skin.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="182166001",
                broader=True,
                language="ENG",
            ),
            ["Acromioclavicular joint structure"],
            "The junction of the upper distal end of the scapula to the distal edge of "
            "the collarbone, also known as the acromion and the clavicle.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="282024004",
                broader=True,
                language="ENG",
            ),
            ["Vertebral column"],
            "The spinal or vertebral column.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="48348007",
                broader=True,
                language="ENG",
            ),
            ["Respiratory Sounds"],
            "Noises, normal and abnormal, heard on auscultation over any part of the RESPIRATORY TRACT.",
        ),
        (
            dict(
                source_desc="Cancer",
                broader=True,
            ),
            ["Malignant Neoplasms"],
            "An organ or organ-system abnormality that consists of uncontrolled autonomous cell-proliferation",
        ),
        (
            # Right (qualifier value) (snomed/24028007)
            dict(
                source_vocab="snomed",
                concept_id="24028007",
                source_desc="Right (qualifier value)",
                broader=True,
            ),
            ["Right", "Lateral"],
            "Being or located on or directed toward the side of the body to the east when facing north.",
        ),
        (
            # Protein-calorie malnutrition (disorder) (snomed/3371e7b7-f04a-40aa-83c2-3fb703539922)
            dict(
                source_vocab="snomed",
                concept_id="3371e7b7-f04a-40aa-83c2-3fb703539922",
                source_desc="Protein-calorie malnutrition (disorder)",
                broader=True,
            ),
            ["Protein-Energy Malnutrition"],
            "A nutritional deficit that is caused by inadequate protein or calorie intake.",
        ),
        (
            # Anticoagulant (rxnorm/58798db8-1fb8-4655-9baf-c6d19d9d1ce9)
            dict(
                source_vocab="snomed",
                concept_id="58798db8-1fb8-4655-9baf-c6d19d9d1ce9",
                source_desc="Anticoagulant",
                broader=True,
            ),
            ["Anticoagulants"],
            "Agents that prevent BLOOD CLOTTING.",
        ),
        (
            # Bipolar joint prosthesis (physical object) (snomed/c31fc990-0824-4d8e-962b-86f56b33e580)
            dict(
                source_vocab="snomed",
                concept_id="c31fc990-0824-4d8e-962b-86f56b33e580",
                source_desc="Bipolar joint prosthesis (physical object)",
                broader=True,
            ),
            [],
            None,
        ),
        (
            # cannot find this one
            dict(
                source_vocab="snomed",
                concept_id="a209c041-2376-4482-8044-a724ed9cb8c1",
                source_desc="Faint (qualifier value)",
                broader=True,
                language="ENG",
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
                concept_id="260994008",
                source_desc="Bipolar (qualifier value)",
                broader=True,
            ),
            ["Subject Headings"],
            "Terms or expressions which provide the major means of access by subject to "
            "the bibliographic unit.",
        ),
        (
            # setting max distance, gets rid of the garbage
            # Bipolar (qualifier value) (snomed/260994008)
            dict(
                source_vocab="snomed",
                concept_id="260994008",
                source_desc="Bipolar (qualifier value)",
                broader=True,
                max_distance=2,
            ),
            [],
            None,
        ),
        (
            # Entire costovertebral angle of twelfth rib (body structure) (snomed/312886007)
            dict(
                source_vocab="snomed",
                concept_id="312886007",
                source_desc="Entire costovertebral angle of twelfth rib (body structure)",
                broader=True,
            ),
            ["Back", "Lumbar Region", "Bona fide anatomical line"],
            "The back or upper side of an animal.",
        ),
        (
            # Cancer Society (snomed/9bd4c0aa-d3b0-434e-8a60-de6f9f338b7e)
            dict(
                source_vocab="snomed",
                concept_id="9bd4c0aa-d3b0-434e-8a60-de6f9f338b7e",
                source_desc="Cancer Society",
                broader=True,
            ),
            ["American Cancer Society"],
            "A voluntary organization concerned with the prevention and treatment of cancer through education and research.",
        ),
        (
            # Cancer Society (snomed/138875005)
            dict(
                source_vocab="snomed",
                concept_id="138875005",
                source_desc="Cancer Society",
                broader=True,
            ),
            ["American Cancer Society"],
            "A voluntary organization concerned with the prevention and treatment of cancer through education and research.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
                source_desc="Room air (substance)",
                broader=True,
                stop_on_found=False,
                max_distance=3,
            ),
            [
                "Room Air",
                "Air (substance)",
                "Atmosphere, planetary",
                "Gases",
                "Inorganic Chemicals",
                "Environment",
                "Weather",
                "atmosphere/weather",
                "Meteorological Concepts",
                "Physical State",
                "fluid - substance",
                "Chemicals",
                "Drug or Chemical by Structure",
                "Substance",
            ],
            "The gaseous envelope surrounding a planet or similar body.",
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
                source_desc="Room air (substance)",
                broader=False,
                stop_on_found=False,
                max_distance=10,
            ),
            ["Room Air"],
            "Unmodified air as existing in the immediate surroundings.",
        ),
        (
            dict(
                source_desc="Cancer",
                language="SPA",
                broader=True,
            ),
            ["Neoplasms"],
            "Crecimiento anormal y nuevo de tejido. Las neoplasias malignas muestran un mayor grado de anaplasia y tienen la propiedad de invasión y metástasis, comparados con las neoplasias benignas.",
        ),
    ),
)
def test_find_defined_concepts(
    api, kwargs, expected_names: List[str], expected_text: str
):
    concepts = lookup_defs.find_defined_concepts(api, **kwargs)
    names = iterators.extract_concept_names(concepts)
    assert names == expected_names
    definitions = iterators.extract_definitions(concepts)
    if expected_text:
        assert any(expected_text in definition for definition in definitions)
    else:
        assert not definitions


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "a_definition"),
    (
        (
            # no english definitions for "faint"
            dict(
                start_cui="C4554554",
                broader=True,
                language="ENG",
            ),
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
            dict(start_cui="C5397118", broader=True, language="ENG"),
            ["Therapeutic procedure", "Oxygen Therapy Care"],
            "Administration of oxygen and monitoring of its effectiveness",
        ),
        (
            dict(start_cui="C1270222", broader=False, language="ENG"),
            ["Felis catus"],
            "The domestic cat, Felis catus, of the carnivore family FELIDAE, comprising "
            "over 30 different breeds. The domestic cat is descended primarily from the "
            "wild cat of Africa and extreme southwestern Asia. Though probably present in "
            "towns in Palestine as long ago as 7000 years, actual domestication occurred "
            "in Egypt about 4000 years ago.",
        ),
        (
            dict(
                start_cui="C1270222",
                broader=False,
                stop_on_found=False,
                max_distance=2,
                language="ENG",
            ),
            ["Felis catus"],
            "The domesticated feline mammal, Felis catus, which is kept as a house pet.",
        ),
        (
            dict(start_cui="C1270222", broader=False, language="ENG"),
            ["Felis catus"],
            "The domestic cat, Felis catus, of the carnivore family FELIDAE, comprising "
            "over 30 different breeds. The domestic cat is descended primarily from the "
            "wild cat of Africa and extreme southwestern Asia. Though probably present in "
            "towns in Palestine as long ago as 7000 years, actual domestication occurred "
            "in Egypt about 4000 years ago.",
        ),
        (
            dict(
                start_cui="C1270222",
                broader=True,
                stop_on_found=True,
                max_distance=2,
                language="ENG",
            ),
            ["Family Felidae"],
            "Taxonomic family which includes domestic and wild cats such as lions and tigers.",
        ),
        (
            dict(
                start_cui="C0011119",
                broader=False,
                stop_on_found=False,
                max_distance=2,
                language="ENG",
                preserve_semantic_type=True,
            ),
            [
                "Decompression Sickness",
                "Altitude Sickness",
                "Postpartum Obstetric Air Embolism",
                "Antepartum Obstetric Air Embolism",
            ],
            "Multiple symptoms associated with reduced oxygen at high ALTITUDE.",
        ),
        (
            dict(
                start_cui="C0011119",
                broader=False,
                stop_on_found=False,
                max_distance=2,
                language="ENG",
                preserve_semantic_type=False,
            ),
            [
                "Decompression Sickness",
                "Barotrauma",
                "Air Embolism",
                "Altitude Sickness",
                "Blast Injuries",
                "Postpartum Obstetric Air Embolism",
                "Antepartum Obstetric Air Embolism",
            ],
            "Injuries resulting when a person is struck by particles impelled with "
            "violent force from an explosion. Blast causes pulmonary concussion and "
            "hemorrhage, laceration of other thoracic and abdominal viscera, ruptured ear "
            "drums, and minor effects in the central nervous system.",
        ),
        (
            dict(
                start_cui="C0011119",
                broader=False,
                stop_on_found=True,
                max_distance=None,
                language="ENG",
                preserve_semantic_type=False,
            ),
            ["Decompression Sickness"],
            "A condition occurring as a result of exposure to a rapid fall in ambient "
            "pressure. Gases, nitrogen in particular, come out of solution and form "
            "bubbles in body fluid and blood. These gas bubbles accumulate in joint "
            "spaces and the peripheral circulation impairing tissue oxygenation causing "
            "disorientation, severe pain, and potentially death.",
        ),
        (
            dict(start_cui="C0022646", broader=True),
            ["Kidney"],
            "Of or pertaining to the kidney.",
        ),
        (
            dict(start_cui="C0022646", broader=False),
            ["Kidney"],
            "Of or pertaining to the kidney.",
        ),
    ),
)
def test_definitions_bfs(api, kwargs, expected_names, a_definition):
    concepts = lookup_defs.definitions_bfs(api, **kwargs)
    names = iterators.extract_concept_names(concepts)
    assert names == expected_names
    definitions = iterators.extract_definitions(concepts)
    if a_definition:
        assert a_definition in definitions
    else:
        assert not definitions


def test_preserve_sem_types(api):
    common_kwargs = dict(
        start_cui="C0011119",
        broader=False,
        stop_on_found=False,
        max_distance=2,
        language="ENG",
    )
    no_preserve = lookup_defs.definitions_bfs(
        api, **common_kwargs, preserve_semantic_type=False
    )

    do_preserve = lookup_defs.definitions_bfs(
        api, **common_kwargs, preserve_semantic_type=True
    )
    # preserving semantic types should only reduce the number of results
    assert len(do_preserve) <= len(no_preserve)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            dict(
                source_vocab="snomed",
                concept_id="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
                source_desc="Room air (substance)",
                broader=True,
                stop_on_found=False,
                max_distance=1,
            ),
            [
                "Unmodified air as existing in the immediate surroundings.",
                "A mixture of gases making up the earth's atmosphere, consisting mainly of "
                "nitrogen, oxygen, argon, and carbon dioxide.",
                "The mixture of gases present in the earth's atmosphere consisting of oxygen, "
                "nitrogen, carbon dioxide, and small amounts of other gases.",
            ],
        ),
        (
            dict(
                source_vocab="snomed",
                concept_id="c31fc990-0824-4d8e-962b-86f56b33e580",
                source_desc="Bipolar joint prosthesis (physical object)",
                broader=True,
                stop_on_found=False,
                max_distance=1,
            ),
            [],
        ),
    ),
)
def test_definitions_itr(api, kwargs, expected):
    concepts = lookup_defs.find_defined_concepts(api, **kwargs)
    defs = list(lookup_defs.definitions_itr(concepts))
    assert defs == expected


def test_max_distance(api):
    def do_find(d):
        return lookup_defs.find_defined_concepts(
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
    data = lookup_defs.find_defined_concepts(
        api, source_vocab="snomed", concept_id="448169003"
    )

    pp = iterators.definitions_to_md(data)
    assert (
        pp
        == """Felis catus
===========
1. The domesticated feline mammal, Felis catus, which is kept as a
house pet.
2. The domestic cat, Felis catus, of the carnivore family FELIDAE,
comprising over 30 different breeds. The domestic cat is descended
primarily from the wild cat of Africa and extreme southwestern Asia.
Though probably present in towns in Palestine as long ago as 7000
years, actual domestication occurred in Egypt about 4000 years ago."""
    )


@pytest.fixture()
def arg_parser():
    return lookup_defs.add_args(argparse.ArgumentParser())


@pytest.mark.parametrize(
    ("cli_args", "kwargs", "expected"),
    (
        (
            ["--source-vocab=snomed", "--concept-id=67362008"],
            dict(),
            "An abnormal balloon- or sac-like dilatation in the wall of AORTA.",
        ),
        (
            [],
            dict(source_vocab="snomed", concept_id="67362008"),
            "An abnormal balloon- or sac-like dilatation in the wall of AORTA.",
        ),
        (
            ["--start-cui=C0003486"],
            dict(),
            "An abnormal balloon- or sac-like dilatation in the wall of AORTA.",
        ),
        (
            [],
            dict(
                start_cui="C0003486",
            ),
            "An abnormal balloon- or sac-like dilatation in the wall of AORTA.",
        ),
    ),
)
def test_find_builder(api, arg_parser, cli_args, kwargs, expected):
    args = arg_parser.parse_args(cli_args)
    find_fn = lookup_defs.find_builder(api, args)
    result = find_fn(**kwargs)
    defs = iterators.extract_definitions(result)
    assert expected in defs
