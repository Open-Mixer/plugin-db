#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Derive python/plugin_db/vocabulary.py, the Python twin's words, from data/pin.json and data/db.json.

Each words item becomes a Words object of its words in their order, keyed as data/ keys them and named in snake case
(PLUGIN_DB_RECORD_CHANGES is `record_changes`); a grouped item also has <item>_group, the group word of each word, and
an item whose words carry the owners' `text` has <item>_text. ITEMS names the data/ item of each, which is how a
catalog keys its messages. Nothing here is typed twice, and the twin's source types no word.

    render-py.py [--check] <data dir> <out file>
"""
import json
import sys


def snake(item):
    return (item[len("PLUGIN_DB_"):] if item.startswith("PLUGIN_DB_") else item).lower()


def render(data_dir):
    db = {}
    for name in ("pin.json", "db.json"):
        db.update(json.load(open(f"{data_dir}/{name}")))
    items = {i: b for i, b in db.items() if isinstance(b, dict) and b.get("kind") == "words"}
    out = [
        "# SPDX-License-Identifier: GPL-3.0-or-later",
        "# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>",
        "# GENERATED: DO NOT EDIT BY HAND.",
        "# Produced by tools/render-py.py from data/pin.json and data/db.json. Each words item is a Words object of its words",
        "# in their order, keyed as data/ keys them; a grouped item has <item>_group (the group word of each word).",
        "",
        "",
        "class Words(dict):",
        '    """the words of one item: words.key is the word, and iterating the values gives them in the order of data/"""',
        "",
        "    def __getattr__(self, key):",
        "        try:",
        "            return self[key]",
        "        except KeyError:",
        "            raise AttributeError(key) from None",
        "",
        "",
    ]
    for item, body in items.items():
        name = snake(item)
        out.append(f"# {item}")
        out.append(f"{name} = Words(")
        for key, w in body["words"].items():
            if not key.isidentifier():
                sys.exit(f"render-py.py: {item}: the key {key} is no Python name")
            out.append(f"    {key}={json.dumps(w['word'])},")
        out.append(")")
        texts = {w["word"]: w["text"] for w in body["words"].values() if "text" in w}
        if texts:
            out.append(f"# the owners' text of each word of {item}, by language")
            out.append(f"{name}_text = {json.dumps(texts, ensure_ascii=False, indent=4)}")
        out.append("")
    # every group after every item: a group names words of an item that may come later in data/
    for item, body in items.items():
        if "groups" not in body:
            continue
        name = snake(item)
        out.append(f"# the {body['groups']} word of each word of {item}")
        out.append(f"{name}_group = {{")
        for key, w in body["words"].items():
            group = next(k for k, g in db[body["groups"]]["words"].items() if g["word"] == w["group"])
            out.append(f"    {name}.{key}: {snake(body['groups'])}.{group},")
        out.append("}")
        out.append("")
    out.append("# the data/ item of each words object: a catalog keys a message as <item>.<word>")
    out.append("ITEMS = {")
    for item in items:
        out.append(f"    {json.dumps(snake(item))}: {json.dumps(item)},")
    out.append("}")
    out.append("")
    schema = json.load(open(f"{data_dir}/store.schema.json"))["$defs"]["recordFields"]
    out.append("# the keys a record must carry (data/store.schema.json, recordFields) and its host's")
    out.append(f"record_required = {json.dumps(schema['required'])}")
    out.append(f"record_host_required = {json.dumps(schema['properties']['host']['required'])}")
    out.append("")
    return "\n".join(out)


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if len(args) != 2:
        sys.exit(__doc__)
    text = render(args[0])
    if check:
        try:
            have = open(args[1]).read()
        except OSError:
            have = None
        if have != text:
            sys.exit(f"render-py.py: {args[1]} is not what data/ renders: run make render-py")
        return
    open(args[1], "w").write(text)


main(sys.argv[1:])
