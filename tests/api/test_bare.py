import pytest
import requests

from umlsrat.api import session, auth


def check_url(api_key: str, url: str):
    ticket = auth.Authenticator(api_key).get_ticket()
    assert ticket
    response = requests.get(
        url, verify=session._pem_file_path, params={"ticket": ticket}
    )
    assert response


@pytest.mark.skip(reason="Unknown failure on server side")
def test_bad_one(api):
    check_url(
        api,
        "https://uts-api.nlm.nih.gov/content/angular/2021AB/CUI/C0205091/relatedConcepts",
    )


@pytest.mark.skip(reason="Failing 401")
def test_xxx(api):
    check_url(
        api,
        "https://uts-api.nlm.nih.gov/content/angular/2021AB/CUI/current/relatedConcepts",
    )
