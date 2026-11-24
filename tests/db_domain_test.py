# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""plugin-db's 18 items are its domain plugin-db (contract.d/plugin-db/plugin-db.json), sorting pass rows V11 and V13.

(a) golden: tools/dbwords.py, the read every render of plugin-db makes (render-db, render-py, render-ts through
    tools/pinwords.py), gives the 18 items with the digest of tests/golden/plugin-db-words.digest, frozen from the pin, db and constants
    files of data/ before the move, and each in the file it came from;
(b) one source: data/ holds no file of the contract directory (store.schema.json, the store's own schema, alone), and no
    file of the tree outside contract.d/ and the changelogs names the pin, db or constants file of data/ as
    a source; while one of them is still there it is compared with the domain;
(c) sabotage: a scratch domain with one word dropped makes the renders' --check of plugin_db_tables.h and vocabulary.py
    red, and gives another digest."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GOLDEN = os.path.join(ROOT, "tests", "golden", "plugin-db-words.digest")
sys.path.insert(0, os.path.join(ROOT, "tools"))

FILES = {"constants.json": ["PLUGIN_DB_PIN_SHA256_HEX_LEN"],
         "db.json": ["PLUGIN_DB_BUNDLE_RULES", "PLUGIN_DB_LAYERS", "PLUGIN_DB_FILES", "PLUGIN_DB_LAYOUT",
                     "PLUGIN_DB_RECORD", "PLUGIN_DB_RECORD_ACTIONS", "PLUGIN_DB_RECORD_CHANGES", "PLUGIN_DB_STATES",
                     "PLUGIN_DB_RUNS", "PLUGIN_DB_REASONS", "PLUGIN_DB_ISOLATION_HOSTS", "PLUGIN_DB_SOURCES",
                     "PLUGIN_DB_BAR", "PLUGIN_DB_LATENCY"],
         "pin.json": ["PLUGIN_DB_PIN_KEYS", "PLUGIN_DB_PIN_CHANGES", "PLUGIN_DB_PIN_LAYOUT_FORMATS"]}

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def digest(files):
    rows = sorted((f, sorted(items.items())) for f, items in files.items())
    text = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(i) for i in files.values())
    return f"{n} {hashlib.sha256(text.encode()).hexdigest()}"


def data_files():
    """what data/ still holds of the three files, its items only (no $schema, requires or render)"""
    out = {}
    for f in FILES:
        p = os.path.join(ROOT, "data", f)
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            out[f] = {k: v for k, v in d.items() if isinstance(v, dict) and "kind" in v}
    return out


def render_check(env, tool, out):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", tool), "--check", os.path.join(ROOT, "data"),
                        os.path.join(ROOT, out)], env=env, capture_output=True, text=True)
    return r.returncode


def main():
    import dbwords
    golden = open(GOLDEN).read().strip()

    # (a) golden
    files = dbwords.files()
    check({f: list(i) for f, i in files.items()} == FILES, "the domain's items with an x-file are the 18, each in its file")
    check(digest(files) == golden, f"the renders' read of them has the golden digest ({digest(files)})")

    # (b) one source
    left = sorted(f for f in os.listdir(os.path.join(ROOT, "data")) if f != "store.schema.json")
    check(not left, "data/ holds the store's schema alone" + (f" (and {', '.join(left)})" if left else ""))
    old = data_files()
    for f, its in old.items():
        check(its == files.get(f), f"data/{f}, still there, holds the domain's items")
    named = subprocess.run(["git", "-C", ROOT, "grep", "-l", "-E", r"data/(pin|db|constants)\.json", "--", ".",
                            ":!contract.d", ":!debian/changelog", ":!packaging/plugin-db.spec", ":!CHANGELOG*",
                            ":!tests/db_domain_test.py", ":!include", ":!python/plugin_db/vocabulary.py",
                            ":!ts/src/vocabulary.ts", ":!tools/render-*.py", ":!tools/dbwords.py"],
                           capture_output=True, text=True).stdout.split()
    check(not named, "no file names the pin, db or constants file of data/ as a source"
          + (": " + ", ".join(named) if named else ""))

    # (c) sabotage
    doc = json.load(open(dbwords.domain_path(), encoding="utf-8"))
    cut = copy.deepcopy(doc)
    cut["components"]["schemas"]["PLUGIN_DB_REASONS"]["oneOf"].pop()
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "plugin-db.json")
        json.dump(cut, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        env = dict(os.environ, PLUGIN_DB_DOMAIN=p)
        check(render_check(env, "render-db.py", "include/plugin-db/plugin_db_tables.h") != 0,
              "sabotage: a word dropped from the domain makes plugin_db_tables.h's --check red")
        check(render_check(env, "render-py.py", "python/plugin_db/vocabulary.py") != 0,
              "sabotage: a word dropped from the domain makes vocabulary.py's --check red")
        os.environ["PLUGIN_DB_DOMAIN"] = p
        check(digest(dbwords.files()) != golden, "sabotage: a word dropped gives another digest")
        del os.environ["PLUGIN_DB_DOMAIN"]

    print(f"{'FAIL' if failures else 'ok  '} db_domain_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
