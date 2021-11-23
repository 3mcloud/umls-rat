import argparse
import sys

from umlst.auth import Authenticator
from umlst.lookup import ConceptLookup, DefinitionsLookup


# def xxxxxxxxx(result: Result):
#     definitions = result['definitions']
#     if definitions:
#         return definitions
#
#     class_type = result['classType']
#     if class_type is None or 'Concept' == class_type:
#         cui = result['ui']
#         r = result.get_result(
#             f'https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions')
#         assert r
#         return find_definitions(r.pop())
#     elif 'SourceAtomCluster' == class_type:
#         print(result)
#         concept = result['concept']
#         if concept:
#             concept = concept.pop()
#             find_definitions(concept)
#
#         concepts = result['concepts']
#         if concepts:
#             concept = concepts.pop()
#             find_definitions(concept)
#         pass
#
#     print(result)
#     pass
#     # dpa = result['defaultPreferredAtom']
#     # if dpa:
#     #     dpa = dpa.pop()
#     #     c = dpa['concept']
#     #     c = c.pop() if c is not None else None
#     #
#     #     print(dpa)
#     #
#     # concepts = result['concepts']
#     # if concepts:
#     #     for c in concepts:
#     #         return find_definitions(c['uri'])
#     #         print(resolved)
#     #
#     # # now what?
#
#     pass
#
#


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
        # 'old back': '450807008',
        'bite': '782161000',
        'depression': '35489007',
    }

    dlu = DefinitionsLookup(auth)

    with open('cheese.txt', 'w', encoding='utf-8') as ofp:
        def printem(k, v):
            ds = dlu.find(v)
            print(f"*****   {k}   *****", file=ofp)
            for x, d in enumerate(ds):
                print(f"({x + 1}) {d}", file=ofp)

        for k, v in stuff.items():
            printem(k, v)


if __name__ == '__main__':
    sys.exit(main())
