from argparse import ArgumentParser

import pytest

from umlsrat.api.metathesaurus import MetaThesaurus


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


@pytest.mark.parametrize(
    ("kwargs", "rel_count"),
    (
        (dict(cui="C0009044"), 277),
        (dict(cui="C0009044", sabs=["MTH"]), 6),
        (dict(cui="C0009044", includeObsolete=True, includeSuppressible=True), 344),
    ),
)
def test_get_relations(api, kwargs, rel_count):
    data = list(api.get_relations(**kwargs))
    assert len(data) == rel_count


@pytest.mark.parametrize(
    ("kwargs", "atom_count", "expected_aui"),
    (
        (dict(cui="C3472551"), 0, None),
        (
            dict(cui="C3472551", includeObsolete=True, includeSuppressible=True),
            5,
            "A32611696",
        ),
        (dict(cui="C0009044", language="ENG"), 14, "A0542680"),
        (dict(cui="C1260922", language="ENG"), 59, "A33193650"),
        (dict(cui="C1260922", language="ENG", pageSize=1000), 59, "A33193650"),
    ),
)
def test_get_atoms_for_cui(api, kwargs, atom_count, expected_aui):
    atoms = list(api.get_atoms_for_cui(**kwargs))
    assert atoms is not None
    assert len(atoms) == atom_count
    if atoms:
        assert expected_aui in set(a.get("ui") for a in atoms)


@pytest.mark.parametrize(
    ("aui",),
    (
        ("A0243916",),
        ("A33193650",),
    ),
)
def test_get_atom(api, aui):
    atom = api.get_atom(aui=aui)
    assert atom["classType"] == "Atom"
    assert atom["ui"] == aui


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
    data = list(api.get_atom_ancestors(**kwargs))
    assert data
    assert len(data) == ancestor_count


@pytest.mark.parametrize(
    ["kwargs", "relation_count"],
    [
        (
            dict(
                source_vocab="MSH",
                concept_id="D002415",
                includeRelationLabels="RN,CHD",
                language="ENG",
            ),
            1,
        ),
        (dict(source_vocab="RCD", concept_id="S24..", language="ENG"), 13),
    ],
)
def test_get_source_relations(api, kwargs, relation_count):
    relations = list(api.get_source_relations(**kwargs))
    # all resulting relation labels should appear in the "includeRelationLabels"
    if "includeRelationLabels" in kwargs:
        for rel in relations:
            assert rel["relationLabel"] in kwargs["includeRelationLabels"]

    assert len(relations) == relation_count


@pytest.mark.parametrize(
    ("kwargs", "expected_cuis"),
    (
        (dict(query="cheese", max_results=1), ["C0007968"]),
        (
            dict(query="broken back bone"),
            ["C5693200", "C5693010", "C5693009"],
        ),
        (
            dict(query="broken back bone", string="cheese"),
            ["C5693200", "C5693010", "C5693009"],
        ),
    ),
)
def test_search(api, kwargs, expected_cuis):
    data = list(api.search(**kwargs))
    assert [_["ui"] for _ in data] == expected_cuis


@pytest.mark.parametrize(
    ("kwargs", "expected_name"),
    (
        (
            dict(source_vocab="snomed", concept_id="75508005"),
            "Dissecting",
        ),
        (
            dict(source_vocab="snomed", concept_id="5960008"),
            "Depressed structure",
        ),
        (
            dict(source_vocab="RCD", concept_id="S24.."),
            "Fracture of carpal bone",
        ),
    ),
)
def test_get_source_concept(api, kwargs, expected_name):
    data = api.get_source_concept(**kwargs)
    assert data["ui"] == kwargs["concept_id"]
    assert data["name"] == expected_name


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


@pytest.mark.parametrize(
    ("kwargs", "expected_names"),
    (
        (
            dict(source_vocab="snomed", concept_id="388594007", targetSource="MSH"),
            {
                "Raccoons",
            },
        ),
        (
            dict(source_vocab="CPT", concept_id="44950", targetSource="CPT"),
            {"Appendectomy", "Appendectomy", "Excision Procedures on the Appendix"},
        ),
        (
            dict(source_vocab="ICD10CM", concept_id="T87.44", language="SPA"),
            {"infección de muñón de amputación de extremidad inferior izquierda"},
        ),
    ),
)
def test_crosswalk(api, kwargs, expected_names):
    result = list(api.crosswalk(**kwargs))
    names = {_.get("name") for _ in result}
    assert names == expected_names


@pytest.mark.parametrize(
    ("kwargs", "expected_str"),
    (
        (
            dict(language="SPA"),
            "CPTSP,ICPCSPA,LNC-ES-AR,LNC-ES-ES,LNC-ES-MX,MDRSPA,MEDLINEPLUS_SPA,MSHSPA,SCTSPA,WHOSPA",
        ),
        (
            dict(language="GER"),
            "DMDICD10,DMDUMD,ICPCGER,LNC-DE-AT,LNC-DE-DE,MDRGER,MSHGER,WHOGER",
        ),
        (dict(language="SPA", sabs="LNC-ES-MX, MSH"), None),
        (dict(language="SPA", sabs="MSH"), None),
        (dict(language="SPA", sabs="LNC-ES-MX,LNC-ES-AR"), "LNC-ES-MX,LNC-ES-AR"),
        (dict(language="ENG", sabs="MSH"), "MSH"),
    ),
)
def test_sabs_str(api, kwargs, expected_str):
    if expected_str:
        sabs_str = api.get_sabs_str(**kwargs)
        assert sabs_str == expected_str
    else:
        with pytest.raises(ValueError):
            api.get_sabs_str(**kwargs)


def test_source_metadata(api):
    assert sum(1 for _ in api._source_metadata) == 187


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
        (dict(name="lnc", fuzzy=False), "LOINC"),
        (dict(name="MESH", fuzzy=True), "MeSH"),
        (dict(name="MESH", fuzzy=False), None),
        # this does not resolve
        (dict(name="Spanish LOINC", fuzzy=True), None),
    ),
)
def test_find_vocab_info(api, kwargs, expected_short_name):
    result = api.find_source_info(**kwargs)
    if not expected_short_name:
        assert not result
        with pytest.raises(ValueError):
            api.validate_source_abbrev(sab=kwargs["name"])
    else:
        assert result
        assert result["shortName"] == expected_short_name


@pytest.mark.parametrize(
    ("abbr", "expected_len", "expected_element"),
    (
        ("ENG", 107, "ICD10CM"),
        ("SPA", 10, "MSHSPA"),
        ("GER", 8, "MSHGER"),
        ("CZE", 2, "MSHCZE"),
        ("POL", 3, "MSHPOL"),
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


def test_args():
    parser = MetaThesaurus.add_args(ArgumentParser())
    args = parser.parse_args(["--use-cache", "False"])
    mt = MetaThesaurus.from_namespace(args)
    assert mt
    assert not mt.session.use_cache


def test_constructor():
    mt = MetaThesaurus()
    assert mt


_n_bamboo_results = 80


@pytest.mark.parametrize(
    ("kwargs", "expected_len"),
    (
        (dict(query="star trek vs star wars", pageSize=25), 0),
        (dict(query="bone", max_results=100, pageSize=25), 100),
        (
            dict(query="bamboo", max_results=100, pageSize=25),
            _n_bamboo_results,
        ),  # 99 bamboo concepts
        (
            dict(query="bamboo", max_results=100, pageSize=25, pageNumber=1),
            _n_bamboo_results,
        ),  # starting on page 1 yields all of them
        (
            dict(query="bamboo", max_results=100, pageSize=25, pageNumber=2),
            _n_bamboo_results - 25,
        ),  # starting on page 2 skips 25 of them
    ),
)
def test_pagination(api, kwargs, expected_len):
    results = list(api.search(**kwargs))
    assert len(results) == expected_len
