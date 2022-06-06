import argparse
import json
import logging
import os
import sys

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_defs
from umlsrat.util.iterators import definitions_to_md

logger = logging.getLogger(os.path.basename(__file__))


def main():
    parser = argparse.ArgumentParser()

    parser = MetaThesaurus.add_args(parser)

    parser = lookup_defs.add_args(parser)

    parser.add_argument(
        "--out-dir",
        help="Write output to this directory.",
        type=str,
        default="definitions",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    api = MetaThesaurus.from_namespace(args)
    find_fn = lookup_defs.find_builder(api, args)

    definitions = find_fn()

    markdown = definitions_to_md(definitions)
    logger.info("Definitions:\n\n" + markdown)

    out_dir = args.out_dir
    out_dir = os.path.join(out_dir, args.target_lang)

    if args.source_ui:
        of_base = f"{args.source_ui}-{args.source_ui}"
    else:
        of_base = f"{args.source_desc}"

    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, f"{of_base}.json"), "w", encoding="utf-8") as ofp:
        json.dump(definitions, ofp, indent=2)

    with open(os.path.join(out_dir, f"{of_base}.md"), "w", encoding="utf-8") as ofp:
        print(markdown, file=ofp)


if __name__ == "__main__":
    sys.exit(main())
