# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The plugin features are plugin-db's: its domain plugin-feature (contract.d/plugin-feature/plugin-feature.json and its
catalogs), sorting pass row V24.

(a) golden: the five PLUGIN_FEATURE_* items, read as a reader reads a domain (each word's const, title, text and from),
    have the digest of tests/golden/plugin-features.digest, frozen from omx-contract 3.20.2's data/plugin-features.json,
    and the catalogs hold one message per word in each of the six languages;
(b) both sources: while the installed omx-contract holds data/plugin-features.json, its words and their catalog texts are
    the domain's; every LV2 from names a term of plugin-db's domain lv2, and every CLAP from a term of omx-clap-core's
    domain clap when a contract directory holding it is named ($CLAP_DOMAIN_DIR) or installed;
(c) sabotage: a word dropped, a text changed and a from naming no term are each seen."""
import copy
import glob
import hashlib
import json
import os
import subprocess
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


def contractdir():
    return subprocess.run(["pkg-config", "--variable=contractdir", "omx-contract"], capture_output=True,
                          text=True).stdout.strip()


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


def classic(d):
    return {k: {key: {kk: (vv["en"] if kk == "text" else vv) for kk, vv in w.items()} for key, w in v["words"].items()}
            for k, v in d.items() if k.startswith("PLUGIN_FEATURE_")}


def digest(items):
    text = json.dumps(sorted(items.items()), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"{len(items)} {sum(len(v) for v in items.values())} {hashlib.sha256(text.encode()).hexdigest()}"


def terms(path, item):
    try:
        s = json.load(open(path))["components"]["schemas"]
    except (OSError, ValueError, KeyError):
        return None
    return {w["const"] for w in s[item]["oneOf"]} if item in s else None


def unresolved(items, lv2_path, clap_path):
    out = []
    for name, words in items.items():
        for key, w in words.items():
            for f in w.get("from", []):
                item, term = f.split("#", 1)
                path = lv2_path if item.startswith("LV2_") else clap_path
                if path is None:
                    continue
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

    # (b) both sources
    cdir = os.environ.get("OMX_STANDARD_DIR") or contractdir()
    old = os.path.join(cdir, "3", "omx-contract", "plugin-features.json")
    if os.path.exists(old):
        check(classic(json.load(open(old))) == mine, "the installed omx-contract's plugin-features.json holds the domain's words")
        check(digest(classic(json.load(open(old)))) == golden, "the golden digest is that of the installed classic words")
    else:
        print(f"skip the installed omx-contract holds no plugin-features.json ({old}): the domain is the one source")
    clap_dir = os.environ.get("CLAP_DOMAIN_DIR") or cdir
    clap = os.path.join(clap_dir, "clap", "clap.json")
    clap = clap if os.path.exists(clap) else None
    if clap is None:
        print(f"skip no domain clap of omx-clap-core in {clap_dir}: the CLAP froms are not resolved here")
    bad = unresolved(mine, LV2, clap)
    check(not bad, "every from names a term of its format's domain" + ("" if not bad else ": " + "; ".join(bad[:5])))

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
    check(bool(unresolved(wrong, LV2, None)), "sabotage: a from naming no term of the domain lv2 is refused")

    print(f"{'FAIL' if failures else 'ok  '} plugin_feature_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
