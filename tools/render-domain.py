#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Derive contract.d/plugin-db/plugin-db.json, plugin-db's domain document, from data/db.json.

data/db.json stays the one source of the words. The domain document carries the items listed in ITEMS (today the
address formats, which the qualification store checks against plugin-db's own list), each as the domain format wants
it: the item's doc is its description, each word is a oneOf entry (the word as const, its key as title, its place as
x-code, its doc as description). Nothing here is typed twice.

The domain's version is plugin-db's VERSION (data/ has no field for it, and omx-contract's schema takes none): a reader
floors on it. The document is append-only under one version, and the render refuses by name to replace the file with
one that adds or removes a word while the version is unchanged, or that moves the x-code of a word the file already
has (a new word is appended, after the existing ones). --check applies the same refusals before it compares.

    render-domain.py [--check] <data dir> <VERSION file> <out file>
"""
import json
import sys

ITEMS = ("PLUGIN_DB_ADDRESS_FORMATS",)


def render(data_dir, version):
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
            "version": version,
            "x-owner": "plugin-db",
            "x-stability": "experimental",
        },
        "components": {"schemas": schemas},
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def words_of(doc):
    return {i: {w["const"]: w["x-code"] for w in b["oneOf"]} for i, b in doc["components"]["schemas"].items()}


def refusals(old, new):
    """what a document that replaces `old` must not do, each by item and word"""
    out = []
    ow, nw = words_of(old), words_of(new)
    if old["info"]["version"] == new["info"]["version"]:
        for item in sorted(set(ow) | set(nw)):
            added = sorted(set(nw.get(item, {})) - set(ow.get(item, {})))
            removed = sorted(set(ow.get(item, {})) - set(nw.get(item, {})))
            if added or removed:
                out.append(f"{item}: words added or removed while the version is unchanged ({new['info']['version']}): "
                           f"added {added}, removed {removed}: bump VERSION")
    for item in sorted(set(ow) & set(nw)):
        for word in sorted(set(ow[item]) & set(nw[item])):
            if ow[item][word] != nw[item][word]:
                out.append(f"{item}: x-code moved: {word} was {ow[item][word]}, is {nw[item][word]}: "
                           "a new word is appended after the existing ones")
    return out


def main(argv):
    check = argv[:1] == ["--check"]
    args = argv[1:] if check else argv
    if len(args) != 3:
        sys.exit(__doc__)
    data_dir, version_file, out = args
    version = open(version_file).read().strip()
    text = render(data_dir, version)
    try:
        have = open(out).read()
    except OSError as e:
        if check:
            sys.exit(f"render-domain.py: {out}: {e.strerror}: run make render-domain")
        have = None
    if have is not None:
        try:
            problems = refusals(json.loads(have), json.loads(text))
        except (ValueError, KeyError, TypeError):
            problems = []  # a file that is no document of this shape is only stale
        if problems:
            sys.exit("".join(f"render-domain.py: {out}: {m}\n" for m in problems).rstrip("\n"))
    if check:
        if have != text:
            sys.exit(f"render-domain.py: {out} is not what data/db.json and VERSION render: run make render-domain")
        return
    with open(out, "w") as f:
        f.write(text)


main(sys.argv[1:])
