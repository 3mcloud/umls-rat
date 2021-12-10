import argparse
import re
import sys

import pandas as pd
import requests


def fix_html(text: str) -> str:
    return re.sub(r"<table.+?>", "<table>", text)


def main(args: argparse.Namespace):
    out_file = args.out_file

    resp = requests.get(args.url, verify=False)
    assert resp.status_code == 200

    contents = fix_html(resp.text)

    dfs = pd.read_html(contents)
    assert len(dfs) == 1
    df = dfs.pop()

    print(df)

    df.to_csv(out_file, index=False)

    df = pd.read_csv(out_file)
    print(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        help="",
        type=str,
        default="https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html",
    )
    parser.add_argument(
        "-o", "--out-file", help="", type=str, default="vocabularies.csv"
    )
    args = parser.parse_args()

    sys.exit(main(args))
