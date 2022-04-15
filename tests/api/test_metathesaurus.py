import pytest


def test_get_concept(api):
    c = api.get_concept("C0009044")
    assert c
    assert c.get("ui") == "C0009044"
    assert c.get("name") == "Closed fracture of carpal bone"


def test_get_relations(api):
    r = api.get_relations("C0009044")
    r = list(r)
    assert len(r) == 5


def test_cache(api):
    concept_url = "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044"
    res1 = api.get_single_result(concept_url)
    res1["foo"] = "bar"
    res2 = api.get_single_result(concept_url)
    assert res1 != res2


def test_cache_path(api):
    cp = api.cache_path

    assert cp


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
