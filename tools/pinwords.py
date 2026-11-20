# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The words of a pin's verdict and pool key are plugin-hostd-protocol's, not plugin-db's: its domain `pin`
(<contract directory>/pin/pin.json, the package plugin-hostd-protocol-contract 0.8.0), items PIN_VERDICTS and PIN_POOLS.
The renders read them there. load() is data/pin.json and data/db.json as the renders have always read them, the two items of
the domain in place of the words that file no longer holds, each as a words item (key: its title, word: its const, doc:
its description, in the order of its codes).

The contract directory is $PIN_DOMAIN_DIR, else the installed one (pkg-config omx-contract, contractdir)."""
import json
import os
import subprocess
import sys

ITEMS = ("PIN_VERDICTS", "PIN_POOLS")
# the item of plugin-db's own file each of them replaces: the place it keeps in the order of the renders
REPLACES = {"PLUGIN_DB_PIN_VERDICTS": "PIN_VERDICTS", "PLUGIN_DB_PIN_POOLS": "PIN_POOLS"}


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
                 "plugin-hostd-protocol-contract 0.8.0 or later, or set PIN_DOMAIN_DIR to a contract directory holding pin/pin.json")
    schemas = doc["components"]["schemas"]
    out = {}
    for item in ITEMS:
        if item not in schemas:
            sys.exit(f"pinwords: {path} has no item {item}")
        words = sorted(schemas[item]["oneOf"], key=lambda w: w["x-code"])
        out[item] = {"kind": "words", "doc": schemas[item]["description"],
                     "words": {w["title"]: {"word": w["const"], "doc": w.get("description", "")} for w in words}}
    return out


def load(data_dir):
    """the items of data/pin.json and data/db.json in the renders' order, the domain's words in the place of the old two"""
    new = domain_items()
    db = {}
    for name in ("pin.json", "db.json"):
        for item, body in json.load(open(f"{data_dir}/{name}")).items():
            if item in REPLACES:
                db[REPLACES[item]] = new[REPLACES[item]]
            else:
                db[item] = body
    for item in ITEMS:
        db.setdefault(item, new[item])
    return db
