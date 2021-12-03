import argparse
import json
import logging
import os
import sys

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.definitions import definitions_bfs
from umlsrat.lookup.umls import find_umls
from umlsrat.vocab_info import validate_vocab_abbrev


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--code', help='Find definitions for this code.', type=str, required=True)
    parser.add_argument('--vocab', help='The code can be found in this vocabulary',
                        default='SNOMEDCT_US')

    parser.add_argument('--num-defs', help='Stop searching after this many definitions. '
                                           '0 = infinity',
                        type=int, default=0)
    parser.add_argument('--target-vocabs', help='Comma-separated list of vocab abbreviations',
                        default=None)

    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus(args.api_key)

    code = args.code
    vocab_name = args.vocab
    num_defs = args.num_defs
    target_vocabs = args.target_vocabs

    if target_vocabs:
        target_vocabs = [validate_vocab_abbrev(_) for _ in target_vocabs.split(',')]

    cui = find_umls(api, vocab_name, code)
    definitions = definitions_bfs(api,
                                  start_cui=cui,
                                  num_defs=num_defs,
                                  target_vocabs=target_vocabs)

    os.makedirs(vocab_name, exist_ok=True)
    with open(os.path.join(vocab_name, f'{code}.json'), 'w', encoding='utf-8') as ofp:
        json.dump(definitions, ofp, indent=2)


if __name__ == '__main__':
    sys.exit(main())
