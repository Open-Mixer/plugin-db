#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Refuse an item that data/ (the package plugin-db) and a domain document of contract.d both declare.

omx-contract's reader refuses one item name in two owners, except when the domain has the name of an installed package:
it then skips the domain without a word. The domain here is called plugin-db, as the package is, so this repository
holds the rule itself: an item is declared once, and the domain document is its only declaration. The check belongs in
omx-contract's reader, which refuses a duplicate item in every other case (Open-Mixer/omx-contract#125); this file goes
when the reader says so for a domain named like a package.

    one-source.py <data dir> <contract.d>
"""
import glob
import json
import re
import sys


def main(data_dir, contract_d):
    seen = {}
    for path in sorted(glob.glob(f"{data_dir}/*.json")):
        doc = json.load(open(path))
        for name in doc if isinstance(doc, dict) else ():
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
                seen.setdefault(name, []).append(path)
    for path in sorted(glob.glob(f"{contract_d}/**/*.json", recursive=True)):
        if "/catalogs/" in path:
            continue
        for name in json.load(open(path)).get("components", {}).get("schemas", {}):
            seen.setdefault(name, []).append(path)
    both = {n: p for n, p in seen.items() if len(p) > 1}
    for name, paths in sorted(both.items()):
        print(f"one-source.py: {name} is declared by {' and '.join(paths)}: one item, one declaration", file=sys.stderr)
    return 1 if both else 0


sys.exit(main(*sys.argv[1:]) if len(sys.argv) == 3 else sys.exit(__doc__))
