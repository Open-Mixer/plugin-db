# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""plugin-db's domains are the one source of what moved into them: no plugin-db test or tool reads omx-contract's old
homes of the moved items (its LV2 formats directory, its plugin-features file, the LV2 froms of data/resource-profile.json's
RESOURCE_KINDS and RESOURCE_UNITS) as a second source (sorting pass V24, V27a, F1).

(a) the call: lv2_domain_test.py and plugin_feature_test.py run against a standard that holds a poisoned copy of each
    old home (an LV2 term changed, a plugin feature word changed, a wrong LV2 from on a resource kind) stay green and
    never compare with it;
(b) no file of tests/ or tools/ names an old home in a path it builds.
The standard is $OMX_STANDARD_DIR, else the installed contract directory (pkg-config omx-contract)."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ME = os.path.abspath(__file__)
TESTS = ["lv2_domain_test.py", "plugin_feature_test.py"]
# a path built to an old home: a join or a string naming formats/lv2 or plugin-features.json
OLD_PATH = re.compile(r'"formats",\s*"lv2"|"[^"\s]*formats/lv2[^"\s]*"|"plugin-features\.json"')

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def poison(std):
    """write a changed copy of each old home into the standard std"""
    om = os.path.join(std, "omx-contract")
    os.makedirs(os.path.join(om, "formats", "lv2"), exist_ok=True)
    json.dump({"LV2_WORKER_TERMS": {"kind": "terms", "doc": "poisoned", "format": "lv2",
                                    "spec": "http://lv2plug.in/ns/ext/worker", "version": "0.0",
                                    "terms": {"schedule": {"uri": "urn:poisoned", "kind": "feature", "status": "used"}}}},
              open(os.path.join(om, "formats", "lv2", "worker.json"), "w"))
    json.dump({"PLUGIN_FEATURE_OTHER": {"kind": "words", "since": "0.0.0", "doc": "poisoned",
                                        "words": {"poisoned": {"word": "poisoned", "text": {"en": "poisoned"}}}}},
              open(os.path.join(om, "plugin-features.json"), "w"))
    rp = os.path.join(om, "resource-profile.json")
    if os.path.exists(rp):
        d = json.load(open(rp))
        if "RESOURCE_KINDS" in d:
            d["RESOURCE_KINDS"]["words"]["latency"]["from"] = ["LV2_CORE_TERMS#poisoned"]
            json.dump(d, open(rp, "w"))
    for p in glob.glob(os.path.join(std, "*", "*.json")):
        try:
            d = json.load(open(p))
        except ValueError:
            continue
        s = d.get("components", {}).get("schemas", {}) if isinstance(d, dict) else {}
        if "RESOURCE_KINDS" in s:
            w = next(w for w in s["RESOURCE_KINDS"]["oneOf"] if w["const"] == "latency")
            w["x-from"] = [{"$ref": "https://openmixer.org/contract/lv2#/components/schemas/LV2_CORE_TERMS",
                            "x-term": "poisoned"}]
            json.dump(d, open(p, "w"))


def main():
    src = os.environ.get("OMX_STANDARD_DIR") or subprocess.run(
        ["pkg-config", "--variable=contractdir", "omx-contract"], capture_output=True, text=True).stdout.strip()
    # (a) the call against a poisoned standard
    with tempfile.TemporaryDirectory() as t:
        std = os.path.join(t, "std")
        shutil.copytree(src, std, symlinks=True)
        poison(std)
        env = dict(os.environ, OMX_STANDARD_DIR=std)
        for name in TESTS:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", name)], capture_output=True, text=True,
                               env=env)
            compared = [ln for ln in r.stdout.splitlines() if "the installed omx-contract's" in ln]
            check(r.returncode == 0 and not compared,
                  f"{name} reads no old home: green against a poisoned one, no comparison with it "
                  f"({r.returncode}: {compared[:2] or [ln for ln in r.stdout.splitlines() if ln.startswith('FAIL')][:2]})")
    # (b) no path to an old home is built
    named = []
    for p in sorted(glob.glob(os.path.join(ROOT, "tests", "*")) + glob.glob(os.path.join(ROOT, "tools", "*"))):
        if os.path.abspath(p) == ME or not os.path.isfile(p):
            continue
        for i, ln in enumerate(open(p, errors="replace"), 1):
            code = ln.split("#", 1)[0] if p.endswith((".py", ".sh")) else ln
            if OLD_PATH.search(code):
                named.append(f"{os.path.relpath(p, ROOT)}:{i}")
    check(not named, "no file of tests/ or tools/ builds a path to an old home" + ("" if not named else ": " + ", ".join(named)))
    print(f"{'FAIL' if failures else 'ok  '} old_home_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
