#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
# plugin-db is the owner of its domains (#84): make install-contract writes <contractdir>/3/plugin-db/MANIFEST.json,
# the package's version and the four domains it installs, so a domain that requires plugin-db >= <version> reads the
# package as installed; and omx-contract reads the directory with the manifest beside its domains, none of them hidden.
#   sh tests/owner-manifest.sh     needs omx-contract (3.22.0 or later reads a domain named like its package as its own)
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
ok() { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=1; }
make -C "$here" --no-print-directory install-contract DESTDIR="$tmp" >/dev/null
cdir=$(make -C "$here" --no-print-directory -s print-contractdir)
m=$tmp$cdir/3/plugin-db/MANIFEST.json
if [ -f "$m" ]; then ok "install-contract writes 3/plugin-db/MANIFEST.json"; else bad "install-contract writes no 3/plugin-db/MANIFEST.json"; fi
if [ -f "$m" ]; then
  got=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["package"], d["version"], " ".join(sorted(d.get("domains", []))))' "$m")
  want="plugin-db $(cat "$here/VERSION") format lv2 plugin-db plugin-feature"
  [ "$got" = "$want" ] && ok "the manifest names plugin-db $(cat "$here/VERSION") and its four domains" || bad "the manifest is '$got', not '$want'"
fi
# read back: every domain is still read beside the manifest (an old reader hides the domain named like its package)
if command -v omx-contract >/dev/null; then
  out=$(OMX_CONTRACT_PATH="$tmp$cdir:$cdir" omx-contract validate --installed 2>&1) && ok "omx-contract validates the directory with the manifest" \
    || { echo "$out" | tail -5; bad "omx-contract refuses the directory with the manifest"; }
else
  bad "no omx-contract command"
fi
exit $fail
