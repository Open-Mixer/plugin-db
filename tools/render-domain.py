#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Derive contract.d/plugin-db/plugin-db.json, plugin-db's domain document, from data/db.json.

data/db.json stays the one source of the words. The domain document carries the items listed in ITEMS (today the
address formats, which the qualification store checks against plugin-db's own list), each as the domain format wants
it: the item's doc is its description, each word is a oneOf entry (the word as const, its key as title, its place as
x-code, its doc as description). Nothing here is typed twice.

    render-domain.py [--check] <data dir> <out file>
"""
import json
import sys

ITEMS = ("PLUGIN_DB_ADDRESS_FORMATS",)


def render(data_dir):
    db = json.load(open(f"{data_dir}/db.json"))
    schemas = {}
    for item in ITEMS:
        body = db[item]
        if body.get("kind") != "words":
            sys.exit(f"render-domain.py: {item} is no words item")
        one_of = []
        for code, (key, w) in enumerate(body["words"].items()):
            one_of.append({"const": w["word"], "title": key, "description": w["doc"], "x-code": code})
        schemas[item] = {"description": body["doc"], "x-since": body["since"], "oneOf": one_of}
    doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://openmixer.org/contract/plugin-db",
        "info": {
            "title": "The words of the plugin database",
            "version": "1.0.0",
            "x-owner": "plugin-db",
            "x-stability": "experimental",
        },
        "components": {"schemas": schemas},
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv):
    check = argv[:1] == ["--check"]
    args = argv[1:] if check else argv
    if len(args) != 2:
        sys.exit(__doc__)
    text = render(args[0])
    if check:
        try:
            have = open(args[1]).read()
        except OSError as e:
            sys.exit(f"render-domain.py: {args[1]}: {e.strerror}: run make render-domain")
        if have != text:
            sys.exit(f"render-domain.py: {args[1]} is not what data/db.json renders: run make render-domain")
        return
    with open(args[1], "w") as f:
        f.write(text)


main(sys.argv[1:])
