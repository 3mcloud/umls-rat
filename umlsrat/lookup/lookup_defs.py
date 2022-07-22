import argparse
import collections
import itertools
import logging
import operator
import os.path
from typing import Optional, Iterable, List, Dict, Callable, Set, Any

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import graph_fn, lookup_umls
from umlsrat.lookup.graph_fn import Action
from umlsrat.util import orderedset, text, iterators
from umlsrat.util.args_util import str2bool
from umlsrat.util.orderedset import FIFO

logger = logging.getLogger(os.path.basename(__file__))


def _resolve_semantic_types(api: MetaThesaurus, concept: Dict) -> Set[str]:
    """Resolve semantic type data and return the set of type names assigned to this concept"""
    type_names = set()

    sem_types = concept["semanticTypes"]
    if not sem_types:
        return type_names

    for st in sem_types:
        type_names.add(st["name"])
        st_uri = st.pop("uri", None)
        if st_uri:
            st["data"] = api.session.get_single_result(st_uri)

    return type_names


def _clean_definition(definition: Dict) -> Dict:
    # clean "value"
    return {
        k: text.clean_definition_text(v) if k == "value" else v
        for k, v in definition.items()
    }


def _definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    get_neighbors: Callable[[MetaThesaurus, str], List[str]],
    stop_on_found: Optional[bool] = True,
    max_distance: int = None,
    target_vocabs: Optional[Iterable[str]] = None,
    language: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS for concepts with associated definitions.


    Resulting concepts
    are returned in order of closest to farthest (relative to ``start_cui``). Within each concept,
    definitions are sorted by length (shortest to longest).


    :param get_neighbors: fn to get neighbors of a CUI (e.g. get_broader or get_narrower)
    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param stop_on_found: stop searching after processing first level containing defined concepts
    :param max_distance: maximum allowed distance from `start_cui` (0/None = Infinity)
    :param target_vocabs: only allow definitions from these vocabularies
    :param language: target language
    :param preserve_semantic_type: preserve the semantic type assigned to ``start_cui``
    :return: a list of Concepts with Definitions
    """
    assert api
    assert start_cui
    if max_distance is None:
        max_distance = 0
    assert max_distance >= 0
    if not stop_on_found and not max_distance:
        logger.warning(
            f"stop_on_found = {stop_on_found} and max_distance = {max_distance}; this "
            f"could result in an unintentionally massive search space. Recommend setting "
            f"`max_distance=2` and go from there."
        )

    # first get target vocabs based on language
    if target_vocabs:
        target_vocabs = set(target_vocabs)
        for tv in target_vocabs:
            info = api.find_source_info(tv)
            assert (
                info.get("language").get("abbreviation") == language
            ), f"Requested vocabulary {tv} is not in the target language {language}"
    else:
        target_vocabs = set(api.sources_for_language(language))
        assert target_vocabs, f"No vocabularies for language abbreviation '{language}'"

    # If we want to preserve semantic type, we need to get them for the start CUI

    if preserve_semantic_type:
        start_sem_types = _resolve_semantic_types(api, api.get_concept(start_cui))

        def allowed_sem_type(concept: Dict) -> bool:
            sem_types = set(d.get("name") for d in concept.get("semanticTypes"))
            return bool(start_sem_types & sem_types)

    else:
        start_sem_types = None

        def allowed_sem_type(concept: Dict) -> bool:
            return True

    ##
    # visit will accumulate definitions
    ##
    defined_concepts = []

    def visit(api: MetaThesaurus, current_cui: str, current_dist: int):
        current_concept = api.get_concept(current_cui)

        # if this url is not populated, there certainly are no definitions
        if not current_concept["definitions"]:
            return

        definitions = list(api.get_definitions(current_cui))

        # filter defs not in target vocab
        if target_vocabs:
            definitions = [_ for _ in definitions if _["rootSource"] in target_vocabs]

        if not definitions:
            return

        # clean text, sort by length, and drop duplicates
        cleaned = orderedset.UniqueFIFO(
            sorted(map(_clean_definition, definitions), key=lambda _: len(_["value"])),
            keyfn=lambda _: f"{_['rootSource']}/{text.normalize(_['value'])}",
        )

        current_concept["definitions"] = cleaned.items
        _resolve_semantic_types(api, current_concept)
        current_concept["distanceFromOrigin"] = current_dist

        # only add concepts with an allowed semantic type
        if not allowed_sem_type(current_concept):
            return

        # reorder dict for readability
        reordered_concept = collections.OrderedDict(
            (k, current_concept.pop(k))
            for k in (
                "classType",
                "ui",
                "name",
                "distanceFromOrigin",
                "definitions",
            )
        )
        reordered_concept.update(current_concept)

        # add to defined concepts
        defined_concepts.append(reordered_concept)

    ##
    # post visit actions are based on number of definitions and current distance from origin
    def post_visit(
        api: MetaThesaurus, current_cui: str, current_dist: int, distances: FIFO
    ) -> Action:
        if stop_on_found and defined_concepts:
            if not distances or distances.peek() > current_dist:
                return Action.STOP
            else:
                return Action.SKIP

        if max_distance and current_dist == max_distance:
            return Action.SKIP

        return Action.NONE

    # here we actually do the search
    graph_fn.breadth_first_search(
        api=api,
        start_cui=start_cui,
        visit=visit,
        get_neighbors=get_neighbors,
        post_visit=post_visit,
    )

    return defined_concepts


def definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    broader: Optional[bool] = True,
    stop_on_found: Optional[bool] = True,
    max_distance: Optional[int] = None,
    target_vocabs: Optional[Iterable[str]] = None,
    language: Optional[str] = "ENG",
    preserve_semantic_type: Optional[bool] = False,
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS for concepts with associated definitions.

    Resulting concepts are returned in order of closest to farthest (relative to ``start_cui``).
    Within each concept, definitions are sorted by length (shortest to longest).

    Use this method when you have a CUI. If you do not have a CUI,
    use :meth:`umlsrat.lookup.definitions.find_defined_concepts`

    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param broader: search broader concepts. If false, search narrower.
    :param stop_on_found: stop searching after processing first level containing defined concepts
    :param max_distance: maximum allowed distance from `start_cui` (Default = None = 0 = Infinity)
    :param target_vocabs: only allow definitions from these vocabularies
    :param language: only consider concepts in this language
    :param preserve_semantic_type: preserve the semantic type assigned to ``start_cui``
    :return: a list of Concepts with Definitions
    """

    def get_neighbors(api: MetaThesaurus, cui: str) -> List[str]:
        if broader:
            return lookup_umls.get_broader_cuis(api, cui, language=language)
        else:
            return lookup_umls.get_narrower_cuis(api, cui, language=language)

    return _definitions_bfs(
        api=api,
        start_cui=start_cui,
        get_neighbors=get_neighbors,
        stop_on_found=stop_on_found,
        max_distance=max_distance,
        target_vocabs=target_vocabs,
        language=language,
        preserve_semantic_type=preserve_semantic_type,
    )


def find_defined_concepts(
    api: MetaThesaurus,
    source_vocab: str = None,
    concept_id: str = None,
    source_desc: str = None,
    broader: Optional[bool] = True,
    stop_on_found: Optional[bool] = True,
    max_distance: Optional[int] = None,
    language: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Find defined concepts in UMLS which are equivalent to or *broader* than the source concept.

    Resulting concepts are returned in order of closest to farthest (relative to ``start_cui``).
    Within each concept, definitions are sorted by length (shortest to longest).

    Use this function when you do not have a UMLS CUI. If you do have a CUI, you can use
    :meth:`umlsrat.lookup.definitions.broader_definitions_bfs`.

    1. Look up CUIs
        * use the source UI (if given). if not found,
        * use the source description
    2. Run :meth:`umlsrat.lookup.definitions.broader_definitions_bfs` for resulting CUIs

    :param api: MetaThesaurus API
    :param source_vocab: source vocab
    :param concept_id: source concept id
    :param source_desc: source concept description
    :param broader: search broader concepts. If false, search narrower.
    :param stop_on_found: stop searching after processing first level containing defined concepts
    :param max_distance: stop searching after reaching this distance from the original source \
    concept. (Default = None = Infinity)
    :param language: only consider concepts in this language
    :param preserve_semantic_type: only search concept which have the same semantic type as the starting concept
    :return: a list of Concepts with Definitions
    """

    if concept_id:
        assert source_vocab, f"Must provide source vocab for code {concept_id}"
    else:
        assert (
            source_desc
        ), "Must provide either source code and vocab or descriptor (source_desc)"

    if logger.isEnabledFor(logging.INFO):
        msg = f"Finding {language} definition(s) of"
        if concept_id:
            msg = f"{msg} {source_vocab}/{concept_id}"

        if source_desc:
            msg = f"{msg} [{source_desc}]"

        logger.info(msg)

    def definitions_search(start_cui: str) -> List[Dict]:
        data = definitions_bfs(
            api,
            start_cui=start_cui,
            broader=broader,
            stop_on_found=stop_on_found,
            max_distance=max_distance,
            language=language,
            preserve_semantic_type=preserve_semantic_type,
        )

        return data

    if concept_id:
        cuis_from_code = lookup_umls.get_cuis_for(
            api, source_vocab=source_vocab, concept_id=concept_id
        )
        if cuis_from_code:
            logger.info(f"Broader BFS for base CUIs {cuis_from_code} ")

            defined_concepts = itertools.chain.from_iterable(
                definitions_search(cui) for cui in cuis_from_code
            )
            # since we searched multiple CUIs, ensure that they are returned in
            # order of closest to farthest. Also, need to ensure uniqueness.
            unique_defined_concepts = {c["ui"]: c for c in defined_concepts}

            if unique_defined_concepts:
                return sorted(
                    unique_defined_concepts.values(),
                    key=lambda _: _.get("distanceFromOrigin"),
                )
            logger.info("No broader concepts with definitions.")
        else:
            logger.info(f"UMLS concept not found for {source_vocab}/{concept_id}")

    # did not find the concept directly (by code)
    if source_desc:
        # if we have a source description, try to use it to find a CUI
        # Use strict matching if we were provided with a source code initially. This will happen if
        # the provided code is an MModal addition (not in original vocab).
        cleaned = text.remove_trailing_parens(source_desc)
        max_search_results = 5  # only check the top 5 results
        search_result = lookup_umls.term_search(
            api,
            term=cleaned,
            max_results=max_search_results,
            strict_match=bool(concept_id),
        )

        if search_result:
            search_term = search_result["searchTerm"]
            logger.info(f"Results for term search '{search_term}'")

            for concept in search_result["concepts"]:
                cui = concept["ui"]
                name = concept["name"]
                logger.info(f"Searching concept '{name}' {cui}")
                defs = definitions_search(cui)
                if defs:
                    return defs

    return []


def add_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add arguments for search functions. Expected to be used with :meth:`find_builder`

    :param parser: the parser
    :return: same parser
    """
    df_group = parser.add_argument_group("Definitions Finder")

    # cui_search = df_group.add_argument_group("CUI Search")
    df_group.add_argument(
        "--start-cui", help="starting Concept ID", type=str, default=None
    )

    # sa_search = df_group.add_argument_group("Source Asserted Search")
    df_group.add_argument("--source-vocab", help="source vocab", type=str, default=None)
    df_group.add_argument(
        "--concept-id", help="source concept id", type=str, default=None
    )
    df_group.add_argument(
        "--source-desc", help="source concept description", type=str, default=None
    )

    df_group.add_argument(
        "--search-broader",
        help="search broader concepts. If false, search narrower.",
        type=str2bool,
        default=True,
        dest="broader",
    )
    df_group.add_argument(
        "--stop-on-found",
        help="stop searching after processing first level containing defined concepts",
        type=str2bool,
        default=True,
    )

    df_group.add_argument(
        "--max-distance",
        help="maximum allowed distance from `start_cui` (Default = 0 = Infinity)",
        type=int,
        default=0,
    )
    df_group.add_argument(
        "--language",
        help="only consider concepts in this language",
        type=str,
        default="ENG",
    )

    df_group.add_argument(
        "--preserve-semantic-type",
        help="preserve the semantic type assigned to start concept",
        type=str2bool,
        default=False,
    )

    return parser


_EXPECTED_KWARG_NAMES = vars(add_args(argparse.ArgumentParser()).parse_args([])).keys()


def find_builder(api: MetaThesaurus, parsed_args: argparse.Namespace):
    """
    Build a method to find defined concepts. Calls either :meth:`definitions_bfs` or
    :meth:`find_defined_concepts` depending on the args. Additional arguments are passed as keyword
    arguments. Such arguments override those passed with `parsed_args`

    :param api: MetaThesaurus API object
    :param parsed_args: parsed args. see :meth:`add_args`
    :return: function to find defined concepts
    """
    vargs = vars(parsed_args)
    # white list
    base_kwargs = {k: vargs[k] for k in _EXPECTED_KWARG_NAMES}
    # drop None
    base_kwargs = {k: v for k, v in base_kwargs.items() if v is not None}

    def find_fun(**kwargs: Any) -> List[Dict]:
        # override base kwargs
        merged_kwargs = base_kwargs.copy()
        merged_kwargs.update(kwargs)

        is_cui_search = "start_cui" in merged_kwargs
        is_source_search = (
            "source_vocab" in merged_kwargs
            or "concept_id" in merged_kwargs
            or "source_desc" in merged_kwargs
        )
        assert operator.xor(is_cui_search, is_source_search), (
            "Expected either 'start_cui' or some source asserted info such as "
            "'source_vocab', 'concept_id' 'source_desc' -- not both."
        )

        if is_cui_search:
            return definitions_bfs(api=api, **merged_kwargs)
        elif is_source_search:
            return find_defined_concepts(api=api, **merged_kwargs)
        else:
            raise AssertionError("Unreachable code")

    return find_fun


def definitions_itr(concepts: List[Dict]) -> Iterable[str]:
    """Iterate over definitions. Nearest to farthest. If there are multiple concepts at a given
    distance iterate over them, in a round-robin order"""
    # group by distance; anything closer will always come first
    for dist, group in itertools.groupby(
        concepts, key=lambda _: _["distanceFromOrigin"]
    ):
        defs = ((obj.get("value") for obj in _.get("definitions")) for _ in group)
        yield from iterators.roundrobin(*defs)
