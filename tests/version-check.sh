#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# make version-check in the trees a DEB build sees (#89): Open-Mixer/.github's build-deb renders a snapshot's newest
# debian/changelog entry as <version>+git<time>.<sha> (its separator.sh: every snapshot takes +git) or, named
# explicitly, <version>~git<time>.<sha>. Both are the release's version, so both are green; a changelog entry of another
# version is red. Each case is a scratch copy of VERSION, the spec, debian/changelog and the Makefile.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
case_() { # <name> <sed expression on the changelog's first line> <expect: ok|red>
    d="$tmp/$1"
    mkdir -p "$d/packaging" "$d/debian"
    cp Makefile VERSION "$d/"
    cp packaging/plugin-db.spec "$d/packaging/"
    cp debian/changelog "$d/debian/"
    sed -i "1s/$2/" "$d/debian/changelog"
    rc=0
    out=$(${MAKE:-make} -s -C "$d" version-check 2>&1) || rc=$?
    if [ "$3" = ok ] && [ "$rc" != 0 ]; then echo "FAIL version-check: $1 is red: $out"; exit 1; fi
    if [ "$3" = red ] && [ "$rc" = 0 ]; then echo "FAIL version-check: $1 is green: $out"; exit 1; fi
    echo "ok   version-check: $1 ($(head -1 "$d/debian/changelog" | sed 's/ unstable.*//')) is $3"
}
case_ "a +git snapshot" '^\(\S\+\) (\([^)]*\))/\1 (\2+git1795500000.e33a9b8)' ok
case_ "a ~git snapshot" '^\(\S\+\) (\([^)]*\))/\1 (\2~git1795500000.e33a9b8)' ok
case_ "the release" '^\(\S\+\) (\([^)]*\))/\1 (\2)' ok
case_ "another version" '^\(\S\+\) (\([^)]*\))/\1 (0.0.1+git1795500000.e33a9b8)' red
