from umlst.auth import Authenticator
from umlst.lookup import DefinitionsLookup

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'


def test_something():
    auth = Authenticator(rklopfer_api_key)
    dlu = DefinitionsLookup(auth)

    # old back
    definition = dlu.find_best('450807008')

    assert definition
