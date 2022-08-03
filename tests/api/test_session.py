import multiprocessing
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from urllib.parse import urlparse

import pytest
from requests import HTTPError

from umlsrat import const


class ResponseCodeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        status_code = int(parsed.path.strip("/"))

        self.send_response(status_code)
        self.end_headers()


_HOSTPORT_PAIR = ("localhost", 1919)
_HOSTPORT_STR = ":".join(map(str, _HOSTPORT_PAIR))


def server(host: str, port: int):
    s = HTTPServer((host, port), ResponseCodeHandler)
    s.serve_forever()


@pytest.fixture(autouse=True)
def start_server():
    p = multiprocessing.Process(target=server, args=_HOSTPORT_PAIR)
    p.start()
    sleep(0.5)
    yield True
    p.terminate()


@pytest.mark.parametrize(
    ("status_code",),
    (
        (500,),
        (503,),
    ),
)
def test_raise_for_status(mt_session, start_server, status_code):
    assert start_server
    results = mt_session.get_results(f"http://{_HOSTPORT_STR}/{status_code}")
    # this is okay because we have a generator
    assert results
    with pytest.raises(HTTPError) as e_info:
        # iterating raises and error
        next(results)
    assert e_info.value.response.status_code == status_code


@pytest.mark.parametrize(
    ("status_code",),
    (
        (400,),
        (404,),
    ),
)
def test_not_found_status(mt_session, status_code):
    result = mt_session.get_single_result(f"http://{_HOSTPORT_STR}/{status_code}")
    assert result is None


def test_get_single_result(mt_session):
    result = mt_session.get_single_result(
        "https://uts-ws.nlm.nih.gov/rest/content/2022AA/CUI/C0009044"
    )
    assert result is not None


def test_include_flags(mt_session):
    uri = f"https://uts-ws.nlm.nih.gov/rest/search/{const.DEFAULT_UMLS_VERSION}?string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    res = list(mt_session.get_results(uri))

    include_uri = f"https://uts-ws.nlm.nih.gov/rest/search/{const.DEFAULT_UMLS_VERSION}?includeObsolete=True&includeSuppressible=True&string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    include_res = list(mt_session.get_results(include_uri))

    assert len(include_res) >= len(res)


def test_cache(mt_session):
    concept_url = f"https://uts-ws.nlm.nih.gov/rest/content/{const.DEFAULT_UMLS_VERSION}/CUI/C0009044"
    res1 = mt_session.get_single_result(concept_url)
    # modify the result
    res1["foo"] = "bar"
    # pull the same URL
    res2 = mt_session.get_single_result(concept_url)
    # make sure that we didn't get the modified object
    assert res1 != res2
