"""
See https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf for basic UMLS license aggreement.
"""
import argparse
import itertools
import logging
import os
import sys
from typing import Iterable, Callable, Dict, List

from umlsrat.api.metathesaurus import MetaThesaurus

logger = logging.getLogger(os.path.basename(__file__))


def my_group_by(iterable: Iterable, key: Callable):
    """You need to sort before grouping in most cases."""
    for key_val, group in itertools.groupby(sorted(iterable, key=key), key=key):
        yield key_val, list(group)


def get_language(obj):
    return obj.get("language").get("expandedForm")


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
        f"Information regarding the sources contained in UMLS Metathesaurus® version {api.umls_version}. "
        f"`Basic UMLS License Agreement <https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf>`_\n"
        "\n"
    )

    lang_groups = my_group_by(api.source_metadata_index.values(), key=get_language)
    lang_groups = sorted(lang_groups, key=lambda kv: -len(kv[1]))
    for title, group in lang_groups:
        rst_string += f"\n{title}\n"
        rst_string += "=" * len(title) + "\n\n"
        rst_string += to_rst_table(group, title=title) + "\n\n"

    with open(out_file, "w", encoding="utf-8") as ofp:
        print(rst_string, file=ofp)


if __name__ == "__main__":
    sys.exit(main())
