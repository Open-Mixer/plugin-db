#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# plugin-db owns the domain `plugin-db`, hand-kept in contract.d/plugin-db/plugin-db.json, and its item
# PLUGIN_DB_ADDRESS_FORMATS (clap, lv2) lives only there: data/db.json no longer declares it, the C that switches on
# a format reads the codes header rendered from the domain, and the format words are read at start-up through the
# loader (omx-contract's docs/consumer-move.md).
#   env: INSTALL_CONTRACT_DIR (install-contract-dir.sh, 3.20.0 or later), OMX_DOMAIN (the omx-domain command),
#        OMX_CONTRACT (the omx-contract command), PDB (the plugin-db command), FORMATS_TEST (tests/formats_test.c, built)
set -eu
: "${MAKE:=make}"
: "${OMX_DOMAIN:=omx-domain}"
: "${OMX_CONTRACT:=omx-contract}"
for v in INSTALL_CONTRACT_DIR PDB FORMATS_TEST; do
  eval "[ -n \"\${$v:-}\" ]" || { echo "FAIL domain-formats: $v is not set" >&2; exit 1; }
done
command -v "$OMX_DOMAIN" >/dev/null || { echo "FAIL domain-formats: no $OMX_DOMAIN command: install libomx-domain-devel (3.20.0 or later)" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
bad() { echo "FAIL $1"; exit 1; }
fresh() { rm -rf "$tmp/t"; mkdir "$tmp/t"; cp -r Makefile VERSION data tools contract.d include "$tmp/t/"; }

# the domain is the source: hand-kept, not rendered, and the classic item is gone
test ! -e tools/render-domain.py || bad "tools/render-domain.py still derives the domain"
! grep -q "render-domain\|check-domain" Makefile || bad "the Makefile still renders or checks a derived domain"
python3 - <<'P' || bad "the domain document is not the source of PLUGIN_DB_ADDRESS_FORMATS"
import json, sys
db = json.load(open("data/db.json"))
if "PLUGIN_DB_ADDRESS_FORMATS" in db:
    sys.exit("data/db.json still declares PLUGIN_DB_ADDRESS_FORMATS")
doc = json.load(open("contract.d/plugin-db/plugin-db.json"))
item = doc["components"]["schemas"]["PLUGIN_DB_ADDRESS_FORMATS"]
if doc["info"]["version"] != "1.0.0" or item.get("x-since") != "1.0.0":
    sys.exit("the domain's own version is 1.0.0 and the item's x-since 1.0.0")
if item.get("x-c-codes") is not True:
    sys.exit("the item is not marked x-c-codes: C switches on its words")
if [w["const"] for w in item["oneOf"]] != ["clap", "lv2"]:
    sys.exit("the words are not clap and lv2")
P
$OMX_CONTRACT fmt --check --contract-dir contract.d >/dev/null || bad "the domain is not in the one formatting"
$OMX_CONTRACT validate --contract-dir contract.d >/dev/null || bad "the domain does not validate"

# the installed tree holds the domain, and the loader opens it
mkdir -p "$tmp/dest/contractdir"
sh "$INSTALL_CONTRACT_DIR" --domain contract.d/plugin-db "$tmp/dest/contractdir" >/dev/null
test -f "$tmp/dest/contractdir/plugin-db/plugin-db.json" || bad "the installed tree has no plugin-db/plugin-db.json"
words=$(OMX_CONTRACT_PATH="$tmp/dest/contractdir" "$OMX_DOMAIN" plugin-db "" PLUGIN_DB_ADDRESS_FORMATS) || bad "the loader does not open plugin-db"
for w in clap lv2; do
  printf '%s\n' "$words" | grep -q "^word=$w " || bad "PLUGIN_DB_ADDRESS_FORMATS lacks $w: $words"
done
[ "$(printf '%s\n' "$words" | wc -l)" -eq 2 ] || bad "PLUGIN_DB_ADDRESS_FORMATS is not exactly clap and lv2: $words"

# no vocabulary render of the item, and no second header: C reads the codes header of the domain
! grep -q "ADDRESS_FORMATS" include/plugin-db/plugin_db_vocabulary.h || bad "plugin_db_vocabulary.h still renders the formats"
! grep -rq "PDB_ADDRESS_FORMATS\|OMX_PLUGIN_DB_ADDRESS_FORMATS_INIT" src include tests/*.c || bad "an old name of the formats is still used"
test -f include/plugin-db/plugin_db_codes.h || bad "no codes header of the domain"
n=$(grep "^#define OMX_" include/plugin-db/plugin_db_codes.h | grep -vc "_CODES_H$")
[ "$(grep -c "^#define OMX_PLUGIN_DB_ADDRESS_FORMATS_" include/plugin-db/plugin_db_codes.h)" -eq "$n" ] && [ "$n" -gt 0 ] || bad "the codes header holds more than the x-c-codes item"
$MAKE --no-print-directory check-codes >/dev/null || bad "check-codes is red on a clean tree"
fresh
sed -i 's/ADDRESS_FORMATS_LV2 1u/ADDRESS_FORMATS_LV2 7u/' "$tmp/t/include/plugin-db/plugin_db_codes.h"
if $MAKE --no-print-directory -C "$tmp/t" check-codes >/dev/null 2>&1; then bad "a codes header changed by hand stays green"; fi
fresh
sed -i 's/"const": "lv2"/"const": "lv3"/' "$tmp/t/contract.d/plugin-db/plugin-db.json"
$OMX_CONTRACT validate --contract-dir "$tmp/t/contract.d" >/dev/null || bad "the fixture domain does not validate"

# the classic item put back beside the domain is refused by name: one item, one declaration (omx-contract's reader skips
# a domain that has the name of an installed package, so it cannot say so itself)
fresh
python3 - "$tmp/t" <<'P'
import json, sys
p = sys.argv[1] + "/data/db.json"
d = json.load(open(p))
d["PLUGIN_DB_ADDRESS_FORMATS"] = {"kind": "words", "since": "0.2.0", "doc": "again", "words": {"clap": {"word": "clap", "doc": "x"}}}
json.dump(d, open(p, "w"), indent=2)
P
if out=$($MAKE --no-print-directory -C "$tmp/t" check-codes 2>&1); then bad "the classic item beside the domain stays green"; fi
printf '%s\n' "$out" | grep -q "PLUGIN_DB_ADDRESS_FORMATS is declared by" || bad "the classic item beside the domain is refused, but not by name: $out"

# the words are read at start-up: a fixture directory with one word changed reaches the command and the library
fixture="$tmp/fx"
mkdir -p "$fixture"
cp -r contract.d/plugin-db "$fixture/"
sed -i 's/"const": "lv2"/"const": "lv3"/' "$fixture/plugin-db/plugin-db.json"
store="$tmp/store"
AMP=http://example.org/plugins/amp
real=$(OMX_CONTRACT_PATH="$PWD/contract.d" "$PDB" --store "$store" show "lv2:$AMP" 2>&1 || true)
printf '%s\n' "$real" | grep -q "has no entry" || bad "the command does not read lv2 from the domain: $real"
changed=$(OMX_CONTRACT_PATH="$fixture" "$PDB" --store "$store" show "lv3:$AMP" 2>&1 || true)
printf '%s\n' "$changed" | grep -q "has no entry" || bad "the command does not see the changed word: $changed"
old=$(OMX_CONTRACT_PATH="$fixture" "$PDB" --store "$store" show "lv2:$AMP" 2>&1 || true)
printf '%s\n' "$old" | grep -q "is no address" || bad "the command still accepts the old word: $old"
"$FORMATS_TEST" load "$fixture" lv3 lv2 >/dev/null || bad "the library does not see the changed word"
OMX_CONTRACT_PATH="$PWD/contract.d" "$FORMATS_TEST" unloaded >/dev/null || bad "the library entry read OMX_CONTRACT_PATH"

# an absent or too-old domain is refused by name at start-up, exit 78
mkdir "$tmp/empty"
rc=0; out=$(OMX_CONTRACT_PATH="$tmp/empty" "$PDB" --store "$store" show "lv2:$AMP" 2>&1) || rc=$?
[ "$rc" = 78 ] && printf '%s\n' "$out" | grep -q "plugin-db" || bad "an absent domain is not refused by name with 78 ($rc): $out"
mkdir -p "$tmp/old"
cp -r contract.d/plugin-db "$tmp/old/"
sed -i 's/"version": "1.0.0"/"version": "0.9.0"/' "$tmp/old/plugin-db/plugin-db.json"
rc=0; out=$(OMX_CONTRACT_PATH="$tmp/old" "$PDB" --store "$store" show "lv2:$AMP" 2>&1) || rc=$?
[ "$rc" = 78 ] && printf '%s\n' "$out" | grep -q "too-old" || bad "a too-old domain is not refused by name with 78 ($rc): $out"

echo "ok   domain formats: the domain is the source, installed, opened by the loader; the codes header and the start-up read hold; an absent, too-old or doubled domain is refused"
