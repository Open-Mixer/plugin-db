#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# While in development there is no backward-compatibility machinery (owner ruling 2026-11-16, audit rows 1-4): no ABI
# baseline for the header-only library, no Breaks/Replaces/moved for a retired package, no @freemixer scope, no
# FREEMIXER_ names read by the commit hook. `no-backcompat.sh`; red names each one still present.
set -u
bad=0
red() { echo "FAIL $1"; bad=1; }
[ ! -e abi ] || red "abi/ (the frozen ABI baseline) still exists"
[ ! -e tests/abi-layout.c ] && [ ! -e tests/abi-probe.c ] || red "the ABI probe sources still exist"
! grep -qE '^(test-abi|abi-layout|abi-baseline|abi-check)\b' Makefile || red "Makefile still has an ABI target"
! grep -q 'abidiff\|make test-abi' .github/workflows/ci.yml || red "ci.yml still has the ABI job"
! grep -qE '^(Breaks|Replaces):' debian/control || red "debian/control still has Breaks/Replaces"
! grep -qE '^ *moved:' .github/workflows/ci.yml || red "ci.yml still passes moved: to the langpacks action"
! grep -q '@freemixer' ts/package.json || red "ts/package.json is still @freemixer/plugin-db"
! grep -qi 'FREEMIXER' .githooks/commit-msg || red ".githooks/commit-msg still reads the FREEMIXER names"
[ $bad = 0 ] && echo "ok none of the removed compatibility machinery is back"
exit $bad
