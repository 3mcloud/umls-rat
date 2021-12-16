import functools
import re

from umlsrat.api.session import uncached_session, tgt_session

_auth_uri = "https://utslogin.nlm.nih.gov"
# option 1 - username/pw authentication at /cas/v1/tickets
# _auth_endpoint = "/cas/v1/tickets/"
# option 2 - api key authentication at /cas/v1/api-key
_auth_endpoint = "/cas/v1/api-key"

_FORM_ACTION_PAT = re.compile(r'<form action="(.+?)" method="POST">')


@functools.lru_cache(maxsize=1)
def get_tgt(api_key: str):
    # params = {'username': self.username,'password': self.password}
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
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._auth_svc = "http://umlsks.nlm.nih.gov"

    @property
    def ticket_granting_ticket(self):
        return get_tgt(self.api_key)

    def get_ticket(self):
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
