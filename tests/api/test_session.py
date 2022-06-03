from umlsrat import const


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