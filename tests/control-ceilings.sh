#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# Floors only (owner rule 2026-11-16): no dependency of debian/control carries a ceiling, `(<< ...)` or `(<= ...)`,
# in Depends, Pre-Depends, Recommends or Build-Depends. Breaks/Replaces/Conflicts name a version an upgrade replaces and
# are not dependency ceilings. The file keeps its name: the Makefile's check-control and the CI call it.
# `control-ceilings.sh [control]`; with --self-test it also plants a ceiling and expects red.
set -eu
check() {
  python3 - "$1" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
stanzas = [s for s in re.split(r"\n\s*\n", text) if s.strip()]
bad = []
for s in stanzas:
    m = re.search(r"^(?:Package|Source):\s*(\S+)", s, re.M)
    if not m:
        continue
    fields = re.findall(r"^(Depends|Pre-Depends|Recommends|Build-Depends|Build-Depends-Indep):(.*(?:\n[ \t].*)*)", s, re.M)
    for field, value in fields:
        for c in re.findall(r"([a-z0-9.+-]+)\s*\(\s*(<<|<=)\s*([^)]+)\)", value):
            bad.append(f"{m.group(1)}: {field} {c[0]} has a ceiling ({c[1]} {c[2].strip()}): floors only")
for b in bad:
    print("FAIL " + b)
sys.exit(1 if bad else 0)
PY
}
control=debian/control
[ "${1:-}" = --self-test ] || control=${1:-debian/control}
check "$control" || exit 1
if [ "${1:-}" = --self-test ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  printf 'Source: s\n\nPackage: a\nDepends: b (>= 1), b (<< 2)\n\nPackage: b\n' > "$tmp/control"
  if check "$tmp/control" >/dev/null; then echo "FAIL the self-test's planted ceiling passed"; exit 1; fi
fi
echo "ok no dependency of debian/control has a ceiling (floors only)"
