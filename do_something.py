import argparse
import json
import sys

from umlst.lookup import Lookup


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--api-key', type=str, help="API key",
                      default='cf4e9f8f-a40c-4225-94e9-24ca9282b887')
  args = parser.parse_args()

  # search = Search(args.api_key)
  # res = search.find("back")

  lu = Lookup(args.api_key)

  xxx = {
    'old back': lu.find('450807008'),
    'bite': lu.find('782161000'),
  }

  print(json.dumps(xxx, indent=2))

  pass


if __name__ == '__main__':
  sys.exit(main())
