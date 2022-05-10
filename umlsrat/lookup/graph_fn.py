import logging
import os.path
from enum import Enum
from typing import Callable, Optional, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util.orderedset import UniqueFIFO, FIFO

logger = logging.getLogger(os.path.basename(__file__))


class Action(Enum):
    # stop the search
    STOP = 0
    # do not apply visit() and do not accu neighbors
    SKIP = 1
    # normal behavior
    NONE = 3


def _pre_visit_passthrough(api: MetaThesaurus, cui: str, distance: int) -> Action:
    return Action.NONE


def _post_visit_passthrough(api: MetaThesaurus, cui: str, distance: int) -> Action:
    return Action.NONE


def breadth_first_search(
    api: MetaThesaurus,
    start_cui: str,
    visit: Callable[[MetaThesaurus, str, int], None],
    get_neighbors: Callable[[MetaThesaurus, str], Iterable[str]],
    pre_visit: Optional[Callable[[MetaThesaurus, str, int], Action]] = None,
    post_visit: Optional[Callable[[MetaThesaurus, str, int], Action]] = None,
) -> None:
    """
    Do a breadth-first search over UMLS, hunting for definitions.

    Neighbors are determined by `get_neighbors`, which defaults to :py:func: umlsrat.lookup.umls.get_broader_concepts

    Resulting umlsrat.lookup.graph_fn.Action of `pre_visit` and `post_visit` allow additional
    control of the search. By default, these do nothing.


    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param visit: applied to each visited concept
    :param get_neighbors: get neighbors for a given CUI.
    :param pre_visit: applied before visiting a concept. default: do nothing
    :param post_visit: applied after visiting a concept. default: do nothing
    """
    assert api
    assert start_cui

    if pre_visit is None:
        pre_visit = _pre_visit_passthrough

    if post_visit is None:
        post_visit = _post_visit_passthrough

    to_visit = UniqueFIFO([start_cui])
    distances = FIFO([0])

    visited = UniqueFIFO()

    while to_visit:
        current_cui = to_visit.peek()
        current_dist = distances.peek()

        logger.info(
            f"{len(visited)} '{current_cui}' "
            f"curDistance = {current_dist} "
            f"numToVisit = {len(to_visit)} "
        )

        pre_visit_action = pre_visit(api, current_cui, current_dist)
        if pre_visit_action == Action.STOP:
            break

        if pre_visit_action != Action.SKIP:
            visit(api, current_cui, current_dist)

        ## Mark as visited
        visited.push(to_visit.pop())
        distances.pop()

        if pre_visit_action == Action.SKIP:
            continue

        post_visit_action = post_visit(api, current_cui, current_dist)

        if post_visit_action == Action.STOP:
            break

        if post_visit_action == Action.SKIP:
            continue

        ## Find neighbors and add to_visit
        # print(f"neighbor cuis: {list(get_neighbors(api, current_cui))}")
        # print()
        for cui in get_neighbors(api, current_cui):
            # remove those we have visited or plan to visit already
            if cui in visited or cui in to_visit:
                continue
            to_visit.push(cui)
            distances.push(current_dist + 1)

    return
