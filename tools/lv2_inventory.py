#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""lv2_inventory.py: the inventory of the LV2 vocabulary as installed, and the coverage of plugin-db's domain lv2.

The inventory (inventory/lv2.json) is every term an LV2 specification bundle defines, with the versions it was read
from; it is written by this tool and never edited by hand. The domain lv2 (contract.d/lv2/lv2.json) maps it term by
term: every installed LV2 term is mapped, with its status, and no term is mapped that the inventory lacks. Moved from
omx-contract's tools/format-inventory.mjs (its LV2 half) and tools/data-layout.mjs (coverageProblems, LV2 half) with
the terms themselves (sorting pass, V27a, O1); the inventory is byte for byte the one that tool writes.

  python3 tools/lv2_inventory.py [--lv2 <lv2 dir>] [--out <dir>] [--check]   write or check inventory/lv2.json
  python3 tools/lv2_inventory.py coverage [--inventory <dir>] [--domain <lv2.json>]

--lv2 defaults to pkg-config's lv2dir (else /usr/lib64/lv2). The bundles are read through serdi (Turtle to
N-Triples). Exit 0 written, equal or covered; 1 a difference or a coverage problem (each named) or a source that
cannot be read; 2 usage."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INVENTORY = os.path.join(ROOT, "inventory")
DOMAIN = os.path.join(ROOT, "contract.d", "lv2", "lv2.json")

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
LV2 = "http://lv2plug.in/ns/lv2core#"

# the bundles under an LV2 directory that are no LV2 specification: the RDF, OWL and XSD schemas LV2 ships
NOT_SPECS = ["schemas.lv2"]

# the prefixes a type is written with in the inventory, so a reader sees owl:ObjectProperty, not the IRI
CURIES = [
    ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL), ("lv2", LV2), ("xsd", "http://www.w3.org/2001/XMLSchema#"),
    ("atom", "http://lv2plug.in/ns/ext/atom#"), ("ui", "http://lv2plug.in/ns/extensions/ui#"),
    ("units", "http://lv2plug.in/ns/extensions/units#"), ("opts", "http://lv2plug.in/ns/ext/options#"),
    ("patch", "http://lv2plug.in/ns/ext/patch#"), ("pg", "http://lv2plug.in/ns/ext/port-groups#"),
    ("state", "http://lv2plug.in/ns/ext/state#"), ("time", "http://lv2plug.in/ns/ext/time#"),
    ("midi", "http://lv2plug.in/ns/ext/midi#"), ("ev", "http://lv2plug.in/ns/ext/event#"),
    ("param", "http://lv2plug.in/ns/ext/parameters#"), ("pprops", "http://lv2plug.in/ns/ext/port-props#"),
    ("pset", "http://lv2plug.in/ns/ext/presets#"), ("bufsz", "http://lv2plug.in/ns/ext/buf-size#"),
    ("log", "http://lv2plug.in/ns/ext/log#"), ("morph", "http://lv2plug.in/ns/ext/morph#"),
    ("rsz", "http://lv2plug.in/ns/ext/resize-port#"), ("urid", "http://lv2plug.in/ns/ext/urid#"),
    ("work", "http://lv2plug.in/ns/ext/worker#"), ("dman", "http://lv2plug.in/ns/ext/dynmanifest#"),
]
LOCAL = re.compile(r"^[A-Za-z0-9_-]+$")


def curie(iri):
    for p, ns in CURIES:
        if iri.startswith(ns) and LOCAL.match(iri[len(ns):]):
            return f"{p}:{iri[len(ns):]}"
    return iri


TERM = re.compile(r'\s*(<[^>]*>|_:\S+|"(?:[^"\\]|\\.)*"(?:\^\^<[^>]*>|@[A-Za-z-]+)?)')
SUFFIX = re.compile(r'(\^\^<[^>]*>|@[A-Za-z-]+)$')


def parse_ntriples(text):
    """N-Triples text as [[s, p, o]]: IRIs bare, a blank node _:x, a literal as "text" with its datatype dropped"""
    out = []
    for line in text.split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        pos = 0
        t = []
        for _ in range(3):
            m = TERM.match(line, pos)
            if not m:
                raise ValueError(f"not N-Triples: {line}")
            pos = m.end()
            v = m.group(1)
            t.append(v[1:-1] if v.startswith("<") else SUFFIX.sub("", v) if v.startswith('"') else v)
        out.append(t)
    return out


def turtle(path):
    r = subprocess.run(["serdi", "-q", "-i", "turtle", "-o", "ntriples", path], capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError(f"{path}: serdi: {r.stderr.strip()}")
    return parse_ntriples(r.stdout)


def read_bundle(d):
    """one bundle's specification: {bundle, uri, version, [deprecated], terms: [{uri, name, types, [deprecated],
    [label]}]}, the terms every IRI a triple of its non-manifest files is about that lies in the specification's
    namespace, and the specification's own URI (named after its bundle), sorted by IRI"""
    manifest = turtle(os.path.join(d, "manifest.ttl"))
    specs = [s for s, p, o in manifest if p == RDF + "type" and o == LV2 + "Specification"]
    if len(specs) != 1:
        raise ValueError(f"{d}: the manifest names {len(specs)} specifications")
    uri = specs[0]

    def num(p):
        v = next((o for s, q, o in manifest if s == uri and q == LV2 + p), None)
        return None if v is None else v.replace('"', "")

    triples = [t for f in sorted(os.listdir(d)) if f.endswith(".ttl") and f != "manifest.ttl"
               for t in turtle(os.path.join(d, f))]

    def in_ns(iri):
        return iri == uri or ((iri.startswith(uri + "#") or iri.startswith(uri + "/")) and len(iri) > len(uri) + 1)

    bundle = os.path.basename(d)
    terms = {}
    for s, p, o in triples:
        if not in_ns(s):
            continue
        t = terms.setdefault(s, {"uri": s, "name": bundle if s == uri else s[len(uri) + 1:], "types": set()})
        if p == RDF + "type":
            t["types"].add(curie(o))
        if p == OWL + "deprecated" and re.match(r'^"(true|1)"$', o):
            t["deprecated"] = True
        if p == RDFS + "label" and not t.get("label"):
            t["label"] = json.loads(o)
    spec_deprecated = terms.get(uri, {}).get("deprecated") is True
    out_terms = []
    for key in sorted(terms):
        t = terms[key]
        o = {"uri": t["uri"], "name": t["name"], "types": sorted(t["types"])}
        if t.get("deprecated"):
            o["deprecated"] = True
        if t.get("label"):
            o["label"] = t["label"]
        out_terms.append(o)
    out = {"bundle": bundle, "uri": uri, "version": f"{num('minorVersion')}.{num('microVersion')}"}
    if spec_deprecated:
        out["deprecated"] = True
    out["terms"] = out_terms
    return out


def read_lv2_dir(d):
    """every LV2 bundle under d read: (specs by bundle name less .lv2, [{bundle, reason}] for each bundle that is no
    specification: a plugin bundle, or one that cannot be read); a bundle never stops the others from being read"""
    bundles = sorted(b for b in os.listdir(d) if b.endswith(".lv2") and b not in NOT_SPECS
                     and os.path.exists(os.path.join(d, b, "manifest.ttl")))
    if not bundles:
        raise ValueError(f"no LV2 bundle under {d}")
    specs, unread = {}, []
    for b in bundles:
        name = b[:-len(".lv2")]
        try:
            manifest = turtle(os.path.join(d, b, "manifest.ttl"))

            def names(typ):
                return sum(1 for s, p, o in manifest if p == RDF + "type" and o == typ)
            if names(LV2 + "Specification") == 0 and names(LV2 + "Plugin") > 0:
                unread.append({"bundle": name, "reason": "a plugin bundle: its manifest names plugins and no specification"})
                continue
            specs[name] = read_bundle(os.path.join(d, b))
        except ValueError as e:
            unread.append({"bundle": name, "reason": str(e).replace(os.path.join(d, b) + ": ", "")})
    return specs, unread


def pkg(args):
    try:
        r = subprocess.run(["pkg-config"] + args, capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def default_lv2_dir():
    return pkg(["--variable=lv2dir", "lv2"]) or "/usr/lib64/lv2"


def inventory_text(lv2_dir=None):
    """inventory/lv2.json as the tool writes it, from the LV2 installed at lv2_dir"""
    doc = {"format": "lv2", "from": "the LV2 specification bundles (lv2 package)",
           "version": pkg(["--modversion", "lv2"]) or "unknown", "specs": read_lv2_dir(lv2_dir or default_lv2_dir())[0]}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def path_name(p):
    return re.sub(r"[^A-Za-z0-9]+", "_", p).upper()


def coverage_problems(schemas, inventory):
    """the coverage problems of the domain lv2's items (its components.schemas) against the inventory: [message]"""
    out = []
    mapped = set()
    for name, spec in inventory["specs"].items():
        want_item = f"LV2_{path_name(name)}_TERMS"
        it = schemas.get(want_item)
        if not it or it.get("x-kind") != "terms":
            out.append(f"{want_item}: the LV2 specification {spec['uri']} is not mapped")
            continue
        mapped.add(want_item)
        if it.get("x-spec") != spec["uri"] or it.get("x-version") != spec["version"]:
            out.append(f"{want_item}: spec {it.get('x-spec')} {it.get('x-version')}, the installed one is "
                       f"{spec['uri']} {spec['version']}")
        terms = {w["const"]: w.get("x-term", {}) for w in it["oneOf"]}
        want = {t["name"]: t for t in spec["terms"]}
        for n, t in want.items():
            m = terms.get(n)
            if m is None:
                out.append(f"{want_item}: {t['uri']} is not mapped")
            elif m.get("uri") != t["uri"]:
                out.append(f"{want_item}: {n} maps {m.get('uri')}, the term is {t['uri']}")
            elif not m.get("status"):
                out.append(f"{want_item}: {n} has no status")
        for n in terms:
            if n not in want:
                out.append(f"{want_item}: {n} is no term of the installed {spec['uri']}")
    for n, it in schemas.items():
        if it.get("x-kind") == "terms" and n not in mapped:
            out.append(f"{n}: maps no installed specification")
    return out


def main(argv):
    if argv[:1] == ["coverage"]:
        inv_dir, dom = INVENTORY, DOMAIN
        args = argv[1:]
        while args:
            a = args.pop(0)
            if a == "--inventory" and args:
                inv_dir = args.pop(0)
            elif a == "--domain" and args:
                dom = args.pop(0)
            else:
                print(f"lv2_inventory: unknown argument {a}", file=sys.stderr)
                return 2
        problems = coverage_problems(json.load(open(dom))["components"]["schemas"],
                                     json.load(open(os.path.join(inv_dir, "lv2.json"))))
        for p in problems:
            print(f"lv2_inventory: {p}", file=sys.stderr)
        if not problems:
            print("lv2_inventory: every installed LV2 term is mapped by the domain lv2, with its status, and nothing more")
        return 1 if problems else 0
    lv2_dir, out, check = None, INVENTORY, False
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--check":
            check = True
        elif a in ("--lv2", "--out") and args:
            v = args.pop(0)
            if a == "--out":
                out = v
            else:
                lv2_dir = v
        else:
            print(f"lv2_inventory: unknown argument {a}", file=sys.stderr)
            return 2
    try:
        text = inventory_text(lv2_dir)
    except (OSError, ValueError) as e:
        print(f"lv2_inventory: {e}", file=sys.stderr)
        return 1
    p = os.path.join(out, "lv2.json")
    if not check:
        os.makedirs(out, exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
        print(f"lv2_inventory: wrote {p}")
        return 0
    have = open(p).read() if os.path.exists(p) else ""
    if have != text:
        print(f"lv2_inventory: {p} is not the inventory of the installed LV2: run python3 tools/lv2_inventory.py and map "
              "what changed", file=sys.stderr)
        return 1
    print("lv2_inventory: the committed inventory is the installed LV2's")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
