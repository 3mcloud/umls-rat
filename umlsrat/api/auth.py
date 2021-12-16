import functools
import re

from umlsrat.api.session import uncached_session, tgt_session

_auth_uri = "https://utslogin.nlm.nih.gov"
_auth_endpoint = "/cas/v1/api-key"

_FORM_ACTION_PAT = re.compile(r'<form action="(.+?)" method="POST">')


@functools.lru_cache(maxsize=1)
def get_tgt(api_key: str) -> str:
    """
    See: https://documentation.uts.nlm.nih.gov/rest/authentication.html

    :param api_key: an API key acquired after registering https://uts.nlm.nih.gov/uts/
    :return: API KEY
    """
    params = {"apikey": api_key}
    h = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
        "User-Agent": "python",
    }
    r = tgt_session().post(_auth_uri + _auth_endpoint, data=params, headers=h)
    r.raise_for_status()

    response_text = r.text

    result = _FORM_ACTION_PAT.search(response_text).group(1)
    assert result
    return result


class Authenticator(object):
    """
    See: https://documentation.uts.nlm.nih.gov/rest/authentication.html
    """

    def __init__(self, api_key: str):
        """
        Helper class for handling authentication calls.

        :param api_key: an API key acquired after registering https://uts.nlm.nih.gov/uts/
        """
        self.api_key = api_key
        self._auth_svc = "http://umlsks.nlm.nih.gov"

    @property
    def ticket_granting_ticket(self) -> str:
        return get_tgt(self.api_key)

    def get_ticket(self) -> str:
        params = {"service": self._auth_svc}
        h = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
            "User-Agent": "python",
        }

        tgt = self.ticket_granting_ticket

        r = uncached_session().post(tgt, data=params, headers=h)
        r.raise_for_status()

        st = r.text
        return st
