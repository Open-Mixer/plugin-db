# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The words of a pin's verdict and pool, its keys and what counts as a changed pin are plugin-hostd-protocol's, not plugin-db's:
its domain `pin` (<contract directory>/pin/pin.json, the package plugin-hostd-protocol-contract), items PIN_VERDICTS and
PIN_POOLS (V12), PIN_KEYS and PIN_CHANGES (plugin-db#34, ruling R5). The renders read them there. load() is the four items
of the domain, each as a words item (key: its title, word: its const,
doc: its description, in the order of its codes), then plugin-db's own items of its domain plugin-db that rebuild pin.json and
db.json (tools/dbwords.py), in that order.

The contract directory is $PIN_DOMAIN_DIR, else the installed one (pkg-config omx-contract, contractdir)."""
import json
import os
import subprocess
import sys

import dbwords

ITEMS = ("PIN_VERDICTS", "PIN_POOLS", "PIN_KEYS", "PIN_CHANGES")


def domain_path():
    d = os.environ.get("PIN_DOMAIN_DIR")
    if not d:
        d = subprocess.run(["pkg-config", "--variable=contractdir", "omx-contract"], capture_output=True, text=True).stdout.strip()
    return os.path.join(d, "pin", "pin.json")


def domain_items():
    path = domain_path()
    try:
        doc = json.load(open(path))
    except (OSError, ValueError) as e:
        sys.exit(f"pinwords: the domain pin of plugin-hostd-protocol is not readable ({path}): {e}; install "
                 "plugin-hostd-protocol-contract, or set PIN_DOMAIN_DIR to a contract directory holding pin/pin.json")
    schemas = doc["components"]["schemas"]
    out = {}
    for item in ITEMS:
        if item not in schemas:
            sys.exit(f"pinwords: {path} has no item {item}")
        words = sorted(schemas[item]["oneOf"], key=lambda w: w["x-code"])
        out[item] = {"kind": "words", "doc": schemas[item]["description"],
                     "words": {w["title"]: {"word": w["const"], "doc": w.get("description", "")} for w in words}}
    return out


def load(data_dir=None):
    """the domain's four items first, then plugin-db's items of pin.json and db.json, in the renders' order (data_dir,
    which held them, is no longer read)"""
    db = dict(domain_items())
    for name in ("pin.json", "db.json"):
        db.update(dbwords.items(name))
    return db
