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
    ("kwargs", "expected_names"),
    (
        (dict(cui="C0559890"), ["Lumbosacral region of spine"]),
        (dict(cui="C3472551"), ["Entire back"]),
        (
            dict(cui="C0009044"),
            [
                "Colles' Fracture",
                "Closed fracture dislocation of wrist",
                "Bone structure of carpus",
                "Closed fracture of lower end of radius AND ulna",
                "Unspecified site injury",
            ],
        ),
        (dict(cui="C3887398"), ["something"]),
    ),
)
def test_get_relations(api, kwargs, expected_names):
    result = list(api.get_relations(**kwargs))
    names = [_["relatedIdName"] for _ in result]
    assert names == expected_names


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
    res = list(api.get_results(uri))

    include_uri = "https://uts-ws.nlm.nih.gov/rest/search/2021AB?includeObsolete=True&includeSuppressible=True&string=10937761000119101&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi"
    include_res = list(api.get_results(include_uri))

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
