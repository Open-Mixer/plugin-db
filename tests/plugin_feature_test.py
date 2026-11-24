# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The plugin features are plugin-db's: its domain plugin-feature (contract.d/plugin-feature/plugin-feature.json and its
catalogs), sorting pass row V24.

plugin-db is inner to the CLAP level (the ruled layer order), so the domain reads no CLAP domain: a CLAP word (const
clap.<feature>) names its CLAP term by its spelling, and the CLAP level holds that its terms and these words agree. The
LV2 words keep their from, a term of plugin-db's own domain lv2.

(a) golden: the five PLUGIN_FEATURE_* items, read as a reader reads a domain (each word's const, title, text and from),
    have the digest of tests/golden/plugin-features.digest, frozen from omx-contract 3.20.2's plugin-features file
    with the CLAP froms left out, and the catalogs hold one message per word in each of the six languages;
(b) the domain: every LV2 from names a term of the domain lv2, and the domain requires and names no domain but lv2;
    its info.x-requires is a sorted array of names with no version (ops wave 2026-11-24).
    It is the one source of the plugin features: no old home in omx-contract is read (tests/old_home_test.py);
(c) sabotage: a word dropped, a text changed, a from naming no term, a CLAP from put back and the old map form
    {name: ">= x.y.z"} of info.x-requires are each seen."""
import copy
import hashlib
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOM = os.path.join(ROOT, "contract.d", "plugin-feature")
GOLDEN = os.path.join(ROOT, "tests", "golden", "plugin-features.digest")
LV2 = os.path.join(ROOT, "contract.d", "lv2", "lv2.json")
ITEMS = ["PLUGIN_FEATURE_AUDIO_EFFECT", "PLUGIN_FEATURE_INSTRUMENT", "PLUGIN_FEATURE_NOTE_EFFECT",
         "PLUGIN_FEATURE_ANALYZER", "PLUGIN_FEATURE_OTHER"]
LANGS = ["ca", "de", "es", "fr", "it", "pt"]

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def read(doc):
    """the domain's items in the data form's shape: {item: {key: {word, doc?, text?, from?}}}"""
    out = {}
    for name, s in doc["components"]["schemas"].items():
        words = {}
        for w in s["oneOf"]:
            e = {"word": w["const"]}
            if "description" in w:
                e["doc"] = w["description"]
            if "x-text" in w:
                e["text"] = w["x-text"]
            if "x-from" in w:
                e["from"] = [f["$ref"].rsplit("/", 1)[1] + "#" + f["x-term"] for f in w["x-from"]]
            words[w["title"]] = e
        out[name] = words
    return out


def requires(doc):
    """info.x-requires: a sorted, non-empty JSON array of package or domain names, with no version; an absent field refers
    to nothing; None for any other form (the old map {name: ">= x.y.z"} and an empty [] are refused, never read)"""
    if "x-requires" not in doc["info"]:
        return []  # absent: the domain refers to nothing outside itself
    req = doc["info"]["x-requires"]
    if not isinstance(req, list) or not req or not all(isinstance(n, str) for n in req) or req != sorted(set(req)):
        return None  # the map form, an empty [] (write no field instead), or an unsorted or doubled list
    return req


def outside(doc):
    """the domains the document requires or names other than lv2"""
    refs = {f["$ref"].split("/contract/", 1)[1].split("#", 1)[0] for s in doc["components"]["schemas"].values()
            for w in s["oneOf"] for f in w.get("x-from", [])}
    req = requires(doc)
    if req is None:
        return ["info.x-requires (not a non-empty sorted array of names)"]
    return sorted((set(req) | refs) - {"lv2"})


def digest(items):
    text = json.dumps(sorted(items.items()), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"{len(items)} {sum(len(v) for v in items.values())} {hashlib.sha256(text.encode()).hexdigest()}"


def terms(path, item):
    try:
        s = json.load(open(path))["components"]["schemas"]
    except (OSError, ValueError, KeyError):
        return None
    return {w["const"] for w in s[item]["oneOf"]} if item in s else None


def unresolved(items, lv2_path):
    out = []
    for name, words in items.items():
        for key, w in words.items():
            for f in w.get("from", []):
                item, term = f.split("#", 1)
                path = lv2_path
                held = terms(path, item)
                if held is None or term not in held:
                    out.append(f"{name}.{key}: {f} is no term of {path}")
    return out


def main():
    doc = json.load(open(os.path.join(DOM, "plugin-feature.json")))
    mine = read(doc)
    golden = open(GOLDEN).read().strip()

    # (a) golden
    check(list(mine) == ITEMS, "the domain plugin-feature holds the five PLUGIN_FEATURE_* items, in order")
    check(digest(mine) == golden, f"their words have the golden digest ({digest(mine)})")
    n = sum(len(v) for v in mine.values())
    for lang in LANGS:
        msgs = json.load(open(os.path.join(DOM, "catalogs", f"{lang}.json")))["messages"]
        keys = {f"{i}.{w['word']}" for i, ws in mine.items() for w in ws.values()}
        check(set(msgs) == keys, f"catalogs/{lang}.json holds one message per word ({len(msgs)} of {n})")

    # (b) the domain
    check(requires(doc) is not None, f"info.x-requires is a sorted array of names with no version ({doc['info'].get('x-requires')!r})")
    check(outside(doc) == [], f"the domain requires and names no domain but lv2 ({outside(doc)})")
    bad = unresolved(mine, LV2)
    check(not bad, "every from names a term of the domain lv2" + ("" if not bad else ": " + "; ".join(bad[:5])))

    # (c) sabotage
    gone = copy.deepcopy(mine)
    gone["PLUGIN_FEATURE_OTHER"].pop(next(iter(gone["PLUGIN_FEATURE_OTHER"])))
    check(digest(gone) != golden, "sabotage: a word dropped changes the digest")
    text = copy.deepcopy(mine)
    w = next(iter(text["PLUGIN_FEATURE_ANALYZER"].values()))
    w["text"] += " Changed."
    check(digest(text) != golden, "sabotage: a text changed changes the digest")
    wrong = copy.deepcopy(mine)
    lv2w = next(w for ws in wrong.values() for w in ws.values() if w.get("from", [""])[0].startswith("LV2_"))
    lv2w["from"] = ["LV2_CORE_TERMS#NoSuchPlugin"]
    check(bool(unresolved(wrong, LV2)), "sabotage: a from naming no term of the domain lv2 is refused")
    back = copy.deepcopy(doc)
    w = next(w for s in back["components"]["schemas"].values() for w in s["oneOf"] if w["const"].startswith("clap."))
    w["x-from"] = [{"$ref": "https://openmixer.org/contract/clap#/components/schemas/CLAP_PLUGIN_FEATURES_TERMS",
                    "x-term": w["const"].split(".", 1)[1]}]
    check(outside(back) == ["clap"], "sabotage: a CLAP from put back names the domain clap and is refused")
    old_map = copy.deepcopy(doc)
    old_map["info"]["x-requires"] = {"lv2": ">= 1.0.0"}
    check(requires(old_map) is None and outside(old_map) == ["info.x-requires (not a non-empty sorted array of names)"],
          "sabotage: the old map form of info.x-requires is refused by name")
    empty = copy.deepcopy(doc)
    empty["info"]["x-requires"] = []
    check(outside(empty) == ["info.x-requires (not a non-empty sorted array of names)"],
          "sabotage: an empty [] info.x-requires is refused by name (an absent field is how a domain refers to nothing)")
    absent = copy.deepcopy(doc)
    absent["info"].pop("x-requires")
    check(requires(absent) == [], "an absent info.x-requires refers to nothing")

    print(f"{'FAIL' if failures else 'ok  '} plugin_feature_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
