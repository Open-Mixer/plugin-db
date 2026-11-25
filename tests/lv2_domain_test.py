# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The LV2 terms and the F1 mapping are plugin-db's: its domains lv2 (contract.d/lv2/lv2.json) and format
(contract.d/format/format.json), sorting pass rows V27a, F1 and O1.

(a) golden: the 24 LV2_*_TERMS of the domain lv2, read as a reader reads them (each item's terms by key), have the
    digest of tests/golden/lv2-terms.digest, frozen from omx-contract 3.20.2's LV2 formats directory (each item's since left out, and the 20 users
    omx-contract's plugin-features file named by their new home, plugin-db's domain plugin-feature); the domain format's
    two items have their golden words; the F1 lookups (an LV2 unit, designation or port property -> its standard word)
    give the golden standard words, and so do the resource lookups (an LV2 term of a resource -> its RESOURCE_KINDS
    word through LV2_RESOURCE_KINDS; units:frame, units:ms, units:s -> frames, ms, s through LV2_UNIT_IDS), frozen from
    the LV2 froms of omx-contract's data/resource-profile.json, which omx-contract drops.
(b) the standard: every F1 word names a term the domain holds, every unit term has exactly one F1 word, and every
    standard word F1 maps to is one the installed omx-contract declares (PARAM_UNITS, PARAM_SCALES, the descriptor
    meanings, RESOURCE_KINDS, RESOURCE_UNITS). The domain lv2 is the one source of the terms and the mapping: no old
    home in omx-contract is read (tests/old_home_test.py).
(c) sabotage: the same checks over a scratch standard without one unit (dB), a scratch domain with one F1 word dropped
    and one with two words for one term are each refused; so are a resource standard without latency and one LV2
    term in two resource words.

The standard words are read from $OMX_STANDARD_DIR, else the installed contract directory (pkg-config omx-contract),
each in the one form omx-contract installs it: PARAM_UNITS and PARAM_SCALES from its domain param (param/param.json),
RESOURCE_KINDS and RESOURCE_UNITS from 3/omx-contract/resource-profile.json; a standard without one is refused by
name, never skipped. No term names a moved file's old home as its user. The meanings are omx-contract's descriptor
schema ($defs.meaning), $OMX_CONTRACT_SCHEMA, else the installed one."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LV2 = os.path.join(ROOT, "contract.d", "lv2", "lv2.json")
FORMAT = os.path.join(ROOT, "contract.d", "format", "format.json")
GOLDEN_DIGEST = os.path.join(ROOT, "tests", "golden", "lv2-terms.digest")

GOLDEN_KINDS = ["specification", "class", "plugin-class", "property", "datatype", "port-property", "feature",
                "extension-data", "option", "parameter", "channel", "port-protocol", "unit", "individual", "extension",
                "factory", "plugin-feature", "port-type", "window-api", "event-type", "note-dialect", "process-status",
                "log-severity", "flag", "enum-value", "constant"]
GOLDEN_STATUSES = ["used", "supported-later", "out-of-scope"]
# F1 frozen: the LV2 table plugin-hostd maps today (its lv2 formats file's lookups) and the grown standard list
GOLDEN_UNITS = {"units:bar": "bar", "units:beat": "beat", "units:bpm": "bpm", "units:cent": "cents", "units:cm": "cm",
                "units:coef": "coef", "units:db": "dB", "units:degree": "deg", "units:frame": "frames", "units:hz": "Hz",
                "units:inch": "inch", "units:khz": "kHz", "units:km": "km", "units:m": "m", "units:mhz": "MHz",
                "units:midiNote": "midiNote", "units:mile": "mile", "units:min": "min", "units:mm": "mm",
                "units:ms": "ms", "units:oct": "oct", "units:pc": "percent", "units:s": "s",
                "units:semitone12TET": "st", "urn:openmixer:unit#dBFS": "dBFS", "urn:openmixer:unit#LUFS": "LUFS",
                "urn:openmixer:unit#ratio": "ratio", "urn:openmixer:unit#dBu": "dBu",
                "urn:openmixer:unit#dBoct": "dBPerOct", "urn:openmixer:unit#dBs": "dBPerS"}
GOLDEN_MEANINGS = {k: k for k in ["attack", "bypass", "cutoffFrequency", "decay", "delay", "frequency", "gain", "hold",
                                  "ratio", "release", "resonance", "threshold", "wetDryRatio", "enabled"]}
GOLDEN_SCALES = {"integer": "stepped", "logarithmic": "log"}
# F1 frozen: the LV2 froms of omx-contract's RESOURCE_KINDS and RESOURCE_UNITS (data/resource-profile.json at b89426c),
# which omx-contract drops; the domain lv2 holds them as LV2_RESOURCE_KINDS and, for the units, LV2_UNIT_IDS
GOLDEN_RESOURCE_KINDS = {"LV2_CORE_TERMS#latency": "latency", "LV2_WORKER_TERMS#schedule": "worker",
                         "LV2_WORKER_TERMS#interface": "worker", "LV2_BUF_SIZE_TERMS#boundedBlockLength": "block-length",
                         "LV2_BUF_SIZE_TERMS#maxBlockLength": "block-length",
                         "LV2_BUF_SIZE_TERMS#minBlockLength": "block-length",
                         "LV2_BUF_SIZE_TERMS#nominalBlockLength": "block-length",
                         "LV2_OPTIONS_TERMS#options": "block-length", "LV2_STATE_TERMS#interface": "state"}
GOLDEN_RESOURCE_UNITS = {"LV2_UNITS_TERMS#frame": "frames", "LV2_UNITS_TERMS#ms": "ms", "LV2_UNITS_TERMS#s": "s"}

# the files that moved into plugin-db's domains, by their old home: a term's `by` names the new home
OLD_HOMES = {"omx-contract:data/plugin-fea" + "tures.json": "plugin-db:contract.d/plugin-feature/plugin-feature.json"}

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def contractdir():
    return subprocess.run(["pkg-config", "--variable=contractdir", "omx-contract"], capture_output=True,
                          text=True).stdout.strip()


def schemas(path):
    return json.load(open(path))["components"]["schemas"]


def terms_of(item):
    """a domain terms item as its data form keys it: {key: term}, the key the const"""
    return {w["const"]: w["x-term"] for w in item["oneOf"]}


def data_form(name, item):
    """the item as omx-contract's LV2 formats directory held it, the shape the golden digest hashes; its since is left out, a
    version of the domain that holds it (1.0.0 in lv2, omx-contract's own release before)"""
    out = {"kind": "terms", "doc": item["description"], "format": item["x-format"],
           "spec": item["x-spec"], "version": item["x-version"]}
    if "x-deprecated" in item:
        out["deprecated"] = item["x-deprecated"]
    out["terms"] = terms_of(item)
    return out


def digest(items):
    """'<items> <terms> <sha256>' of the items by name, canonical JSON"""
    rows = sorted(items.items())
    text = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(i["terms"]) for _, i in rows)
    return f"{len(rows)} {n} {hashlib.sha256(text.encode()).hexdigest()}"


def lv2_terms(doc):
    return {k: data_form(k, v) for k, v in doc.items() if k.startswith("LV2_") and k.endswith("_TERMS")}


def lookup(doc, item):
    """the F1 read: {<the term as an LV2 file writes it>: <standard word>}, each word through its x-from term"""
    out = {}
    for w in doc[item]["oneOf"]:
        f = w["x-from"][0]
        term = terms_of(doc[f["$ref"].rsplit("/", 1)[1]])[f["x-term"]]
        uri = term["uri"]
        units = "http://lv2plug.in/ns/extensions/units#"
        out["units:" + uri[len(units):] if uri.startswith(units) else f["x-term"]] = w["const"]
    return out


def by_term(doc, item):
    """the read of a mapping item: {<item>#<term>: <standard word>} through every x-from of every word"""
    return {f["$ref"].rsplit("/", 1)[1] + "#" + f["x-term"]: w["const"]
            for w in doc[item]["oneOf"] for f in w["x-from"]} if item in doc else {}


def resource_profile(std_dir):
    """(RESOURCE_KINDS words, RESOURCE_UNITS words) of the standard, from the one form omx-contract installs them in,
    <contractdir>/3/omx-contract/resource-profile.json; None when it is not there"""
    p = os.path.join(std_dir, "3", "omx-contract", "resource-profile.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    if "RESOURCE_KINDS" not in d or "RESOURCE_UNITS" not in d:
        return None
    return ({w["word"] for w in d["RESOURCE_KINDS"]["words"].values()},
            {w["word"] for w in d["RESOURCE_UNITS"]["words"].values()})


def resource_refusals(doc, kinds, runits):
    """what the resource check refuses: [] when every LV2_RESOURCE_KINDS word names held terms, each term once, and is a
    RESOURCE_KINDS word, and the LV2 units a resource is given in read RESOURCE_UNITS words through LV2_UNIT_IDS"""
    out = []
    seen = set()
    for w in doc.get("LV2_RESOURCE_KINDS", {"oneOf": []})["oneOf"]:
        for f in w["x-from"]:
            src = f["$ref"].rsplit("/", 1)[1]
            if src not in doc or f["x-term"] not in terms_of(doc[src]):
                out.append(f"LV2_RESOURCE_KINDS.{w['title']}: names {src}#{f['x-term']}, no term of the domain")
            if (src, f["x-term"]) in seen:
                out.append(f"LV2_RESOURCE_KINDS.{w['title']}: a second word for {src}#{f['x-term']}")
            seen.add((src, f["x-term"]))
        if w["const"] not in kinds:
            out.append(f"LV2_RESOURCE_KINDS.{w['title']}: {w['const']!r} is no RESOURCE_KINDS word")
    units = by_term(doc, "LV2_UNIT_IDS")
    for term in GOLDEN_RESOURCE_UNITS:
        if units.get(term) not in runits:
            out.append(f"LV2_UNIT_IDS: {term} reads {units.get(term)!r}, no RESOURCE_UNITS word")
    return out


def uri_refusals(doc):
    """each OpenMixer unit word's x-uri is the exact urn a TTL writer writes, and round-trips to its title: the name after
    urn:openmixer:unit#, lower-cased"""
    out = []
    for w in doc["LV2_OPENMIXER_UNIT_IDS"]["oneOf"]:
        uri = w.get("x-uri")
        if not isinstance(uri, str) or not uri.startswith("urn:openmixer:unit#"):
            out.append(f"LV2_OPENMIXER_UNIT_IDS.{w['title']}: x-uri {uri!r} is no urn:openmixer:unit# spelling")
        elif uri.split("#", 1)[1].lower() != w["title"]:
            out.append(f"LV2_OPENMIXER_UNIT_IDS.{w['title']}: x-uri {uri} does not round-trip to its title")
    return out


def openmixer_unit(doc, uri):
    """the F1 read of an OpenMixer spelling: the word whose title is the name after urn:openmixer:unit#, lower-cased"""
    name = uri.split("#", 1)[1].lower()
    return next((w["const"] for w in doc["LV2_OPENMIXER_UNIT_IDS"]["oneOf"] if w["title"] == name), None)


def standard_words(std_dir, schema_path):
    """(PARAM_UNITS words, PARAM_SCALES words, meanings) of the standard the domain maps to: PARAM_UNITS and PARAM_SCALES
    from omx-contract's domain param (<contractdir>/param/param.json), its one form; None for a list it does not hold"""
    p = os.path.join(std_dir, "param", "param.json")
    s = json.load(open(p)).get("components", {}).get("schemas", {}) if os.path.exists(p) else {}
    units = {w["const"] for w in s["PARAM_UNITS"]["oneOf"]} if "PARAM_UNITS" in s else None
    scales = {w["const"] for w in s["PARAM_SCALES"]["oneOf"]} if "PARAM_SCALES" in s else None
    meanings = set(json.load(open(schema_path))["$defs"]["meaning"]["enum"])
    return units, scales, meanings


def f1_refusals(doc, units, scales, meanings):
    """what the F1 check refuses: [] when every word names a held term once and maps to a standard word"""
    out = []
    for item, std in (("LV2_UNIT_IDS", units), ("LV2_DESIGNATION_MEANINGS", meanings),
                      ("LV2_PORT_PROPERTY_SCALES", scales)):
        seen = set()
        for w in doc[item]["oneOf"]:
            f = w["x-from"][0]
            src = f["$ref"].rsplit("/", 1)[1]
            if src not in doc or f["x-term"] not in terms_of(doc[src]):
                out.append(f"{item}.{w['title']}: names {src}#{f['x-term']}, no term of the domain")
            if (src, f["x-term"]) in seen:
                out.append(f"{item}.{w['title']}: a second word for {src}#{f['x-term']}")
            seen.add((src, f["x-term"]))
            if w["const"] not in std:
                out.append(f"{item}.{w['title']}: {w['const']!r} is no standard word")
        if item == "LV2_UNIT_IDS":
            for key, t in terms_of(doc["LV2_UNITS_TERMS"]).items():
                if t["kind"] == "unit" and ("LV2_UNITS_TERMS", key) not in seen:
                    out.append(f"LV2_UNIT_IDS: the unit LV2_UNITS_TERMS#{key} has no word")
    out += uri_refusals(doc)
    for w in doc["LV2_OPENMIXER_UNIT_IDS"]["oneOf"]:
        if w["const"] not in units:
            out.append(f"LV2_OPENMIXER_UNIT_IDS.{w['title']}: {w['const']!r} is no standard word")
    return out


def main():
    doc = schemas(LV2)
    fmt = schemas(FORMAT)
    cdir = os.environ.get("OMX_STANDARD_DIR") or contractdir()
    schema_path = os.environ.get("OMX_CONTRACT_SCHEMA") or os.path.join(
        subprocess.run(["pkg-config", "--variable=datadir", "omx-contract"], capture_output=True,
                       text=True).stdout.strip(), "omx-contract.schema.json")

    # (a) golden
    mine = lv2_terms(doc)
    check(len(mine) == 24, f"the domain lv2 holds the 24 LV2_*_TERMS items ({len(mine)})")
    check(digest(mine) == open(GOLDEN_DIGEST).read().strip(),
          f"their terms have the golden digest ({digest(mine)})")
    check([w["const"] for w in fmt["FORMAT_TERM_KINDS"]["oneOf"]] == GOLDEN_KINDS,
          "the domain format's FORMAT_TERM_KINDS are the golden words")
    check([w["const"] for w in fmt["FORMAT_TERM_STATUSES"]["oneOf"]] == GOLDEN_STATUSES,
          "the domain format's FORMAT_TERM_STATUSES are the golden words")
    read = dict(lookup(doc, "LV2_UNIT_IDS"))
    read.update({u: openmixer_unit(doc, u) for u in GOLDEN_UNITS if u.startswith("urn:")})
    written = {w["x-uri"]: w["const"] for w in doc["LV2_OPENMIXER_UNIT_IDS"]["oneOf"] if "x-uri" in w}
    check(written == {u: c for u, c in GOLDEN_UNITS.items() if u.startswith("urn:")},
          "F1: each OpenMixer unit word's x-uri is the golden urn spelling of its standard unit (what a TTL writer writes)")
    check(not uri_refusals(doc), "F1: each x-uri round-trips to its word's title" +
          ("" if not uri_refusals(doc) else ": " + "; ".join(uri_refusals(doc))))
    check(read == GOLDEN_UNITS, "F1: every LV2 unit and OpenMixer spelling reads the golden standard unit")
    check(lookup(doc, "LV2_DESIGNATION_MEANINGS") == GOLDEN_MEANINGS, "F1: every designation reads the golden meaning")
    check(lookup(doc, "LV2_PORT_PROPERTY_SCALES") == GOLDEN_SCALES, "F1: every port property reads the golden scale")
    check(by_term(doc, "LV2_RESOURCE_KINDS") == GOLDEN_RESOURCE_KINDS,
          "F1: every LV2 term of a resource reads the golden RESOURCE_KINDS word (LV2_RESOURCE_KINDS)")
    check({t: by_term(doc, "LV2_UNIT_IDS").get(t) for t in GOLDEN_RESOURCE_UNITS} == GOLDEN_RESOURCE_UNITS,
          "F1: units:frame, units:ms and units:s read the golden resource units frames, ms and s (LV2_UNIT_IDS)")
    kinds = {w["const"] for w in fmt["FORMAT_TERM_KINDS"]["oneOf"]}
    statuses = {w["const"] for w in fmt["FORMAT_TERM_STATUSES"]["oneOf"]}
    odd = [f"{k}#{key}" for k, i in doc.items() if i.get("x-kind") == "terms" for key, t in terms_of(i).items()
           if t["kind"] not in kinds or t["status"] not in statuses]
    check(not odd, "every term's kind and status is a word of the domain format" + (": " + ", ".join(odd[:5]) if odd else ""))

    # (b) the standard
    units, scales, meanings = standard_words(cdir, schema_path)
    check(units is not None and scales is not None,
          f"the standard holds PARAM_UNITS and PARAM_SCALES (omx-contract's domain param under {cdir})")
    units, scales = units or set(), scales or set()
    bad = f1_refusals(doc, units, scales, meanings)
    check(not bad, "F1: every word names a term of the domain once, every unit has its word, every standard word exists"
          + ("" if not bad else ": " + "; ".join(bad)))

    rp = resource_profile(cdir)
    check(rp is not None, f"the standard holds RESOURCE_KINDS and RESOURCE_UNITS ({cdir}/3/omx-contract/resource-profile.json)")
    rkinds, runits = rp or (set(), set())
    bad = resource_refusals(doc, rkinds, runits)
    check(not bad, "F1: every resource word names held terms once and is a RESOURCE_KINDS word; the resource units are"
          " RESOURCE_UNITS words" + ("" if not bad else ": " + "; ".join(bad)))
    moved = sorted({b for i in doc.values() if i.get("x-kind") == "terms" for w in i["oneOf"]
                    for b in w["x-term"].get("by", []) if b in OLD_HOMES})
    check(not moved, "no term names a moved file's old home as its user" + ("" if not moved else ": " + ", ".join(moved)))

    # (c) sabotage
    bent = copy.deepcopy(doc)
    w = next(w for w in bent["LV2_OPENMIXER_UNIT_IDS"]["oneOf"] if w["title"] == "dboct")
    w["x-uri"] = "urn:openmixer:unit#dB-oct"
    check(any("does not round-trip" in r for r in uri_refusals(bent)), "sabotage: an x-uri that does not round-trip is refused")
    w.pop("x-uri")
    check(any("no urn:openmixer:unit# spelling" in r for r in uri_refusals(bent)), "sabotage: a word with no x-uri is refused")
    check(any("'latency' is no RESOURCE_KINDS word" in r for r in resource_refusals(doc, rkinds - {"latency"}, runits)),
          "sabotage: a resource standard without latency is refused")
    again = copy.deepcopy(doc)
    if len(again.get("LV2_RESOURCE_KINDS", {"oneOf": []})["oneOf"]) > 1:
        again["LV2_RESOURCE_KINDS"]["oneOf"][0]["x-from"].append(again["LV2_RESOURCE_KINDS"]["oneOf"][1]["x-from"][0])
    check(any("a second word" in r for r in resource_refusals(again, rkinds, runits)),
          "sabotage: one LV2 term in two resource words is refused")
    check(any("'dB' is no standard word" in r for r in f1_refusals(doc, units - {"dB"}, scales, meanings)),
          "sabotage: a standard list without dB is refused")
    dropped = copy.deepcopy(doc)
    dropped["LV2_UNIT_IDS"]["oneOf"] = [w for w in dropped["LV2_UNIT_IDS"]["oneOf"] if w["title"] != "khz"]
    check(any("units_terms#khz has no word" in r.lower() for r in f1_refusals(dropped, units, scales, meanings)),
          "sabotage: an LV2 unit with no F1 word is refused")
    twice = copy.deepcopy(doc)
    twice["LV2_UNIT_IDS"]["oneOf"].append(dict(twice["LV2_UNIT_IDS"]["oneOf"][0], title="again"))
    check(any("a second word" in r for r in f1_refusals(twice, units, scales, meanings)),
          "sabotage: two F1 words for one term are refused")
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(os.path.join(t, "lv2"))
        gone = copy.deepcopy(json.load(open(LV2)))
        del gone["components"]["schemas"]["LV2_UNITS_TERMS"]["oneOf"][0]
        check(digest(lv2_terms(gone["components"]["schemas"])) != open(GOLDEN_DIGEST).read().strip(),
              "sabotage: a term dropped from the domain changes the digest")

    print(f"{'FAIL' if failures else 'ok  '} lv2_domain_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
