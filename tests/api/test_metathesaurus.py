import pytest


@pytest.mark.parametrize(
    ("cui", "name"),
    [
        ("C0009044", "Closed fracture of carpal bone"),
        ("C3887398", "Closed fracture of left wrist"),
    ],
)
def test_get_concept(api, cui, name):
    c = api.get_concept(cui)
    assert c
    assert c.get("ui") == cui
    assert c.get("name") == name


@pytest.mark.parametrize(
    ["source_vocab", "concept_id", "allowable_labels", "expected_len"],
    [("MSH", "D002415", {"RN", "CHD"}, 1)],
)
def test_get_source_relations(
    api, source_vocab, concept_id, allowable_labels, expected_len
):
    relations = list(
        api.get_source_relations(
            source_vocab=source_vocab,
            concept_id=concept_id,
            includeRelationLabels=",".join(allowable_labels),
            language="ENG",
        )
    )
    # all resulting relation labels should appear in the "includeRelationLabels"
    for rel in relations:
        assert rel["relationLabel"] in allowable_labels

    # assert expected length
    assert len(relations) == expected_len


def test_include_flags(api):
    uri = "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    res = list(api._get_results(uri))

    include_uri = "https://uts-ws.nlm.nih.gov/rest/search/2021AB?includeObsolete=True&includeSuppressible=True&string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    include_res = list(api._get_results(include_uri))

    assert len(include_res) >= len(res)


def test_pagination(api):
    results = api.search("star trek vs star wars", pageSize=25)
    assert not list(results)
    results = api.search("bone", pageSize=25, max_results=100)
    assert len(list(results)) == 100


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    ((dict(cui="C3472551", includeObsolete=True, includeSuppressible=True), None),),
)
def test_get_atoms(api, kwargs, expected):
    result = list(api.get_atoms(**kwargs))
    assert result
    for atom in result:
        list(api.get_ancestors(atom["ui"]))


def test_cache(api):
    concept_url = "https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0009044"
    res1 = api._get_single_result(concept_url)
    # modify the result
    res1["foo"] = "bar"
    # pull the same URL
    res2 = api._get_single_result(concept_url)
    # make sure that we didn't get the modified object
    assert res1 != res2
