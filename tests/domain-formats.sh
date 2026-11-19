#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# plugin-db publishes its address formats (clap, lv2) as a domain item the omx-contract loader opens: the installed tree
# holds contract.d/plugin-db/plugin-db.json, the loader (omx-domain, over omx_domain_open_at) opens it and lists
# clap and lv2 in PLUGIN_DB_ADDRESS_FORMATS, and `make check-domain` is red on a domain file that is missing or stale.
# data/db.json stays the one source; the domain file is what tools/render-domain.py derives from it.
#   env: INSTALL_CONTRACT_DIR (install-contract-dir.sh, 3.20.0 or later), OMX_DOMAIN (the omx-domain command)
set -eu
: "${MAKE:=make}"
: "${OMX_DOMAIN:=omx-domain}"
[ -n "${INSTALL_CONTRACT_DIR:-}" ] || { echo "FAIL domain-formats: INSTALL_CONTRACT_DIR is not set: no install-contract-dir.sh" >&2; exit 1; }
command -v "$OMX_DOMAIN" >/dev/null || { echo "FAIL domain-formats: no $OMX_DOMAIN command: install libomx-domain (3.20.0 or later)" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fresh() { rm -rf "$tmp/t"; mkdir "$tmp/t"; cp -r Makefile VERSION data tools contract.d "$tmp/t/" 2>/dev/null || true; }

# the installed tree holds the domain, and the loader opens it
mkdir -p "$tmp/dest/contractdir"
sh "$INSTALL_CONTRACT_DIR" --domain contract.d/plugin-db "$tmp/dest/contractdir"
test -f "$tmp/dest/contractdir/plugin-db/plugin-db.json" || { echo "FAIL the installed tree has no plugin-db/plugin-db.json"; exit 1; }
words=$(OMX_CONTRACT_PATH="$tmp/dest/contractdir" "$OMX_DOMAIN" plugin-db "" PLUGIN_DB_ADDRESS_FORMATS) \
  || { echo "FAIL the loader does not open plugin-db"; exit 1; }
for w in clap lv2; do
  printf '%s\n' "$words" | grep -q "^word=$w " || { echo "FAIL PLUGIN_DB_ADDRESS_FORMATS lacks $w: $words"; exit 1; }
done
[ "$(printf '%s\n' "$words" | wc -l)" -eq 2 ] || { echo "FAIL PLUGIN_DB_ADDRESS_FORMATS is not exactly clap and lv2: $words"; exit 1; }

# the gate: green on a clean tree, red on a missing file and on a stale one
fresh
$MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null || { echo "FAIL check-domain is red on a clean tree"; exit 1; }
fresh
rm "$tmp/t/contract.d/plugin-db/plugin-db.json"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL a missing domain file stays green"; exit 1; fi
fresh
sed -i 's/"const": "lv2"/"const": "lv-2"/' "$tmp/t/contract.d/plugin-db/plugin-db.json"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL a domain file changed by hand stays green"; exit 1; fi
fresh
sed -i 's/"word": "lv2"/"word": "lv3"/' "$tmp/t/data/db.json"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL data/db.json changed and not rendered again stays green"; exit 1; fi
echo "ok   domain formats: installed, opened by the loader, clap and lv2; check-domain red on missing, stale and unrendered"
