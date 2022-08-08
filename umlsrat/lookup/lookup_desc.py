from typing import List, Callable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls
from umlsrat.util import text
from umlsrat.util.orderedset import UniqueFIFO


def _get_norm_fn(normalize: bool) -> Callable[[str], str]:
    if normalize:
        return text.normalize
    else:

        return text.identity


def _append_cui_descriptions(
    api: MetaThesaurus,
    cui: str,
    syn_names: UniqueFIFO,
    txt_norm: Callable[[str], str],
    sabs: str,
) -> List[str]:
    def push_name(name: str) -> None:
        syn_names.push(txt_norm(name))

    for atom in api.get_atoms_for_cui(cui, sabs=sabs):
        push_name(atom.get("name"))

    return syn_names.items


def get_synonyms(
    api: MetaThesaurus,
    cui: str,
    language: str = "ENG",
    normalize: bool = False,
) -> List[str]:
    """
    Find unique, synonymous concept names. Uniqueness is determined by
    case-insensitive exact string match or by the normalized form if ``normalize=True``.

    >>> from umlsrat.api.metathesaurus import MetaThesaurus
    >>> from umlsrat.lookup.lookup_desc import get_synonyms
    >>> get_synonyms(MetaThesaurus(), "C0034500")

    .. code-block:: js

            [
                "Raccoon",
                "Raccoons",
                "Procyons",
                "Procyon",
                "Genus Procyon",
                "Genus Procyon (organism)",
            ]

    :param api: MetaThesaurus
    :param cui: CUI
    :param language: target language
    :param normalize: normalize names
    :return: list of names for this concept
    """
    # get source vocab abbreviations for language
    sabs = api.get_sabs_str(language)
    # create name queue
    syn_names = UniqueFIFO(keyfn=str.lower)
    # get text norm function
    txt_norm = _get_norm_fn(normalize)
    _append_cui_descriptions(
        api=api, cui=cui, syn_names=syn_names, txt_norm=txt_norm, sabs=sabs
    )
    return syn_names.items


def find_synonyms(
    api: MetaThesaurus,
    source_vocab: str,
    concept_id: str,
    language: str = "ENG",
    normalize: bool = False,
) -> List[str]:
    """
    Find unique, synonymous concept names given a source concept. Uniqueness is determined by
    case-insensitive exact string match or by the normalized form if ``normalize=True``.

    >>> from umlsrat.api.metathesaurus import MetaThesaurus
    >>> from umlsrat.lookup.lookup_desc import find_synonyms
    >>> find_synonyms(MetaThesaurus(), "ICD10CM", "T87.44")

    .. code-block:: js

        [
          "Infection of amputation stump, left lower extremity",
          "infection of amputation stump of left lower extremity",
          "infection of amputation stump of left lower extremity (diagnosis)",
          "Infection of amputation stump of left lower limb",
          "Infection of amputation stump of left leg",
          "Infection of amputation stump of left lower limb (disorder)"
        ]

    With normalization.

    >>> find_synonyms(MetaThesaurus(), "ICD10CM", "T87.44", normalize=True)

    .. code-block:: js

        [
          "infection of amputation stump left lower extremity",
          "infection of amputation stump of left lower extremity",
          "infection of amputation stump of left lower limb",
          "infection of amputation stump of left leg"
        ]

    :param api: MetaThesaurus
    :param source_vocab: source vocabulary e.g. ICD10CM
    :param concept_id: concept ID in the source vocab
    :param language: target language
    :param normalize: normalize names
    :return: list of names for this concept
    """
    # get source vocab abbreviations for language
    sabs = api.get_sabs_str(language)
    # create name queue
    syn_names = UniqueFIFO(keyfn=str.lower)
    # get text norm function
    txt_norm = _get_norm_fn(normalize)

    base_concept = api.get_source_concept(source_vocab, concept_id)
    if not base_concept:
        raise ValueError(f"Source concept not found {source_vocab}/{concept_id}")

    if source_vocab in sabs.split(","):
        # The name of the base concept always comes first -- provided that it is a vocab associated
        # with the desired language.
        syn_names.push(txt_norm(base_concept.get("name")))

    for cui in lookup_umls.get_cuis_for(api, source_vocab, concept_id):
        _append_cui_descriptions(
            api=api,
            cui=cui,
            txt_norm=txt_norm,
            syn_names=syn_names,
            sabs=sabs,
        )

    return syn_names.items
