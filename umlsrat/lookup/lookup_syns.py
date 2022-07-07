from typing import List

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls
from umlsrat.util.orderedset import UniqueFIFO


def find_synonyms(
    api: MetaThesaurus, source_vocab: str, source_ui: str, language: str = "ENG"
) -> List[str]:
    """
    Find synonymous concept names.

    :param api: MetaThesaurus
    :param source_vocab: source vocabulary e.g. ICD10CM
    :param source_ui: concept ID in the source vocab
    :param language: target language
    :return: list of names for this concept
    """
    source_vocab = api.validate_source_abbrev(source_vocab)

    concept = api.get_source_concept(source_vocab, source_ui)
    if not concept:
        raise ValueError(f"Source concept not found {source_vocab}/{source_ui}")

    language = api.validate_language_abbrev(language)
    lang_sabs = api.sources_for_language(language)
    lang_sabs_str = ",".join(lang_sabs)

    syn_names = UniqueFIFO(keyfn=str.upper)

    if source_vocab in lang_sabs:
        syn_names.push(concept.get("name"))

    for cui in lookup_umls.get_cuis_for(api, source_vocab, source_ui):
        for rel in api.get_relations(
            cui=cui, includeRelationLabels="SY", sabs=lang_sabs_str
        ):
            syn_names.push(rel.get("relatedIdName"))

    return syn_names.items
