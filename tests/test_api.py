def test_cache(api):
    res1 = api.get_results(
        f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044"
    )
    res1.pop()
    res1.append("shit")
    res2 = api.get_results(
        f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044"
    )
    assert res1 != res2


def test_undocumented_call(api):
    concepts = api.get_related_concepts("C4517971")
    assert concepts
    cids = [_["concept"] for _ in concepts]
    assert cids == ["C3472551", "C1995000", "C1995000", "C1995000", "C1281593"]
