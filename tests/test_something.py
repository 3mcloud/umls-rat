from collections import defaultdict

from umlst import lookup
from umlst.api import KeyValuePair, API
from umlst.auth import Authenticator
from umlst.lookup import DefinitionsLookup
from umlst.util import Vocabularies

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = API(Authenticator(rklopfer_api_key))


def do_lookup(snomed_id):
    return DefinitionsLookup(api).find_best(snomed_id)


def test_old_back():
    # old back
    definition = do_lookup('450807008')
    assert definition


def test_find_umls_old_back():
    cui = lookup.find_umls(api, Vocabularies.SNOMEDCT, '450807008')
    print(cui)
    assert cui == 'C4517971'
    # assert cui == 'C3472551'


def test_find_definition_old_back():
    definition = lookup.find_definitions(api, Vocabularies.SNOMEDCT, '450807008')
    print(definition)
    assert definition


def test_definitions_bfs():
    cui = lookup.find_umls(api, Vocabularies.SNOMEDCT, '450807008')
    defs = lookup.definitions_bfs(api, cui)
    print(defs)
    assert defs


# def test_stuff():
#     base_concept = api.get_source_concept(Vocabularies.SNOMEDCT, '450807008')
#     print(base_concept)


def test_steps():
    concept = api.get_concept('C1995000')
    print(concept)
    relations = api.get_relations('C1995000')
    print(relations)

    mapping = defaultdict(list)
    for x in relations:
        label = x['relationLabel']
        if label in ('RN', 'RB'):
            mapping[label].append(x)

    print(mapping)


def test_undocumented_call():
    concepts = api.get_related_concepts('C4517971')
    print(concepts)
    assert concepts

    xxx = api.get_related_concepts('C1281593')
    print(xxx)


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


def do_walk(snomed_concept_id: str):
    uri = f"https://uts-ws.nlm.nih.gov/rest/crosswalk/current/source/SNOMEDCT_US/{snomed_concept_id}"
    add_params = (KeyValuePair('targetSource', 'MSH'),)
    res = api.get_results(uri, add_params)
    return res


def test_walk():
    # res = do_walk('450807008')
    # print(res)
    # res = do_walk('77568009')
    # print(res)
    res = do_walk('123961009')
    print(res)

    assert res
    pass


def test_garbage():
    def find(smid):
        return lookup.ConceptLookup(api).find(Vocabularies.SNOMEDCT, smid)

    xx = [
        find('450807008'),
        find('77568009'),
        find('123961009'),
    ]
    assert xx
    ob = xx[0]
