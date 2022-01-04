import logging
import os.path
from collections import defaultdict
from enum import Enum
from typing import Callable, Optional, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util.orderedset import UniqueFIFO, FIFO

logger = logging.getLogger(os.path.basename(__file__))


class Action(Enum):
    STOP = 0
    SKIP = 1
    NONE = 3


def _visit(api: MetaThesaurus, cui: str, distance: int) -> None:
    raise NotImplementedError


def _pre_visit_passthrough(api: MetaThesaurus, cui: str, distance: int) -> Action:
    return Action.NONE


def _post_visit_passthrough(api: MetaThesaurus, cui: str, distance: int) -> Action:
    return Action.NONE


def _get_broader_concepts(api: MetaThesaurus, cui: str, distance: int) -> Iterable[str]:
    allowed_relations = ("SY", "RN", "CHD")
    allowed_relations_str = ",".join(allowed_relations)

    related_concepts = api.get_related_concepts(
        cui, relationLabels=allowed_relations_str
    )

    # group by relation type
    grouped = defaultdict(list)
    for rc in related_concepts:
        rcuid = rc["concept"]
        if rcuid not in visited and rcuid not in to_visit:
            grouped[rc["label"]].append(rcuid)

    for rtype in allowed_relations:
        cuis = grouped[rtype]
        to_visit.push_all(cuis)
        distances.push_all([current_dist + 1] * len(cuis))


def breadth_first_search(
    api: MetaThesaurus,
    start_cui: str,
    visit: Callable[[MetaThesaurus, str, int], None],
    pre_visit: Optional[
        Callable[[MetaThesaurus, str, int], Action]
    ] = _pre_visit_passthrough,
    post_visit: Optional[
        Callable[[MetaThesaurus, str, int], Action]
    ] = _post_visit_passthrough,
) -> None:
    """
    Do a breadth-first search over UMLS, hunting for definitions. Neighbors are determined
    by :py:meth:`umlsrat.api.metathesaurus.MetaThesaurus.get_related_concepts` and restricted to
    ("SY", "RN", "CHD") relations -- which  means we only search "higher" in the tree.

    Resulting umlsrat.lookup.graph_fn.Action of `pre_visit` and `post_visit` allow additional
    control of the search. By default these do nothing.

    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param visit: applied to each visited concept
    :param pre_visit: applied before visiting a concept. default: do nothing
    :param post_visit: applied after visiting a concept. default: do nothing
    """
    assert api
    assert start_cui

    to_visit = UniqueFIFO([start_cui])
    distances = FIFO([0])

    visited = set()

    allowed_relations = ("SY", "RN", "CHD")
    allowed_relations_str = ",".join(allowed_relations)
    while to_visit:
        current_cui = to_visit.peek()
        current_dist = distances.peek()

        pre_visit_action = pre_visit(api, current_cui, current_dist)
        if pre_visit_action == Action.STOP:
            break

        if pre_visit_action != Action.SKIP:
            visit(api, current_cui, current_dist)

        ## Mark as visited
        visited.add(to_visit.pop())
        distances.pop()

        logger.info(
            f"curDistance = {current_dist} "
            f"numToVisit = {len(to_visit)} "
            f"numVisited = {len(visited)}"
        )

        if pre_visit_action == Action.SKIP:
            continue

        post_visit_action = post_visit(api, current_cui, current_dist)

        if post_visit_action == Action.STOP:
            break

        if post_visit_action == Action.SKIP:
            continue

        ## Find neighbors and add to_visit
        related_concepts = api.get_related_concepts(
            current_cui, relationLabels=allowed_relations_str
        )

        # group by relation type
        grouped = defaultdict(list)
        for rc in related_concepts:
            rcuid = rc["concept"]
            if rcuid not in visited and rcuid not in to_visit:
                grouped[rc["label"]].append(rcuid)

        for rtype in allowed_relations:
            cuis = grouped[rtype]
            to_visit.push_all(cuis)
            distances.push_all([current_dist + 1] * len(cuis))
