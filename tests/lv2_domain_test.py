# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The LV2 terms and the F1 mapping are plugin-db's: its domains lv2 (contract.d/lv2/lv2.json) and format
(contract.d/format/format.json), sorting pass rows V27a, F1 and O1.

(a) golden: the 24 LV2_*_TERMS of the domain lv2, read as a reader reads them (each item's terms by key), have the
    digest of tests/golden/lv2-terms.digest, frozen from omx-contract 3.20.2 (each item's since left out)'s data/formats/lv2; the domain format's
    two items have their golden words; the F1 lookups (an LV2 unit, designation or port property -> its standard word)
    give the golden standard words.
(b) both sources: while the installed omx-contract still holds data/formats/lv2, its terms are the domain's, item for
    item; every F1 word names a term the domain holds, every unit term has exactly one F1 word, and every standard word
    F1 maps to is one the installed omx-contract declares (PARAM_UNITS, PARAM_SCALES, the descriptor meanings).
(c) sabotage: the same checks over a scratch standard without one unit (dB), a scratch domain with one F1 word dropped
    and one with two words for one term are each refused.

The standard words are read from $OMX_STANDARD_DIR, else the installed contract directory (pkg-config omx-contract):
a domain document holding PARAM_UNITS (its words' const), else the data form 3/omx-contract/primitives.json. The
meanings are omx-contract's descriptor schema ($defs.meaning), $OMX_CONTRACT_SCHEMA, else the installed one."""
import copy
import glob
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
# F1 frozen: the LV2 table plugin-hostd maps today (data/formats/lv2.json lookups) and the grown standard list
GOLDEN_UNITS = {"units:bar": "bar", "units:beat": "beat", "units:bpm": "bpm", "units:cent": "cents", "units:cm": "cm",
                "units:coef": "x", "units:db": "dB", "units:degree": "deg", "units:frame": "frames", "units:hz": "Hz",
                "units:inch": "inch", "units:khz": "kHz", "units:km": "km", "units:m": "m", "units:mhz": "MHz",
                "units:midiNote": "midiNote", "units:mile": "mile", "units:min": "min", "units:mm": "mm",
                "units:ms": "ms", "units:oct": "oct", "units:pc": "percent", "units:s": "s",
                "units:semitone12TET": "st", "urn:openmixer:unit#dBFS": "dBFS", "urn:openmixer:unit#LUFS": "LUFS",
                "urn:openmixer:unit#ratio": "ratio", "urn:openmixer:unit#dBu": "dBu",
                "urn:openmixer:unit#dBoct": "dB-oct"}
GOLDEN_MEANINGS = {k: k for k in ["attack", "bypass", "cutoffFrequency", "decay", "delay", "frequency", "gain", "hold",
                                  "ratio", "release", "resonance", "threshold", "wetDryRatio", "enabled"]}
GOLDEN_SCALES = {"integer": "stepped", "logarithmic": "log"}

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
    """the item as omx-contract's data/formats/lv2 holds it, the shape the golden digest hashes; its since is left out, a
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
    return {k: data_form(k, v) for k, v in doc.items() if k.startswith("LV2_") and k.endswith("_TERMS")
            and k != "LV2_OPENMIXER_UNITS_TERMS"}


def lookup(doc, item):
    """the F1 read: {<the term as an LV2 file writes it>: <standard word>}, each word through its x-from term"""
    out = {}
    for w in doc[item]["oneOf"]:
        f = w["x-from"][0]
        src = f["$ref"].rsplit("/", 1)[1]
        term = terms_of(doc[src])[f["x-term"]]
        uri = term["uri"]
        prefix = {"http://lv2plug.in/ns/extensions/units#": "units:"}
        key = next((p + uri[len(u):] for u, p in prefix.items() if uri.startswith(u)), None)
        out[key or (f["x-term"] if item != "LV2_UNIT_IDS" else uri)] = w["const"]
    return out


def standard_words(std_dir, schema_path):
    """(PARAM_UNITS words, PARAM_SCALES words, meanings) of the standard the domain maps to"""
    units = scales = None
    for p in sorted(glob.glob(os.path.join(std_dir, "*", "*.json"))):
        try:
            s = json.load(open(p)).get("components", {}).get("schemas", {})
        except (OSError, ValueError):
            continue
        if "PARAM_UNITS" in s:
            units = {w["const"] for w in s["PARAM_UNITS"]["oneOf"]}
            if "PARAM_SCALES" in s:
                scales = {w["const"] for w in s["PARAM_SCALES"]["oneOf"]}
    prim = os.path.join(std_dir, "3", "omx-contract", "primitives.json")
    if (units is None or scales is None) and os.path.exists(prim):
        d = json.load(open(prim))
        if units is None:
            units = {w["word"] for w in d["PARAM_UNITS"]["words"].values()}
        if scales is None:
            scales = set(d["PARAM_SCALES"]["ids"])
    meanings = set(json.load(open(schema_path))["$defs"]["meaning"]["enum"])
    return units or set(), scales or set(), meanings


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
            for src in ("LV2_UNITS_TERMS", "LV2_OPENMIXER_UNITS_TERMS"):
                for key, t in terms_of(doc[src]).items():
                    if t["kind"] == "unit" and (src, key) not in seen:
                        out.append(f"LV2_UNIT_IDS: the unit {src}#{key} has no word")
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
    check(lookup(doc, "LV2_UNIT_IDS") == GOLDEN_UNITS, "F1: every LV2 unit reads the golden standard unit")
    check(lookup(doc, "LV2_DESIGNATION_MEANINGS") == GOLDEN_MEANINGS, "F1: every designation reads the golden meaning")
    check(lookup(doc, "LV2_PORT_PROPERTY_SCALES") == GOLDEN_SCALES, "F1: every port property reads the golden scale")
    refs = {i.get("x-kinds", {}).get("$ref") for k, i in doc.items() if k.endswith("_TERMS")}
    check(refs == {"https://openmixer.org/contract/format#/components/schemas/FORMAT_TERM_KINDS"},
          "every terms item takes its kinds from the domain format")

    # (b) both sources
    classic = os.path.join(cdir, "3", "omx-contract", "formats", "lv2")
    if os.path.isdir(classic):
        old = {}
        for p in sorted(glob.glob(os.path.join(classic, "*.json"))):
            for k, v in json.load(open(p)).items():
                if k.endswith("_TERMS"):
                    old[k] = {kk: vv for kk, vv in v.items() if kk not in ("source", "why", "since")}
        check(old == mine, f"the installed omx-contract's data/formats/lv2 holds the domain's terms ({len(old)} items)")
        check(digest(old) == open(GOLDEN_DIGEST).read().strip(), "the golden digest is that of the installed classic terms")
    else:
        print(f"skip the installed omx-contract holds no data/formats/lv2 ({classic}): the domain is the one source")
    units, scales, meanings = standard_words(cdir, schema_path)
    bad = f1_refusals(doc, units, scales, meanings)
    check(not bad, "F1: every word names a term of the domain once, every unit has its word, every standard word exists"
          + ("" if not bad else ": " + "; ".join(bad)))

    # (c) sabotage
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
