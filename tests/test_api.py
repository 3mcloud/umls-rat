from umlsrat.api import API

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = API(rklopfer_api_key)


def test_cache():
    res1 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    res1.pop()
    res1.append("shit")
    res2 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    assert res1 != res2


def test_undocumented_call():
    concepts = api.get_related_concepts('C4517971')
    assert concepts
    assert len(concepts) == 5
