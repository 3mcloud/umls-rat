import pytest
from requests import HTTPError

from umlsrat import const


@pytest.mark.parametrize(
    ("status_code",),
    (
        (500,),
        (503,),
    ),
)
def test_get_bad_results(mt_session, status_code):
    results = mt_session.get_results(f"http://httpstat.us/{status_code}")
    # this is okay because we have a generator
    assert results
    with pytest.raises(HTTPError) as e_info:
        # iterating raises and error
        next(results)
    assert e_info.value.response.status_code == status_code


def test_get_single_result(mt_session):
    result = mt_session.get_single_result("http://httpstat.us/400")
    assert result is None
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
