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

    base_concept = api.get_source_concept(source_vocab, source_ui)
    if not base_concept:
        raise ValueError(f"Source concept not found {source_vocab}/{source_ui}")

    language = api.validate_language_abbrev(language)
    lang_sabs = set(api.sources_for_language(language))
    lang_sabs_str = ",".join(lang_sabs)

    syn_names = UniqueFIFO(keyfn=str.upper)

    if source_vocab in lang_sabs:
        # The name of the base concept always comes first -- provided that it is a vocab associated
        # with the desired language.
        syn_names.push(base_concept.get("name"))

    for cui in lookup_umls.get_cuis_for(api, source_vocab, source_ui):
        for rel in api.get_relations(
            cui=cui, includeRelationLabels="SY", sabs=lang_sabs_str
        ):
            rel_atom = api.session.get_single_result(rel.get("relatedId"))
            if rel_atom.get("rootSource") not in lang_sabs:
                continue

            if "atoms" in rel_atom:
                for a in api.session.get_results(rel_atom.get("atoms")):
                    syn_names.push(a.get("name"))
            else:
                syn_names.push(rel_atom.get("name"))

    return syn_names.items
