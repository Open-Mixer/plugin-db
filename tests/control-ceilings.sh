#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# Every dependency of a package of debian/control on another package of this source carries a ceiling (R-107): an
# exact `(= ${source:Version})` or `(= ${binary:Version})`, or a floor `(>= ...)` with a ceiling `(<< ...)` beside it.
# The channel's installability gate refuses a release that breaks this, after it is tagged; this refuses it here.
# `control-ceilings.sh [control]`; with --self-test it also plants a floor without a ceiling and expects red.
set -eu
check() {
  python3 - "$1" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
stanzas = [s for s in re.split(r"\n\s*\n", text) if s.strip()]
ours = {m.group(1) for s in stanzas for m in [re.search(r"^Package:\s*(\S+)", s, re.M)] if m}
bad = []
for s in stanzas:
    m = re.search(r"^Package:\s*(\S+)", s, re.M)
    if not m:
        continue
    fields = re.findall(r"^(Depends|Pre-Depends|Recommends):(.*(?:\n[ \t].*)*)", s, re.M)
    for field, value in fields:
        clauses = [c.strip() for c in value.replace("\n", " ").split(",") if c.strip()]
        names = {}
        for c in clauses:
            for alt in c.split("|"):
                a = re.match(r"\s*([a-z0-9.+-]+)\s*(?:\(([<>=]+)\s*([^)]+)\))?", alt)
                if a and a.group(1) in ours:
                    names.setdefault(a.group(1), []).append(a.group(2))
        for name, ops in names.items():
            if "=" in ops or ("<<" in ops and (">=" in ops or ">>" in ops)):
                continue
            bad.append(f"{m.group(1)}: {field} {name} {'has no ceiling' if any(o in ('>=', '>>') for o in ops) else 'has no version'} (R-107)")
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
  printf 'Source: s\n\nPackage: a\nDepends: b (>= ${source:Version})\n\nPackage: b\n' > "$tmp/control"
  if check "$tmp/control" >/dev/null; then echo "FAIL the self-test's floor without a ceiling passed"; exit 1; fi
fi
echo "ok every dependency between this source's packages has a ceiling"
