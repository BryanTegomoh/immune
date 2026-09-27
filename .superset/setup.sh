#!/usr/bin/env bash
set -euo pipefail
python3 -c 'import sys; assert sys.version_info >= (3,12), "IMMUNE provider clients require Python 3.12+"'
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
