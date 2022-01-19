from typing import Dict, List

import umlsrat.lookup.umls
from umlsrat.lookup import definitions


def extract_definitions(concepts: List[Dict]) -> List[str]:
    defs = []
    for concept in concepts:
        for d in concept["definitions"]:
            defs.append(d)
    return [d["value"] for d in defs]


def find_single_mesh_def(api, snomed_code: str) -> str:
    cui = umlsrat.lookup.umls.get_cui_for(api, "SNOMEDCT_US", snomed_code)
    concepts = definitions.definitions_bfs(
        api, cui, min_concepts=1, target_vocabs=("MSH",)
    )
    return extract_definitions(concepts).pop()


def test_old_back(api):
    # old back
    definition = find_single_mesh_def(api, "450807008")
    assert (
        definition
        == "The rear surface of an upright primate from the shoulders to the hip, "
        "or the dorsal surface of tetrapods."
    )


def test_wrist(api):
    # Closed fracture of left wrist (10937761000119101)
    definition = find_single_mesh_def(api, "10937761000119101")
    assert (
        definition
        == "Fractures in which the break in bone is not accompanied by an external wound."
    )


def test_find_definitions(api):
    data = definitions.find_defined_concepts(
        api, "snomed", "282024004", target_lang="ENG"
    )
    values = extract_definitions(data)
    assert values == [
        "region of the back between thorax and pelvis.",
        "The part of the spine in the lower back that consists of the lumbar region and the sacrum.",
        "Region of the back including the LUMBAR VERTEBRAE, SACRUM, and nearby structures.",
    ]


def test_find_normal_breath_sounds(api):
    data = definitions.find_defined_concepts(
        api, "snomed", "48348007", target_lang="ENG"
    )
    values = extract_definitions(data)
    assert values


def test_find_room_air(api):
    data = definitions.find_defined_concepts(
        api,
        source_vocab="snomed",
        source_code="37f13bfd-5fce-4c66-b8e4-1fefdd88a7e2",
        source_desc="Room air (substance)",
        min_concepts=2,
    )
    values = extract_definitions(data)
    assert values == [
        "Unmodified air as existing in the immediate surroundings.",
        "The mixture of gases present in the earth's atmosphere consisting of oxygen, nitrogen, carbon dioxide, and small amounts of other gases.",
        "A mixture of gases making up the earth's atmosphere, consisting mainly of nitrogen, oxygen, argon, and carbon dioxide.",
    ]


def test_find_without_code(api):
    data = definitions.find_defined_concepts(api, source_desc="Cancer")
    values = set(extract_definitions(data))
    assert values == {
        "Cancer begins in your cells, which are the building blocks of your body. Normally, your body forms new cells as you need them, replacing old cells that die. Sometimes this process goes wrong. New cells grow even when you don't need them, and old cells don't die when they should. These extra cells can form a mass called a tumor. Tumors can be benign or malignant. Benign tumors aren't cancer while malignant ones are. Cells from malignant tumors can invade nearby tissues. They can also break away and spread to other parts of the body.  Cancer is not just one disease but many diseases. There are more than 100 different types of cancer. Most cancers are named for where they start. For example, lung cancer starts in the lung, and breast cancer starts in the breast. The spread of cancer from one part of the body to another is called metastasis. Symptoms and treatment depend on the cancer type and how advanced it is. Most treatment plans may include surgery, radiation and/or chemotherapy. Some may involve hormone therapy, immunotherapy or other types of biologic therapy, or stem cell transplantation.  NIH: National Cancer Institute",
        "new abnormal tissue that grows by excessive cellular division and proliferation more rapidly than normal and continues to grow after the stimuli that initiated the new growth cease; tumors perform no useful body function and may be benign or malignant; benign neoplasms are a noncancerous growth that does not invade nearby tissue or spread to other parts of the body; malignant neoplasms or cancer show a greater degree of anaplasia and have the properties of invasion and metastasis; neoplasm terms herein do not distinguish between benign or malignant states, use references listed to cover this concept.",
        "A tumor composed of atypical neoplastic, often pleomorphic cells that invade other tissues. Malignant neoplasms often metastasize to distant anatomic sites and may recur after excision. The most common malignant neoplasms are carcinomas, Hodgkin and non-Hodgkin lymphomas, leukemias, melanomas, and sarcomas.",
        "Uncontrolled growth of abnormal cells with potential for metastatic spread.",
        "A group of diseases in which abnormal cells divide without control, invade nearby tissues and may also spread to other parts of the body through the blood and lymph systems.",
        "A general term for autonomous tissue growth exhibiting morphologic features of malignancy (e.g. severe atypia, nuclear pleomorphism, tumor cell necrosis, abnormal mitoses, tissue invasiveness) and for which the transformed cell type has not been specifically identified.",
        "A term for diseases in which abnormal cells divide without control and can invade nearby tissues. Malignant cells can also spread to other parts of the body through the blood and lymph systems. There are several main types of malignancy. Carcinoma is a malignancy that begins in the skin or in tissues that line or cover internal organs. Sarcoma is a malignancy that begins in bone, cartilage, fat, muscle, blood vessels, or other connective or supportive tissue. Leukemia is a malignancy that starts in blood-forming tissue such as the bone marrow, and causes large numbers of abnormal blood cells to be produced and enter the blood. Lymphoma and multiple myeloma are malignancies that begin in the cells of the immune system. Central nervous system cancers are malignancies that begin in the tissues of the brain and spinal cord.",
        'A tumor composed of atypical neoplastic, often pleomorphic cells that invade other tissues. Malignant neoplasms often metastasize to distant anatomic sites and may recur after excision. The most common malignant neoplasms are carcinomas (adenocarcinomas or squamous cell carcinomas), Hodgkin and non-Hodgkin lymphomas, leukemias, melanomas, and sarcomas. Check for "https://www.cancer.gov/about-cancer/treatment/clinical-trials/intervention/C9305" active clinical trials using this agent. ("http://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI%20Thesaurus&code=C9305" NCI Thesaurus)',
        "An organ or organ-system abnormality that consists of uncontrolled autonomous cell-proliferation which can occur in any part of the body as a benign or malignant neoplasm (tumour). [HPO:probinson]",
    }


def test_find_spanish(api):
    data = definitions.find_defined_concepts(
        api, source_desc="Cancer", target_lang="SPA"
    )
    values = extract_definitions(data)
    assert values == [
        "Crecimiento anormal y nuevo de tejido. Las neoplasias malignas muestran un mayor grado de anaplasia y tienen la propiedad de invasión y metástasis, comparados con las neoplasias benignas."
    ]
    # assert values == [
    #     'Neoplasia maligna formada por células epiteliales que tienden a infiltrarse en los tejidos circundantes y dan lugar a metástasis. Es un tipo histológico de neoplasia y no un sinónimo de "cáncer".'
    # ]


def test_pretty_print(api):
    data = definitions.find_defined_concepts(
        api, source_vocab="snomed", source_code="448169003"
    )

    pp = definitions.pretty_print_defs(data)
    assert (
        pp
        == """Felis catus
===========
1. The domestic cat, Felis catus, of the carnivore family FELIDAE,
comprising over 30 different breeds. The domestic cat is descended
primarily from the wild cat of Africa and extreme southwestern Asia.
Though probably present in towns in Palestine as long ago as 7000
years, actual domestication occurred in Egypt about 4000 years ago.
(From Walker's Mammals of the World, 6th ed, p801)
2. The domestic cat, Felis catus. (NCI)
3. The domesticated feline mammal, Felis catus, which is kept as a
house pet."""
    )
