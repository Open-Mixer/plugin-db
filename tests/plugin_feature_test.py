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
    {name: ">= x.y.z"} of info.x-requires are each seen;
(d) the role groups (owner ruling 2026-11-27: a plugin is offered under the group its declared features
    and classes name, through one table here and never a consumer's list): the five items name PLUGIN_FEATURE_ROLES as
    their x-groups, every x-group is a word of it, every role is reached by some word, the table is the golden
    tests/golden/plugin-roles.digest, and the words that carry no group are exactly the ones that name no role. A
    group naming no role, a feature item without x-groups, an unreached role and a word given or stripped of a
    group are each seen."""
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
ROLES = "PLUGIN_FEATURE_ROLES"
ROLES_GOLDEN = os.path.join(ROOT, "tests", "golden", "plugin-roles.digest")
# the words that name no role: a channel layout, the bare effect or plugin, and a role of use (mastering, restoration),
# which says how a plugin is used and not what it does; a plugin declaring only these is filed by its reader's own rule
UNGROUPED = ["clap.ambisonic", "clap.audio-effect", "clap.glitch", "clap.mastering", "clap.mono", "clap.multi-effects",
             "clap.restoration", "clap.stereo", "clap.surround", "lv2.Plugin"]
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


def role_table(doc):
    """{source word: role} over the five feature items, the role None for a word with no x-group"""
    s = doc["components"]["schemas"]
    return {w["const"]: w.get("x-group") for name in ITEMS for w in s[name]["oneOf"]}


def role_refusals(doc):
    """what is wrong with the role groups, one line each"""
    s = doc["components"]["schemas"]
    out = []
    if ROLES not in s:
        return [f"no {ROLES} item"]
    roles = [w["const"] for w in s[ROLES]["oneOf"]]
    for name in ITEMS:
        if s[name].get("x-groups") != ROLES:
            out.append(f"{name} names x-groups {s[name].get('x-groups')!r}, not {ROLES}")
    table = role_table(doc)
    for word, role in table.items():
        if role is not None and role not in roles:
            out.append(f"{word}: x-group {role!r} is no word of {ROLES}")
    used = {r for r in table.values() if r is not None}
    out += [f"{ROLES}.{r}: no word files under it" for r in roles if r not in used]
    bare = sorted(w for w, r in table.items() if r is None)
    if bare != UNGROUPED:
        out.append(f"the words with no group are {bare}, not {UNGROUPED}")
    return out


def role_digest(doc):
    rows = sorted((w, r) for w, r in role_table(doc).items() if r is not None)
    roles = [(w["const"], w["title"], w.get("x-text")) for w in doc["components"]["schemas"][ROLES]["oneOf"]]
    text = json.dumps([roles, rows], ensure_ascii=False, separators=(",", ":"))
    return f"{len(roles)} {len(rows)} {hashlib.sha256(text.encode()).hexdigest()}"


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
    every = read(doc)
    mine = {k: v for k, v in every.items() if k in ITEMS}
    golden = open(GOLDEN).read().strip()

    # (a) golden
    check(list(every) == ITEMS + [ROLES], "the domain plugin-feature holds the five PLUGIN_FEATURE_* items and the role groups, in order")
    check(digest(mine) == golden, f"their words have the golden digest ({digest(mine)})")
    n = sum(len(v) for v in every.values())
    for lang in LANGS:
        msgs = json.load(open(os.path.join(DOM, "catalogs", f"{lang}.json")))["messages"]
        keys = {f"{i}.{w['word']}" for i, ws in every.items() for w in ws.values()}
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

    # (d) the role groups
    bad = role_refusals(doc)
    check(not bad, "the role groups: every feature item names PLUGIN_FEATURE_ROLES, every group is a role, every role is reached"
          + ("" if not bad else ": " + "; ".join(bad[:5])))
    rg = open(ROLES_GOLDEN).read().strip()
    check(role_digest(doc) == rg, f"the role table has the golden digest ({role_digest(doc)})")

    def word(d, const):
        return next(w for name in ITEMS for w in d["components"]["schemas"][name]["oneOf"] if w["const"] == const)
    nogroup = copy.deepcopy(doc)
    word(nogroup, "lv2.Reverb")["x-group"] = "teleport"
    check(any("lv2.Reverb: x-group 'teleport'" in p for p in role_refusals(nogroup)), "sabotage: a group naming no role is refused by name")
    noitem = copy.deepcopy(doc)
    noitem["components"]["schemas"]["PLUGIN_FEATURE_OTHER"].pop("x-groups")
    check(any(p.startswith("PLUGIN_FEATURE_OTHER names x-groups") for p in role_refusals(noitem)), "sabotage: a feature item without x-groups is refused by name")
    unreached = copy.deepcopy(doc)
    for name in ITEMS:
        for w in unreached["components"]["schemas"][name]["oneOf"]:
            if w.get("x-group") == "midi":
                w.pop("x-group")
    check(any(p == "PLUGIN_FEATURE_ROLES.midi: no word files under it" for p in role_refusals(unreached)), "sabotage: an unreached role is refused by name")
    stripped = copy.deepcopy(doc)
    word(stripped, "clap.reverb").pop("x-group")
    check(bool(role_refusals(stripped)) and role_digest(stripped) != rg, "sabotage: a word stripped of its group is seen")
    given = copy.deepcopy(doc)
    word(given, "clap.stereo")["x-group"] = "spatial"
    check(bool(role_refusals(given)) and role_digest(given) != rg, "sabotage: a layout word given a group is seen")
    moved = copy.deepcopy(doc)
    word(moved, "lv2.ParaEQ")["x-group"] = "filters"
    check(role_digest(moved) != rg, "sabotage: a word moved to another group changes the digest")

    print(f"{'FAIL' if failures else 'ok  '} plugin_feature_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
