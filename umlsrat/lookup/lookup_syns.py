from typing import List

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls
from umlsrat.util import text
from umlsrat.util.orderedset import UniqueFIFO


def find_synonyms(
    api: MetaThesaurus,
    source_vocab: str,
    source_ui: str,
    language: str = "ENG",
    normalize: bool = False,
) -> List[str]:
    """
    Find unique, synonymous concept names. Uniqueness is determined by case-insensitive exact
    string match or by the normalized form if ``normalize=True``.

    :param api: MetaThesaurus
    :param source_vocab: source vocabulary e.g. ICD10CM
    :param source_ui: concept ID in the source vocab
    :param language: target language
    :param normalize: normalize names
    :return: list of names for this concept
    """
    source_vocab = api.validate_source_abbrev(source_vocab)

    base_concept = api.get_source_concept(source_vocab, source_ui)
    if not base_concept:
        raise ValueError(f"Source concept not found {source_vocab}/{source_ui}")

    language = api.validate_language_abbrev(language)
    lang_sabs = set(api.sources_for_language(language))
    lang_sabs_str = ",".join(lang_sabs)

    if normalize:
        syn_names = UniqueFIFO()
        do_norm = text.normalize

    else:
        syn_names = UniqueFIFO(keyfn=str.lower)

        def do_norm(name: str) -> str:
            return name

    def push_name(name: str) -> str:
        syn_names.push(do_norm(name))

    if source_vocab in lang_sabs:
        # The name of the base concept always comes first -- provided that it is a vocab associated
        # with the desired language.
        push_name(base_concept.get("name"))

    for cui in lookup_umls.get_cuis_for(api, source_vocab, source_ui):
        for rel in api.get_relations(
            cui=cui, includeRelationLabels="SY", sabs=lang_sabs_str
        ):
            rel_atom = api.session.get_single_result(rel.get("relatedId"))
            if rel_atom.get("rootSource") not in lang_sabs:
                continue

            if "atoms" in rel_atom:
                # add the name of the cluster
                push_name(rel_atom.get("name"))

                # get the atoms in the cluster
                sub_atoms_url = rel_atom.get("atoms")
                sub_atoms = api.session.get_results(sub_atoms_url)
                # sort by UI for consistent order which apparently isn't maintained by the call?
                # sub_atoms = sorted(sub_atoms, key=lambda _:_.get("ui"))
                for a in sub_atoms:
                    push_name(a.get("name"))
            else:
                push_name(rel_atom.get("name"))

    return syn_names.items
