#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A dependency between two packages of THIS source has one shape in both formats (dependency audit 2026-11-16):
# the RPM spec's `Requires: <ours> = %{version}-%{release}` is EXACT, so debian/control's clause on the same package
# is `(= ${source:Version})` or `(= ${binary:Version})`, never a floor with a ceiling; a range on one side and an exact
# on the other lets the two formats admit different sets. `dep-shape.sh [spec] [control]`; with --self-test it also
# plants a range beside an exact and expects red.
set -eu
check() {
  python3 - "$1" "$2" <<'PY'
import re, sys
spec, control = open(sys.argv[1]).read(), open(sys.argv[2]).read()
name = re.search(r"^Name:\s*(\S+)", spec, re.M).group(1)
# the spec's packages: the main one, `%package foo` (name-foo) and `%package -n foo`
rpm = {name: ""}
for m in re.finditer(r"^%package(?:\s+-n\s+(\S+)|\s+(\S+))\n(.*?)(?=^%|\Z)", spec, re.M | re.S):
    rpm[m.group(1) or name + "-" + m.group(2)] = m.group(3)
rpm_shape = {}
for pkg, body in rpm.items():
    for m in re.finditer(r"^Requires:\s*(.*)$", body, re.M):
        c = m.group(1).strip()
        em = re.match(r"(\S+) = %\{version\}-%\{release\}$", c)
        rm = re.match(r"\((\S+) >= [^ ]+ with \1 < [^)]+\)$", c)
        dep = em.group(1) if em else rm.group(1) if rm else None
        if dep in rpm:
            rpm_shape[(pkg, dep)] = "exact" if em else "range"
stanzas = [s for s in re.split(r"\n\s*\n", control) if re.search(r"^Package:", s, re.M)]
deb = {re.search(r"^Package:\s*(\S+)", s, re.M).group(1): s for s in stanzas}
deb_shape = {}
for pkg, s in deb.items():
    for field, value in re.findall(r"^(Depends|Pre-Depends):(.*(?:\n[ \t].*)*)", s, re.M):
        ops = {}
        for c in value.replace("\n", " ").split(","):
            a = re.match(r"\s*([a-z0-9.+-]+)\s*\(([<>=]+)\s*([^)]+)\)", c)
            if a and a.group(1) in deb:
                ops.setdefault(a.group(1), []).append(a.group(2))
        for dep, o in ops.items():
            deb_shape[(pkg, dep)] = "exact" if "=" in o else "range"
bad = []
for (pkg, dep), shape in sorted(rpm_shape.items()):
    other = deb_shape.get((pkg, dep))
    if other is not None and other != shape:
        bad.append("%s -> %s: %s in the spec, %s in debian/control" % (pkg, dep, shape, other))
for b in bad:
    print("FAIL " + b)
print("%d dependencies between this source's packages compared" % len([k for k in rpm_shape if k in deb_shape]))
sys.exit(1 if bad else 0)
PY
}
spec=packaging/plugin-db.spec control=debian/control
if [ "${1:-}" != --self-test ]; then spec=${1:-$spec}; control=${2:-$control}; fi
check "$spec" "$control" || exit 1
if [ "${1:-}" = --self-test ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  printf 'Name: s\nVersion: 1\n%%package -n python3-s\nRequires: s = %%{version}-%%{release}\n' > "$tmp/spec"
  printf 'Source: s\n\nPackage: s\n\nPackage: python3-s\nDepends: s (>= ${source:Version}), s (<< 2~)\n' > "$tmp/control"
  if check "$tmp/spec" "$tmp/control" >/dev/null; then echo "FAIL the self-test's range beside an exact passed"; exit 1; fi
fi
echo "ok every dependency between this source's packages has one shape in the spec and in debian/control"
