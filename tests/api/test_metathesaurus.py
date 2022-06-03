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
    ("cui", "definitions"),
    (
        (
            "C0009044",
            [
                "A traumatic break in one or more of the carpal bones that does not involve a break in the adjacent skin."
            ],
        ),
    ),
)
def test_get_definitions(api, cui, definitions):
    data = list(api.get_definitions(cui))
    defs = [_["value"] for _ in data]
    assert defs == definitions


@pytest.mark.parametrize(("cui", "rel_count"), (("C0009044", 5),))
def test_get_relations(api, cui, rel_count):
    data = list(api.get_relations(cui))
    assert len(data) == rel_count


@pytest.mark.parametrize(
    ("kwargs", "atom_count"),
    (
        (dict(cui="C3472551", includeObsolete=True, includeSuppressible=True), 5),
        (dict(cui="C0009044", language="ENG"), 13),
    ),
)
def test_get_atoms(api, kwargs, atom_count):
    data = list(api.get_atoms(**kwargs))
    assert data
    assert len(data) == atom_count


@pytest.mark.parametrize(
    ("kwargs", "ancestor_count"),
    (
        (
            dict(
                aui="A0243916",
            ),
            16,
        ),
        (dict(aui="A8349179"), 6),
    ),
)
def test_get_ancestors(api, kwargs, ancestor_count):
    data = list(api.get_ancestors(**kwargs))
    assert data
    assert len(data) == ancestor_count


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


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            dict(query="cheese", max_results=1),
            [
                {
                    "ui": "C0007968",
                    "rootSource": "MTH",
                    "uri": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0007968",
                    "name": "Cheese",
                }
            ],
        ),
        (
            dict(query="broken back bone"),
            [
                {
                    "ui": "C5405410",
                    "rootSource": "CPT",
                    "uri": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C5405410",
                    "name": "Closed treatment of broken forearm (ulna)bone at the elbow area on the inside or back part of the arm with manipulation",
                }
            ],
        ),
    ),
)
def test_search(api, kwargs, expected):
    data = list(api.search(**kwargs))
    assert data == expected


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            dict(source_vocab="snomed", concept_id="75508005"),
            {
                "classType": "SourceAtomCluster",
                "ui": "75508005",
                "suppressible": False,
                "obsolete": False,
                "rootSource": "SNOMEDCT_US",
                "atomCount": 2,
                "cVMemberCount": 0,
                "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/attributes",
                "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms",
                "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/ancestors",
                "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/parents",
                "children": None,
                "descendants": None,
                "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/relations",
                "definitions": None,
                "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=75508005&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi",
                "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms/preferred",
                "subsetMemberships": [
                    {
                        "memberUri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000/member/75508005",
                        "uri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000",
                        "name": "CTV3 simple map",
                    }
                ],
                "contentViewMemberships": [],
                "name": "Dissecting",
            },
        ),
        (
            dict(source_vocab="snomed", concept_id="5960008"),
            {
                "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/ancestors",
                "atomCount": 3,
                "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/atoms",
                "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/attributes",
                "cVMemberCount": 0,
                "children": None,
                "classType": "SourceAtomCluster",
                "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=5960008&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi",
                "contentViewMemberships": [],
                "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/atoms/preferred",
                "definitions": None,
                "descendants": None,
                "name": "Depressed structure",
                "obsolete": False,
                "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/parents",
                "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/5960008/relations",
                "rootSource": "SNOMEDCT_US",
                "subsetMemberships": [
                    {
                        "memberUri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000/member/5960008",
                        "name": "CTV3 simple map",
                        "uri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000",
                    }
                ],
                "suppressible": False,
                "ui": "5960008",
            },
        ),
    ),
)
def test_get_source_concept(api, kwargs, expected):
    data = api.get_source_concept(**kwargs)
    assert data == expected


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    ((dict(source_vocab="MSH", concept_id="D002415"), ["Felis"]),),
)
def test_get_source_parents(api, kwargs, expected_names):
    data = list(api.get_source_parents(**kwargs))
    names = [_["name"] for _ in data]
    assert names == expected_names


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(source_vocab="MSH", concept_id="D002415"),
            [
                "Carnivora",
                "Mammals",
                "Vertebrates",
                "Organisms (MeSH Category)",
                "Medical Subject Headings",
                "Eukaryota",
                "Topical Descriptor",
                "MeSH Descriptors",
                "Animals",
                "Chordata",
                "Eutheria",
                "Feliformia",
                "Felidae",
                "Felis",
            ],
        ),
    ),
)
def test_get_source_ancestors(api, kwargs, expected_names):
    data = list(api.get_source_ancestors(**kwargs))
    names = [_["name"] for _ in data]
    assert names == expected_names


def test_source_metadata(api):
    assert sum(1 for _ in api._source_metadata) == 222


@pytest.mark.parametrize(
    ("sab", "exists"),
    (
        ("SNOMEDCT_US", True),
        ("snomed", False),
        ("LNC", True),
        ("LOINC", False),
        ("MM-LOINC", False),
        ("MSH", True),
    ),
)
def test_source_metadata_index(api, sab, exists):
    metadata = api.source_metadata_index
    if exists:
        assert sab in metadata
    else:
        assert sab not in metadata


@pytest.mark.parametrize(
    ("kwargs", "expected_short_name"),
    (
        (dict(name="snomed"), "SNOMED CT, US Edition"),
        (dict(name="SNOMEDCT_US"), "SNOMED CT, US Edition"),
        (dict(name="LOINC", fuzzy=False), "LOINC"),
        (dict(name="MESH", fuzzy=True), "MeSH"),
        # this does not resolve
        (dict(name="Spanish LOINC", fuzzy=True), None),
    ),
)
def test_find_vocab_info(api, kwargs, expected_short_name):
    result = api.find_source_info(**kwargs)
    if not expected_short_name:
        assert not result
    else:
        assert result
        assert result["shortName"] == expected_short_name


@pytest.mark.parametrize(
    ("abbr", "expected_len", "expected_element"),
    (
        ("ENG", 150, "ICD10CM"),
        ("SPA", 9, "MSHSPA"),
        ("GER", 8, "MSHGER"),
        ("CZE", 2, "MSHCZE"),
        ("POL", 1, "MSHPOL"),
        ("FRA", 0, None),  # FRA? Nope; FRE.
        ("FRE", 8, "MSHFRE"),
    ),
)
def test_vocabs_for_language(api, abbr, expected_len, expected_element):
    result = api.sources_for_language(abbr)
    assert len(result) == expected_len
    assert not result or expected_element in result


@pytest.mark.parametrize(
    ("abbr", "expected"), (("ENG", "ENG"), ("eng", "ENG"), ("FRA", None))
)
def test_validate_language_abbrev(api, abbr, expected):
    if expected is not None:
        assert api.validate_language_abbrev(abbr) == expected
    else:
        with pytest.raises(ValueError):
            api.validate_language_abbrev(abbr)


def test_pagination(api):
    results = api.search("star trek vs star wars", pageSize=25)
    assert not list(results)
    results = api.search("bone", pageSize=25, max_results=100)
    assert len(list(results)) == 100
