# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The whole LV2 vocabulary is mapped by plugin-db's domain lv2: every term of inventory/lv2.json has its term in the
domain, with its URI and its status, and the domain maps no term the inventory lacks (tools/lv2_inventory.py, the LV2
half of omx-contract's format coverage check, moved with the terms; sorting pass V27a, O1).

(a) the call: `tools/lv2_inventory.py coverage` over the committed domain and inventory exits 0, and the inventory
    holds the 24 specifications and 452 terms;
(b) the inventory is the installed LV2's, where serdi and the LV2 bundles are installed (else skipped);
(c) sabotage, each through the same call on a scratch domain or inventory, refused by name: one term unmapped, a term
    without its status, a wrong URI, a wrong version, a term the format does not define, and a newer LV2 installed with
    one term more."""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TOOL = os.path.join(ROOT, "tools", "lv2_inventory.py")
DOMAIN = os.path.join(ROOT, "contract.d", "lv2", "lv2.json")
INVENTORY = os.path.join(ROOT, "inventory")

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def run(*args):
    r = subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)
    return r.returncode, [ln[len("lv2_inventory: "):] for ln in r.stderr.splitlines()]


def coverage(tmp, domain=None, inventory=None):
    """the call over the domain and inventory given (the committed ones when None): (exit code, problems)"""
    args = ["coverage"]
    if domain is not None:
        p = os.path.join(tmp, "lv2.json")
        json.dump(domain, open(p, "w"))
        args += ["--domain", p]
    if inventory is not None:
        d = os.path.join(tmp, "inv")
        os.makedirs(d, exist_ok=True)
        json.dump(inventory, open(os.path.join(d, "lv2.json"), "w"))
        args += ["--inventory", d]
    return run(*args)


def word(doc, item, key):
    return next(w for w in doc["components"]["schemas"][item]["oneOf"] if w["const"] == key)


def main():
    dom = json.load(open(DOMAIN))
    inv = json.load(open(os.path.join(INVENTORY, "lv2.json")))
    with tempfile.TemporaryDirectory() as tmp:
        # (a) the call
        rc, problems = coverage(tmp)
        check(rc == 0 and problems == [], f"every installed LV2 term is mapped by the domain lv2 ({rc}: {problems[:3]})")
        n = sum(len(s["terms"]) for s in inv["specs"].values())
        check(len(inv["specs"]) == 24 and n == 452, f"the inventory holds 24 specifications and 452 terms ({len(inv['specs'])}, {n})")

        # (b) the installed LV2
        lv2dir = subprocess.run(["pkg-config", "--variable=lv2dir", "lv2"], capture_output=True, text=True).stdout.strip() \
            or "/usr/lib64/lv2"
        if shutil.which("serdi") and os.path.exists(os.path.join(lv2dir, "core.lv2")):
            rc, problems = run("--check")
            check(rc == 0, f"the committed inventory is the installed LV2's ({problems})")
        else:
            print(f"skip no serdi or LV2 bundles under {lv2dir}: the inventory is not read again here")

        # (c) sabotage
        d = copy.deepcopy(dom)
        s = d["components"]["schemas"]["LV2_WORKER_TERMS"]
        s["oneOf"] = [w for w in s["oneOf"] if w["const"] != "schedule"]
        check(coverage(tmp, domain=d) == (1, ["LV2_WORKER_TERMS: http://lv2plug.in/ns/ext/worker#schedule is not mapped"]),
              "sabotage: one term unmapped is refused by name")
        d = copy.deepcopy(dom)
        del word(d, "LV2_URID_TERMS", "map")["x-term"]["status"]
        check(coverage(tmp, domain=d) == (1, ["LV2_URID_TERMS: map has no status"]),
              "sabotage: a term without its status is refused by name")
        d = copy.deepcopy(dom)
        word(d, "LV2_URID_TERMS", "map")["x-term"]["uri"] = "http://lv2plug.in/ns/ext/urid#mapped"
        check(coverage(tmp, domain=d) == (1, ["LV2_URID_TERMS: map maps http://lv2plug.in/ns/ext/urid#mapped, the term is "
                                              "http://lv2plug.in/ns/ext/urid#map"]),
              "sabotage: a wrong URI is refused by name")
        d = copy.deepcopy(dom)
        d["components"]["schemas"]["LV2_URID_TERMS"]["x-version"] = "0.1"
        rc, problems = coverage(tmp, domain=d)
        check(rc == 1 and len(problems) == 1 and problems[0].startswith("LV2_URID_TERMS: spec http://lv2plug.in/ns/ext/urid 0.1,"),
              f"sabotage: a wrong version is refused by name ({problems})")
        d = copy.deepcopy(dom)
        s = d["components"]["schemas"]["LV2_WORKER_TERMS"]
        s["oneOf"].append(dict(copy.deepcopy(s["oneOf"][0]), const="invented", title="invented", **{"x-code": 99}))
        check(coverage(tmp, domain=d) == (1, ["LV2_WORKER_TERMS: invented is no term of the installed http://lv2plug.in/ns/ext/worker"]),
              "sabotage: a term the format does not define is refused by name")
        i = copy.deepcopy(inv)
        i["specs"]["worker"]["terms"].append({"uri": "http://lv2plug.in/ns/ext/worker#wake", "name": "wake",
                                              "types": ["lv2:Feature"]})
        check(coverage(tmp, inventory=i) == (1, ["LV2_WORKER_TERMS: http://lv2plug.in/ns/ext/worker#wake is not mapped"]),
              "sabotage: a newer LV2 installed, one term more, is refused until it is mapped")

    print(f"{'FAIL' if failures else 'ok  '} lv2_coverage_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
