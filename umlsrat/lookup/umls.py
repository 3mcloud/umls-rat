import logging
import os.path
from typing import Optional

from umlsrat.api.metathesaurus import MetaThesaurus, Result

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

    # if we didn't find a UMLS concept directly, there should be a SY relation
    relations = result['relations']
    sy_rels = [_ for _ in relations if _['relationLabel'] == 'SY']
    if not sy_rels:
        raise ValueError(f"No parents or SY relations for:\n{result}")

    for rel in sy_rels:
        rel_res = rel['relatedId']
        assert len(rel_res) == 1
        return _get_umls_concept(rel_res[0])

    raise ValueError(f"Impossible to find UMLS concept for:\n{result}")


def find_umls(api: MetaThesaurus, source_vocab: str, concept_id: str) -> str:
    """
    Get the UMLS CUI for a concept from a source vocabulary.
    """
    # uri = f"https://uts-ws.nlm.nih.gov/rest/search/current"
    # add_params = (
    #     KeyValuePair('string', concept_id),
    #     KeyValuePair('sabs', source_vocab),
    #     KeyValuePair('inputType', 'code'),
    #     KeyValuePair('searchType', 'exact'),
    #     KeyValuePair('includeObsolete', 'true'),
    #     KeyValuePair('includeSuppressible', 'true'),
    # )
    # search_res = api.get_single_result(uri, add_params)
    # concept_res = search_res['uri'].pop()
    # return concept_res
    source_res = api.get_source_concept(source_vocab, concept_id)
    assert source_res

    concept_res = _find_umls(source_res)
    return concept_res['ui']
