import argparse
import json
import logging
import os
import sys

from umlsrat import lookup
from umlsrat.api import API
from umlsrat.auth import Authenticator
from umlsrat.util import Vocabularies


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--code', help='Find definitions for this code.', type=str, required=True)
    parser.add_argument('--vocabulary', help='The code can be found in this vocabulary',
                        default=Vocabularies.SNOMEDCT)

    parser.add_argument('--num-defs', help='Stop searching after this many definitions. '
                                           '0 = infinity',
                        type=int, default=0)
    parser.add_argument('--target-vocabs', help='Comma-separated list of vocab abbreviations',
                        default=None)

    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = API(Authenticator(args.api_key))

    vocab_name = args.vocabulary
    code = args.code
    num_defs = args.num_defs
    target_vocabs = args.target_vocabs
    # TODO need to validate vocab abbrev somehow
    if target_vocabs:
        target_vocabs = [_.strip().upper() for _ in target_vocabs.split(',')]

    cui = lookup.find_umls(api, vocab_name, code)
    definitions = lookup.definitions_bfs(api,
                                         start_cui=cui,
                                         num_defs=num_defs,
                                         target_vocabs=target_vocabs)

    os.makedirs(vocab_name, exist_ok=True)
    with open(os.path.join(vocab_name, f'{code}.json'), 'w', encoding='utf-8') as ofp:
        json.dump(definitions, ofp, indent=2)


if __name__ == '__main__':
    sys.exit(main())
