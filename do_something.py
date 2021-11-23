import argparse
import sys

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

    clu = ConceptLookup(args.api_key)

    stuff = {
        # 'old back': '450807008',
        'bite': '782161000',
        'depression': '35489007',
    }

    dlu = DefinitionsLookup(clu)

    def printem(k, v):
        ds = dlu.find(v)
        print(f"*****   {k}   *****")
        for x, d in enumerate(ds):
            print(f"({x + 1}) {d}")

    for k, v in stuff.items():
        printem(k, v)
    #
    # bite_defs = dlu.find('782161000')
    # print(f"bite defs = {bite_defs}")
    #
    # depression_defs = dlu.find('35489007')
    # print(f"depression defs = {depression_defs}")
    pass


if __name__ == '__main__':
    sys.exit(main())
