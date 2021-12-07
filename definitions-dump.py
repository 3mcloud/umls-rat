import argparse
import json
import logging
import os
import sys

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.definitions import find_definitions
from umlsrat.vocab_info import available_languages, available_vocabs


def main():
    parser = argparse.ArgumentParser()

    source_group = parser.add_argument_group("Source")
    source_group.add_argument('--source-code',
                              help='Find definitions for this code.',
                              type=str, required=True)
    source_group.add_argument('--source-vocab', help='The code can be found in this vocabulary',
                              type=str, default='SNOMEDCT_US', choices=available_vocabs())
    # source_group.add_argument('--source-desc', help='A description of the source code.',
    #                           type=str, default=None)

    parser.add_argument('--num-defs', help='Stop searching after this many definitions. '
                                           '0 = infinity',
                        type=int, default=0)
    parser.add_argument('--target-language', help='Target language for definitions.',
                        default='ENG', choices=available_languages())

    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus(args.api_key)

    source_code = args.source_code
    source_vocab = args.source_vocab

    num_defs = args.num_defs
    target_language = args.target_language

    definitions = find_definitions(
        api=api,
        source_vocab=source_vocab,
        source_code=source_code,
        num_defs=num_defs,
        target_lang=target_language
    )

    os.makedirs(source_vocab, exist_ok=True)
    with open(os.path.join(source_vocab, f'{source_code}.json'), 'w', encoding='utf-8') as ofp:
        json.dump(definitions, ofp, indent=2)


if __name__ == '__main__':
    sys.exit(main())
