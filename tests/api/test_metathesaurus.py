import pytest


def test_cache(api):
    concept_url = "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044"
    res1 = api.get_single_result(concept_url)
    res1["foo"] = "bar"
    res2 = api.get_single_result(concept_url)
    assert res1 != res2


@pytest.mark.skip(reason="get_related_concepts is too unstable")
def test_undocumented_call(api):
    concepts = api.get_related_concepts("C4517971")
    assert concepts
    cids = [_["concept"] for _ in concepts]
    assert cids == ["C3472551", "C1995000", "C1995000", "C1995000", "C1281593"]


@pytest.mark.skip(reason="get_related_concepts is too unstable")
def test_find_definitions_left(api):
    # this will work .... ???
    results = api.get_related_concepts(
        "C0205091", relationLabels=",".join(("SY", "RN", "CHD"))
    )
    assert results
    concepts = [_["concept"] for _ in results]
    assert concepts == [
        "C2348232",
        "C1547871",
        "C1180147",
        "C1180147",
        "C0441987",
        "C0441987",
        "C0441987",
        "C0205089",
        "C0205089",
        "C0205089",
    ]


@pytest.mark.skip(reason="Unknown failure on server side -- too many results returned")
def test_find_definitions_left_fail(api):
    # the following will fail! -- BAD
    api.get_related_concepts("C0205091")
