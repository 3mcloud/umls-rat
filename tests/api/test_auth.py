from umlsrat.api.auth import Authenticator


def test_get_ticket(api_key):
    auth = Authenticator(api_key)
    ticket = auth.get_ticket()
    assert ticket
