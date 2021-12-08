import argparse
import json
import logging
import os
import sys

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.definitions import find_definitions, definitions_to_string
from umlsrat.vocab_info import available_languages, available_vocabs

logger = logging.getLogger(os.path.basename(__file__))


def main():
    parser = argparse.ArgumentParser()

    source_group = parser.add_argument_group("Source")
    source_group.add_argument('--source-code',
                              help='Find definitions for this code.',
                              type=str, default=None)
    source_group.add_argument('--source-vocab', help='The code can be found in this vocabulary',
                              type=str, default='SNOMEDCT_US', choices=available_vocabs())
    source_group.add_argument('--source-desc', help='A description of the source code.',
                              type=str, default=None)

    parser.add_argument('--min-num-defs', help='Stop searching after this many definitions. '
                                           '0 = infinity',
                        type=int, default=2)
    parser.add_argument('--target-language', help='Target language for definitions.',
                        type=str, default='ENG', choices=available_languages())

    parser.add_argument('--out-dir', help='Write output to this directory.',
                        type=str, default='definitions')

    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus(args.api_key)

    source_code = args.source_code
    source_vocab = args.source_vocab
    source_desc = args.source_desc

    min_num_defs = args.min_num_defs
    target_language = args.target_language

    definitions = find_definitions(
        api=api,
        source_vocab=source_vocab,
        source_code=source_code,
        source_desc=source_desc,
        min_num_defs=min_num_defs,
        target_lang=target_language
    )

    logger.info("Definitions:\n" + definitions_to_string(definitions))

    out_dir = args.out_dir
    out_dir = os.path.join(out_dir, target_language)

    if source_code:
        out_file = f"{source_vocab}-{source_code}.json"
    else:
        out_file = f"{source_desc}.json"

    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, out_file), 'w', encoding='utf-8') as ofp:
        json.dump(definitions, ofp, indent=2)


if __name__ == '__main__':
    sys.exit(main())
