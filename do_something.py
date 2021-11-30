import argparse
import sys

from umlst.auth import Authenticator
from umlst.lookup import DefinitionsLookup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', type=str, help="API key",
                        default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
    args = parser.parse_args()

    # search = Search(args.api_key)
    # res = search.find("back")
    auth = Authenticator(args.api_key)
    # clu = ConceptLookup(auth)

    stuff = {
        'old back': '450807008',
        # 'bite': '782161000',
        # 'depression': '35489007',
    }

    dlu = DefinitionsLookup(auth)

    with open('cheese.txt', 'w', encoding='utf-8') as ofp:
        def printem(k, v):
            desc = dlu.find_best(v)
            print(f"*****   {k}   *****", file=ofp)
            print(f"{desc}\n", file=ofp)

            # for x, d in enumerate(desc):
            #     print(f"({x + 1}) {d}", file=ofp)

        for k, v in stuff.items():
            printem(k, v)


if __name__ == '__main__':
    sys.exit(main())
