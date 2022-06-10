#!/usr/bin/env bash

DOCS_DIR=$(dirname $0)
make -C "${DOCS_DIR}" clean html SPHINXOPTS="-W --keep-going"
