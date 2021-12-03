from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import definitions
from umlsrat.lookup.umls import find_umls

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = MetaThesaurus(rklopfer_api_key)


def find_single_mesh_def(snomed_code: str) -> str:
    cui = find_umls(api, "SNOMEDCT_US", snomed_code)
    def_dict = definitions.definitions_bfs(api, cui, num_defs=1, target_vocabs=('MSH',)).pop()
    return def_dict['value']


def test_old_back():
    # old back
    definition = find_single_mesh_def('450807008')
    assert definition


def test_wrist():
    # Closed fracture of left wrist (10937761000119101)
    definition = find_single_mesh_def('10937761000119101')
    assert definition


def test_find_definitions():
    defs = definitions.find_definitions(api, 'snomed', '282024004', 'ENG', num_defs=2)
    print(defs)
    assert defs