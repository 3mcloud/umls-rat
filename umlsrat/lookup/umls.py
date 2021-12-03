import logging
import os.path
from typing import Optional

from umlsrat.api.metathesaurus import MetaThesaurus, Result
from umlsrat.util import misc

logger = logging.getLogger(os.path.basename(__file__))


def _get_umls_concept(result: Result) -> Optional[Result]:
    for c_field in ('concept', 'concepts'):
        concept_res = result[c_field]
        if not concept_res: continue
        for c in concept_res:
            # check for valid UI
            if c['ui']:
                return c


def _find_umls(result: Result) -> Result:
    umls = _get_umls_concept(result)
    if umls: return umls

    # if we didn't find a UMLS concept directly, check 'SY' then 'RO' relations
    relations = result['relations']
    grouped = misc.group_data(relations, lambda _: _['relationLabel'])

    for rel_type in ('SY', 'RO',):
        rels = grouped.get(rel_type)
        if not rels:
            logger.info(f"'{result['ui']}' has no '{rel_type}' relations")
            continue

        for rel in rels:
            rel_res = rel['relatedId']
            assert len(rel_res) == 1
            rel_concept = rel_res.pop()
            return _get_umls_concept(rel_concept)

    raise ValueError(f"Impossible to find UMLS concept for:\n{result}")


def find_umls(api: MetaThesaurus, source_vocab: str, concept_id: str) -> Optional[str]:
    """
    Get the UMLS CUI for a concept from a source vocabulary.
    """
    source_res = api.get_source_concept(source_vocab, concept_id)
    if not source_res:
        logger.info(f"Concept not found: {source_vocab}/{concept_id}")
        return None

    concept_res = _find_umls(source_res)
    return concept_res['ui']
