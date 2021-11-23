import argparse
import json
import sys

from umlst.lookup import Lookup
from umlst.util import Result


def find_definitions(result: Result):
    definitions = result['definitions']
    if definitions:
        return definitions

    dpa = result['defaultPreferredAtom']
    if dpa:
        c = dpa['concept']
        print(dpa)
        pass

    concepts = result['concepts']
    if concepts:
        for c in concepts:
            return find_definitions(c['uri'])
            print(resolved)
            pass
        pass
    # now what?

    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()

    # search = Search(args.api_key)
    # res = search.find("back")

    lu = Lookup(args.api_key)

    stuff = {
        'old back': lu.find('450807008'),
        'bite': lu.find('782161000'),
    }

    print(stuff)

    xxx = find_definitions(stuff['bite'])

    pass


if __name__ == '__main__':
    sys.exit(main())
