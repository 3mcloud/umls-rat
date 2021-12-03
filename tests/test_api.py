from umlsrat.api.metathesaurus import MetaThesaurus

rklopfer_api_key = 'cf4e9f8f-a40c-4225-94e9-24ca9282b887'
api = MetaThesaurus(rklopfer_api_key)


def test_cache():
    res1 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    res1.pop()
    res1.append("shit")
    res2 = api.get_results(f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044")
    assert res1 != res2


def test_undocumented_call():
    concepts = api.get_related_concepts('C4517971')
    assert concepts
    cids = [_['concept'] for _ in concepts]
    assert cids == ['C3472551', 'C1995000', 'C1995000', 'C1995000', 'C1281593']


def do_search(term: str):
    the_concepts = None
    for it in ('sourceConcept', 'sourceDescriptor', 'sourceUi',):
        for st in ('words', 'normalizedWords', 'approximate'):
            concepts = api.search(term, inputType=it, searchType=st)
            # filter bogus results
            concepts = [_ for _ in concepts if _['ui']]
            if concepts:
                the_concepts = concepts
    return the_concepts


def test_search():
    concepts = do_search("Room air (substance)")
    print(concepts)
    concepts = do_search("Room air")
    print(concepts)
    concepts = do_search("Anticoagulant")
    print(concepts)
