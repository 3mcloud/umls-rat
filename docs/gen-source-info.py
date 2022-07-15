"""
See https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf for basic UMLS license aggreement.
"""
import argparse
import itertools
import logging
import os
import sys
from typing import Iterable, Dict, List

from umlsrat.api.metathesaurus import MetaThesaurus

logger = logging.getLogger(os.path.basename(__file__))


def get_language(obj: Dict):
    return obj.get("language").get("expandedForm")


def group_by_language(iterable: Iterable[Dict]):
    """You need to sort before grouping in most cases."""

    def group_gen():
        for lang, group in itertools.groupby(
            sorted(iterable, key=get_language), key=get_language
        ):
            # entries are sorted by abbreviation
            yield lang, sorted(group, key=lambda _: _["abbreviation"])

    return sorted(group_gen(), key=lambda kv: -len(kv[1]))


def to_rst_table(iterable: Iterable[Dict], title: str) -> str:
    """ """

    rst_string = (
        f".. list-table:: {title}\n" "    :widths: auto\n" "    :header-rows: 1\n" "\n"
    )

    rows = []

    def writerow(items: List):
        row = f"    * - {items.pop(0)}\n"
        row += "\n".join(f"      - {_}" for _ in items)
        rows.append(row)

    writerow(["Abbreviation", "Preferred Name"])

    for info in iterable:
        writerow(
            [
                info["abbreviation"],
                # get_language(info),
                info["preferredName"],
                # info["restrictionLevel"],
            ]
        )

    return rst_string + "\n".join(rows)


def main():
    parser = argparse.ArgumentParser()

    MetaThesaurus.add_args(parser)

    parser.add_argument(
        "--out-file",
        help="Write RST output to this file.",
        type=str,
        default="source-info.rst",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus.from_namespace(args)
    out_file = args.out_file

    rst_string = (
        "***********\n"
        "Source Info\n"
        "***********\n"
        f"Information regarding the sources contained in UMLS Metathesaurus® version {api.umls_version}. \n"
        f"\n"
        f"* `Basic UMLS License Agreement <https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf>`_\n"
        f"* `Vocabulary Documentation <https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html>`_\n"
        "\n"
    )

    for title, group in group_by_language(api.source_metadata_index.values()):
        rst_string += f"\n{title}\n"
        rst_string += "=" * len(title) + "\n\n"
        rst_string += to_rst_table(group, title=title) + "\n\n"

    with open(out_file, "w", encoding="utf-8") as ofp:
        print(rst_string, file=ofp)


if __name__ == "__main__":
    sys.exit(main())
