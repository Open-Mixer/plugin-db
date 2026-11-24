# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""plugin-db's words and numbers are its domain plugin-db (contract.d/plugin-db/plugin-db.json): the items that carry an
x-file, read in the data form `omx-contract render --with-domain` rebuilds from them (docs/render.md of omx-contract), so
the renders read what omx-contract's C render reads. files() is {<x-file>: {<item>: <data item>}}, the items of each file
in the document's order; items(<x-file>) is one file's.

The document is $PLUGIN_DB_DOMAIN (a path to a plugin-db.json), else the tree's own."""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def domain_path():
    return os.environ.get("PLUGIN_DB_DOMAIN") or os.path.join(ROOT, "contract.d", "plugin-db", "plugin-db.json")


def data_item(s):
    """one domain item as its data item: kind, since, doc, why, then groups and words, or unit and value"""
    item = {"kind": s.get("x-kind", "codes"), "since": s["x-since"], "doc": s["description"]}
    if "x-why" in s:
        item["why"] = s["x-why"]
    if item["kind"] == "scalar":
        item["unit"] = s["x-unit"]
        item["value"] = s["x-value"]
        return item
    if item["kind"] != "words":
        sys.exit(f"dbwords: an item of kind {item['kind']} is no words or scalar item of plugin-db's")
    if "x-groups" in s:
        item["groups"] = s["x-groups"]
    words = {}
    for w in s["oneOf"]:
        e = {"word": w["const"]}
        if "x-group" in w:
            e["group"] = w["x-group"]
        if "description" in w:
            e["doc"] = w["description"]
        if "x-text" in w:
            e["text"] = {"en": w["x-text"]}
        words[w["title"]] = e
    item["words"] = words
    return item


def files():
    path = domain_path()
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"dbwords: the domain plugin-db is not readable ({path}): {e}")
    out = {}
    for name, s in doc["components"]["schemas"].items():
        if "x-file" in s:
            out.setdefault(s["x-file"], {})[name] = data_item(s)
    return out


def items(name):
    return files().get(name, {})
