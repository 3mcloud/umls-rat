from umlsrat import lookup
from umlsrat.api import API
from umlsrat.vocabs import find_vocab_abbr

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = API(rklopfer_api_key)


def do_lookup(snomed_code: str) -> str:
    cui = lookup.find_umls(api, find_vocab_abbr('snomed'), snomed_code)
    def_dict = lookup.definitions_bfs(api, cui, num_defs=1, target_vocabs=('MSH',)).pop()
    return def_dict['value']


def test_old_back():
    # old back
    definition = do_lookup('450807008')
    assert definition


def test_find_umls_old_back():
    cui = lookup.find_umls(api, 'snomed', '450807008')
    print(cui)
    assert cui == 'C4517971'
    # assert cui == 'C3472551'


def test_definitions_bfs():
    cui = lookup.find_umls(api, 'snomed', '450807008')
    defs = lookup.definitions_bfs(api, cui, num_defs=1)
    assert defs


def test_lookup_wrist():
    # Closed fracture of left wrist (10937761000119101)
    definition = do_lookup('10937761000119101')
    assert definition


def test_find_umls_wrist():
    umlsc = lookup.find_umls(api, 'snomed', '10937761000119101')
    assert umlsc