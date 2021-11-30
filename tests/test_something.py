from umlst import lookup, result
from umlst.auth import Authenticator
from umlst.lookup import DefinitionsLookup
from umlst.result import KeyValuePair

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'


def dlu(authenticator):
    return DefinitionsLookup(authenticator)


def do_lookup(snomed_id):
    return dlu(Authenticator(rklopfer_api_key)).find_best(snomed_id)


def test_old_back():
    # old back
    definition = do_lookup('450807008')
    assert definition


def test_something():
    # Closed fracture of left wrist (10937761000119101)
    definition = do_lookup('10937761000119101')
    assert definition


def test_find_umls_wrist():
    auth = Authenticator(rklopfer_api_key)

    umlsc = lookup.find_umls(auth, '10937761000119101')
    assert umlsc


def test_find_umls_old_back():
    auth = Authenticator(rklopfer_api_key)
    umlsc = lookup.find_umls(auth, '450807008')
    print(umlsc)
    assert umlsc


def test_find_definition_old_back():
    auth = Authenticator(rklopfer_api_key)
    definition = lookup.find_definitions(auth, '450807008')
    print(definition)
    assert definition


def do_walk(auth: Authenticator, snomed_concept_id: str):
    uri = f"https://uts-ws.nlm.nih.gov/rest/crosswalk/current/source/SNOMEDCT_US/{snomed_concept_id}"
    add_params = (KeyValuePair('targetSource', 'MSH'),)
    res = result.get_result(auth, uri, add_params)
    return res


def test_walk():
    auth = Authenticator(rklopfer_api_key)
    # res = do_walk(auth, '450807008')
    # print(res)
    # res = do_walk(auth, '77568009')
    # print(res)
    res = do_walk(auth, '123961009')
    print(res)

    assert res
    pass


def test_garbage():
    auth = Authenticator(rklopfer_api_key)

    def find(smid):
        return lookup.ConceptLookup(auth).find(smid)

    xx = [
        find('450807008'),
        find('77568009'),
        find('123961009'),
    ]
    assert xx
    ob = xx[0]
