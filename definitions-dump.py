import argparse
import json
import logging
import os
import sys

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.definitions import find_defined_concepts, pretty_print_defs
from umlsrat.vocabularies.vocab_info import available_languages, available_vocabs

logger = logging.getLogger(os.path.basename(__file__))


def main():
    parser = argparse.ArgumentParser()

    source_group = parser.add_argument_group("Source")
    source_group.add_argument(
        "--source-code", help="Find definitions for this code.", type=str, default=None
    )
    source_group.add_argument(
        "--source-vocab",
        help="The code can be found in this vocabulary",
        type=str,
        default="SNOMEDCT_US",
        choices=available_vocabs(),
    )
    source_group.add_argument(
        "--source-desc",
        help="A description of the source code.",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--min-concepts",
        help="Stop searching after this many defined concepts. " "0 = infinity",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--target-language",
        help="Target language for definitions.",
        type=str,
        default="ENG",
        choices=available_languages(),
    )

    parser.add_argument(
        "--out-dir",
        help="Write output to this directory.",
        type=str,
        default="definitions",
    )

    # parser.add_argument("--version", type=str, help="UMLS version to use", default='2021AB')
    parser.add_argument("--no-cache", help="Do not use the cache", action="store_true")
    parser.add_argument("--api-key", type=str, help="API key", required=True)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus(args.api_key, use_cache=not args.no_cache)

    source_code = args.source_code
    source_vocab = args.source_vocab
    source_desc = args.source_desc

    min_concepts = args.min_concepts
    target_language = args.target_language

    definitions = find_defined_concepts(
        api=api,
        source_vocab=source_vocab,
        source_code=source_code,
        source_desc=source_desc,
        min_concepts=min_concepts,
        target_lang=target_language,
    )

    logger.info("Definitions:\n\n" + pretty_print_defs(definitions))

    out_dir = args.out_dir
    out_dir = os.path.join(out_dir, target_language)

    if source_code:
        out_file = f"{source_vocab}-{source_code}.json"
    else:
        out_file = f"{source_desc}.json"

    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, out_file), "w", encoding="utf-8") as ofp:
        json.dump(definitions, ofp, indent=2)


if __name__ == "__main__":
    sys.exit(main())
