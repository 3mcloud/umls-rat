from umlst import lookup
from umlst.auth import Authenticator
from umlst.lookup import DefinitionsLookup

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
