#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""tests/pin_old_items_test.py: plugin-db no longer holds PLUGIN_DB_PIN_VERDICTS and PLUGIN_DB_PIN_POOLS (sorting pass, V12:
the words of a pin's verdict and pool are plugin-hostd-protocol's, its domain pin). The last PR of the row removes them, and
this test is red while anything of the tree still holds or reads them:

(a) the domain plugin-db's items that rebuild pin.json are exactly those of plugin-db's own file format: PLUGIN_DB_PIN_KEYS, PLUGIN_DB_PIN_CHANGES and
    PLUGIN_DB_PIN_LAYOUT_FORMATS, and the rendered plugin_db_vocabulary.h defines no word of the two;
(b) no file of the tree names either item, or the OMX_ macros of its words (the changelogs, which record what was, and this
    file are the only places that may);
(c) sabotage, in scratch copies: one name planted in a C source, in a data file and in a test is found by the scan.

Exit 0 all green, 1 a FAIL line."""
import json, os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = re.compile(r"PLUGIN_DB_PIN_(?:VERDICTS|POOLS)")
OWN = {"PLUGIN_DB_PIN_KEYS", "PLUGIN_DB_PIN_CHANGES", "PLUGIN_DB_PIN_LAYOUT_FORMATS"}
SKIP_DIRS = {".git", "build", "node_modules"}
failed = 0


def check(cond, what):
    global failed
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        failed += 1


def scan(root):
    """[(file, line number)] of every name of the two items, outside the changelogs and this file"""
    found = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            path = os.path.join(d, f)
            rel = os.path.relpath(path, root)
            if rel in ("tests/pin_old_items_test.py", "debian/changelog"):
                continue
            try:
                text = open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if rel.endswith(".spec"):
                text = text.split("%changelog")[0]
            found += ["%s:%d" % (rel, n) for n, line in enumerate(text.splitlines(), 1) if NAME.search(line)]
    return found


def main():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import dbwords
    items = set(dbwords.items("pin.json"))
    check(items == OWN, "(a) the domain's pin.json items are %s" % sorted(items))
    voc = open(os.path.join(ROOT, "include", "plugin-db", "plugin_db_vocabulary.h")).read()
    check(not NAME.search(voc), "(a) plugin_db_vocabulary.h defines no word of the two items")
    found = scan(ROOT)
    check(not found, "(b) no file names either item: %s" % found[:6])
    with tempfile.TemporaryDirectory() as tmp:
        for what, rel, line in (("a C source", "src/cli.c", "/* PLUGIN_DB_PIN_VERDICTS */\n"),
                                ("a data file", "data/notes.json", '{"PLUGIN_DB_PIN_POOLS": {}}\n'),
                                ("a test", "tests/x.sh", "echo OMX_PLUGIN_DB_PIN_POOLS_OFF\n")):
            t = os.path.join(tmp, what.replace("/", "-").replace(" ", "-"))
            os.makedirs(os.path.join(t, os.path.dirname(rel)), exist_ok=True)
            open(os.path.join(t, rel), "w").write(line)
            check(scan(t) == ["%s:1" % rel], "(c) %s planted in %s is found" % (line.strip()[:40], what))
    return 1 if failed else 0


sys.exit(main())
