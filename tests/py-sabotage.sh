#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# Each arm breaks one rule of the Python twin, one word of its generated vocabulary, a sentence of a catalog, or the
# conformance of its sources, in a copy of the tree, and the tests over it must go red: the golden fixtures are what
# holds the Python twin to the C reader and to the TypeScript twin, so a rule they would split on is red here. An arm
# whose text is gone is itself a failure: a guard nothing reaches is no guard.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
TWIN='PYTHONPATH=python python3 -W error -m unittest discover -s python/tests'

arm() { # <what> <file> <text => replacement | append: text> <command, default the twin's tests>
    rm -rf "$tmp/t"
    mkdir "$tmp/t"
    cp -r Makefile VERSION catalogs data python tests tools "$tmp/t/"
    if ! python3 - "$tmp/t/$2" "$3" <<'PY'
import sys
path, spec = sys.argv[1:]
s = open(path).read()
if spec.startswith("append: "):
    open(path, "w").write(s + spec[len("append: "):] + "\n")
    sys.exit(0)
before, after = spec.split(" => ")
if before not in s:
    sys.exit("the text is gone: " + before)
open(path, "w").write(s.replace(before, after, 1))
PY
    then echo "FAIL $1: the arm no longer applies"; fail=1; return; fi
    if (cd "$tmp/t" && sh -c "${4:-$TWIN}") >"$tmp/log" 2>&1; then echo "FAIL $1: stays green"; fail=1
    else echo "ok   $1 is red"; fi
}

R=python/plugin_db/reader.py V=python/plugin_db/vocabulary.py T=python/plugin_db/text.py
arm "a shipped refusal is not read" $R 'and reference["verdict"] == v.pin_verdicts.refused): => and False):'
arm "a warned override is not read" $R "if warned_override: => if False:"
arm "a figure at the line is over it" $R "if latency_ms > line_ms => if latency_ms >= line_ms"
arm "a missing line is guessed" $R "if latency_ms is None or line_ms is None: => if latency_ms is None:"
arm "a refusal has a tier" $R 'if answering["verdict"] in (v.pin_verdicts.inProcess, v.pin_verdicts.isolated) else None => if answering["verdict"] is not None else None'
arm "the rules are not compared" $R 'return _differs(r["rules"], h.get("rules")) => return False'
arm "absent is not first" $R "if files == v.files.absent: => if False:"
arm "the figure is the cell of any quantum" $R 'and c["quantum"] == quantum), None) => ), None)'
arm "a record of other bytes is trusted" $R '"pinFiles": ours is not None and pin["files"] == ours["files"], => "pinFiles": True,'
arm "isolated only without plugin-hostd" $R 'if r["hostName"] is not None and r["hostName"] in v.isolation_hosts.values(): => if True:'
arm "a true is read as a number" $R " and not isinstance(x, bool) => "
arm "a layout pinned since the record is not seen" $R '"pinLayout": ours is not None and pin.get("layout") == ours.get("layout"), => "pinLayout": True,'
arm "a run word renamed in the generated vocabulary" $V 'alone="alone" => alone="solo"'
arm "a reason renamed in the generated vocabulary" $V 'noCell="no-cell" => noCell="no-room"'
arm "a vocabulary changed by hand is red to the render check" $V 'alone="alone" => alone="solo"' "make check-py"
arm "a catalog sentence is not read" $T 'return said if isinstance(said, str) and said else source => return source'
arm "a catalog is read for English" $T "    if lang == SOURCE:
        return source
 => "
arm "a fact not known here is given" python/plugin_db/query.py "if here.get(key) is not None: => if True:"
arm "an epoch of zero is not given" python/plugin_db/query.py "if here.get(key) is not None: => if here.get(key):"
arm "a command that fails is read" python/plugin_db/query.py "if r.returncode: => if False:"
arm "a run word typed in the twin" $R 'append: TYPED = "alone"'
arm "a tier word typed in the twin" $R "append: TYPED = 'in-process'"
arm "an owner's sentence typed in the twin" $T "append: TYPED = \"the plugin's files are gone; show names the path that was pinned\""
[ "$fail" = 0 ] || exit 1
echo "ok   py sabotage: every arm is red"
