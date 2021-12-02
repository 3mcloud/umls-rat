from umlsrat import lookup
from umlsrat.api import API
from umlsrat.util import Vocabularies

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = API(rklopfer_api_key)


def do_lookup(snomed_code: str) -> str:
    cui = lookup.find_umls(api, Vocabularies.SNOMEDCT, snomed_code)
    def_dict = lookup.definitions_bfs(api, cui, num_defs=1, target_vocabs=('MSH',)).pop()
    return def_dict['value']


def test_old_back():
    # old back
    definition = do_lookup('450807008')
    assert definition


def test_find_umls_old_back():
    cui = lookup.find_umls(api, Vocabularies.SNOMEDCT, '450807008')
    print(cui)
    assert cui == 'C4517971'
    # assert cui == 'C3472551'


def test_definitions_bfs():
    cui = lookup.find_umls(api, Vocabularies.SNOMEDCT, '450807008')
    defs = lookup.definitions_bfs(api, cui, num_defs=1)
    assert defs


def test_undocumented_call():
    concepts = api.get_related_concepts('C4517971')
    assert concepts
    assert len(concepts) == 5


def test_lookup_wrist():
    # Closed fracture of left wrist (10937761000119101)
    definition = do_lookup('10937761000119101')
    assert definition


def test_cache():
    res1 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    res1.pop()
    res1.append("shit")
    res2 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    assert res1 != res2


def test_find_umls_wrist():
    umlsc = lookup.find_umls(api, Vocabularies.SNOMEDCT, '10937761000119101')
    assert umlsc
