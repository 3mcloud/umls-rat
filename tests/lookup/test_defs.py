import argparse
from typing import List, Optional

import pytest

from umlsrat.lookup import lookup_defs, lookup_umls
from umlsrat.util.iterators import definitions_to_md
from utilities import extract_definitions, extract_concept_names


def find_single_mesh_def(api, snomed_code: str) -> Optional[str]:
    cuis = lookup_umls.get_cuis_for(api, "SNOMEDCT_US", snomed_code)
    assert cuis
    for cui in cuis:
        concepts = lookup_defs.definitions_bfs(
            api, cui, stop_on_found=True, target_vocabs=("MSH",)
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
        (
            "10937761000119101",
            "Fractures in which the break in bone is not accompanied by an external wound.",
        ),
    ],
)
def test_single_mesh_def(api, snomed_code, expected_def):
    definition = find_single_mesh_def(api, snomed_code)
    assert definition == expected_def


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "a_definition"),
    (
        (
            dict(
                source_vocab="snomed",
                source_ui="282024004",
                broader=True,
                language="ENG",
            ),
            ["Vertebral column"],
            "The spinal or vertebral column.",
        ),
        (
            dict(
                source_vocab="snomed",
                source_ui="48348007",
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
            "Uncontrolled growth of abnormal cells with potential for metastatic spread.",
        ),
        (
            # Right (qualifier value) (snomed/24028007)
            dict(
                source_vocab="snomed",
                source_ui="24028007",
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
                source_ui="3371e7b7-f04a-40aa-83c2-3fb703539922",
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
                source_ui="58798db8-1fb8-4655-9baf-c6d19d9d1ce9",
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
                source_ui="c31fc990-0824-4d8e-962b-86f56b33e580",
                source_desc="Bipolar joint prosthesis (physical object)",
                broader=True,
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
                source_ui="260994008",
                source_desc="Bipolar (qualifier value)",
                broader=True,
            ),
            ["Subject Headings"],
            "Terms or expressions which provide the major means of access by subject to "
            "the bibliographic unit.",
        ),
        (
            # Entire costovertebral angle of twelfth rib (body structure) (snomed/312886007)
            dict(
                source_vocab="snomed",
                source_ui="312886007",
                source_desc="Entire costovertebral angle of twelfth rib (body structure)",
                broader=True,
            ),
            ["Back", "Bona fide anatomical line"],
            "The back or upper side of an animal.",
        ),
        (
            # Cancer Society (snomed/9bd4c0aa-d3b0-434e-8a60-de6f9f338b7e)
            dict(
                source_vocab="snomed",
                source_ui="9bd4c0aa-d3b0-434e-8a60-de6f9f338b7e",
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
                source_ui="138875005",
                source_desc="Cancer Society",
                broader=True,
            ),
            ["American Cancer Society"],
            "A voluntary organization concerned with the prevention and treatment of cancer through education and research.",
        ),
        (
            dict(
                source_vocab="snomed",
                source_ui="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
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
                "atmosphere/weather",
                "Environment",
                "Meteorological Concepts",
                "Weather",
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
                source_ui="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
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
    api, kwargs, expected_names: List[str], a_definition: str
):
    concepts = lookup_defs.find_defined_concepts(api, **kwargs)
    names = extract_concept_names(concepts)
    assert names == expected_names
    if a_definition:
        assert a_definition in extract_definitions(concepts)
    else:
        assert not extract_definitions(concepts)


@pytest.mark.parametrize(
    ("kwargs", "expected_names", "a_definition"),
    (
        # (
        #         # no english definitions for "faint"
        #         dict(
        #             start_cui="C4554554",
        #             broader=True,
        #             language="ENG",
        #         ),
        #         [],
        #         None,
        # ),
        # (
        #         # no definitions for "faint" in any language
        #         dict(start_cui="C4554554"),
        #         [],
        #         None,
        # ),
        # (
        #         dict(start_cui="C5397118", broader=True, language="ENG"),
        #         ["Oxygen Therapy Care", "Therapeutic procedure"],
        #         "Administration of oxygen and monitoring of its effectiveness",
        # ),
        # (
        #         dict(start_cui="C1270222", broader=False, language="ENG"),
        #         ["Felis catus"],
        #         "The domestic cat, Felis catus, of the carnivore family FELIDAE, comprising "
        #         "over 30 different breeds. The domestic cat is descended primarily from the "
        #         "wild cat of Africa and extreme southwestern Asia. Though probably present in "
        #         "towns in Palestine as long ago as 7000 years, actual domestication occurred "
        #         "in Egypt about 4000 years ago.",
        # ),
        # (
        #         dict(
        #             start_cui="C1270222",
        #             broader=False,
        #             stop_on_found=False,
        #             max_distance=2,
        #             language="ENG",
        #         ),
        #         ["Felis catus"],
        #         "The domestic cat, Felis catus.",
        # ),
        (
            dict(
                start_cui="C0011119",
                broader=False,
                stop_on_found=False,
                max_distance=2,
                language="ENG",
                preserve_semantic_type=True,
            ),
            ["Decompression Sickness"],
            "A condition occurring as a result of exposure to a rapid fall in ambient "
            "pressure. Gases, nitrogen in particular, come out of solution and form "
            "bubbles in body fluid and blood. These gas bubbles accumulate in joint "
            "spaces and the peripheral circulation impairing tissue oxygenation causing "
            "disorientation, severe pain, and potentially death.",
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
            ["Felis catus"],
            "The domestic cat, Felis catus.",
        ),
    ),
)
def test_definitions_bfs(api, kwargs, expected_names, a_definition):
    concepts = lookup_defs.definitions_bfs(api, **kwargs)
    names = extract_concept_names(concepts)
    assert names == expected_names
    if a_definition:
        assert a_definition in extract_definitions(concepts)
    else:
        assert not extract_definitions(concepts)


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
                source_ui="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
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
                source_ui="c31fc990-0824-4d8e-962b-86f56b33e580",
                source_desc="Bipolar joint prosthesis (physical object)",
                broader=True,
                stop_on_found=False,
                max_distance=1,
            ),
            [
                "Prostheses used to partially or totally replace a human or animal joint.",
                "artificial substitute, constructed of either synthetic or biological material, which is used to partially or totally replace or repair injured or diseased joints.",
                "Implantable prostheses designed for total or partial replacement of a joint. These prostheses typically consist of two or more articulated components; they are usually made of metal (e.g., cobalt-chromium alloys), hard plastics (e.g., polyethylene), or a combination of materials. Many joint prostheses include a component that resembles a ball and another that includes a socket. Some joint prostheses components may be used alone as a partial prosthesis; a total prosthesis usually includes all the components to permit complete replacement of the joint. Joint prostheses are implanted to replace articulations such as the knee, hip, ankle, shoulder, and elbow; they are used mainly in patients who suffer from osteoarthritis or rheumatoid arthritis, as well as after trauma.",
                "artificial substitute for a missing body part or function",
                "artificial substitute, constructed of either synthetic or biological material, which is used to partially or totally replace or repair injured or diseased muscles, cartilage, connective tissue, etc; for bones use BONE PROSTHESIS.",
                "Devices intended to replace non-functioning organs. They may be temporary or permanent. Since they are intended always to function as the natural organs they are replacing, they should be differentiated from PROSTHESES AND IMPLANTS and specific types of prostheses which, though also replacements for body parts, are frequently cosmetic (EYE, ARTIFICIAL) as well as functional (ARTIFICIAL LIMBS).",
                "Nonexpendable items used in the performance of orthopedic surgery and related therapy. They are differentiated from ORTHOTIC DEVICES, apparatus used to prevent or correct deformities in patients.",
                "Artificial substitutes for body parts, and materials inserted into tissue for functional, cosmetic, or therapeutic purposes. Prostheses can be functional, as in the case of artificial arms and legs, or cosmetic, as in the case of an artificial eye. Implants, all surgically inserted or grafted into the body, tend to be used therapeutically. IMPLANTS, EXPERIMENTAL is available for those used experimentally.",
                "A device, such as an artificial leg, that replaces a part of the body.",
                "Functional, reconstructive, and/or cosmetic artificial or, less frequently, biological passive replacements for missing, disabled, or abnormal tissues, organs, or other body parts. These devices may be externally attached to the body (e.g., nose, earlobe, upper limb, denture) or totally or partially implanted (e.g., joint prosthesis, ossicles). Prostheses intended for insertion into tubular body structures (e.g., biliary duct, ureter) to provide support and/or to maintain patency are usually called stents or endoprostheses; implantable prosthetic devices intended mainly for passive replacement of body parts (e.g., tooth root, ureter) are usually known as implants. Dedicated prostheses are available in many different sizes, shapes, and materials. They are used mainly in orthopedic (e.g., limbs, joints), cardiac (e.g., valves, heart ventricles), and other surgical procedures; to improve a patient's capabilities (e.g., dentures, eye lenses); and for reconstructive and/or cosmetic purposes (e.g., facial and body muscle enhancements).",
                "artificial substitute for a missing body part or function; used for functional or cosmetic reasons, or both.",
                "A device which is an artificial substitute for a missing body part or function; used for functional or cosmetic reasons, or both.",
                "Functional, reconstructive, and/or cosmetic artificial or, less frequently, biological passive replacements for missing, disabled, or abnormal tissues, organs, or other body parts. These devices may be externally attached to the body (e.g., nose, earlobe, upper limb, denture) or totally or partially implanted (e.g., joint prosthesis, ossicles). Prostheses intended for insertion into tubular body structures (e.g., biliary duct, ureter) to provide support and/or to maintain patency are usually called stents or endoprostheses; implantable prosthetic devices intended mainly for passive replacement of body parts (e.g., tooth root, ureter) are usually known as implants. Dedicated prostheses are available in many different sizes, shapes, and materials. They are used mainly in orthopedic (e.g., limbs, joints), cardiac (e.g., valves, heart ventricles), and other surgical procedures; to improve a patient's capabilities (e.g., dentures, eye lenses); and for reconstructive and/or cosmetic purposes (e.g., facial and body muscle enhancements).",
            ],
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
        api, source_vocab="snomed", source_ui="448169003"
    )

    pp = definitions_to_md(data)
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


@pytest.fixture()
def arg_parser():
    return lookup_defs.add_args(argparse.ArgumentParser())


@pytest.mark.parametrize(
    ("cli_args", "kwargs", "expected"),
    (
        (
            ["--source-vocab=snomed", "--source-ui=67362008"],
            dict(),
            "An abnormal balloon- or sac-like dilatation in the wall of AORTA.",
        ),
        (
            [],
            dict(source_vocab="snomed", source_ui="67362008"),
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
    defs = extract_definitions(result)
    assert expected in defs
