#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# check-rendered must fail on a rendered header changed by hand, and on the domain plugin-db changed and not rendered again.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fresh() { rm -rf "$tmp/t"; mkdir "$tmp/t"; cp -r Makefile VERSION data include contract.d "$tmp/t/"; }
# plant <file> <sed expression>: the edit must change the file, so an arm never passes on a word that is no longer there
plant() { cp "$tmp/t/$1" "$tmp/before"; sed -i "$2" "$tmp/t/$1"; ! cmp -s "$tmp/before" "$tmp/t/$1" || { echo "FAIL the sabotage $2 changes nothing in $1"; exit 1; }; }

fresh
make --no-print-directory -C "$tmp/t" check-rendered >/dev/null || { echo "FAIL check-rendered is red on a clean tree"; exit 1; }
fresh
# a word of plugin-db's own pin file format (PLUGIN_DB_PIN_LAYOUT_FORMATS)
plant include/plugin-db/plugin_db_vocabulary.h 's/_CLAP "clap"/_CLAP "klap"/'
if make --no-print-directory -C "$tmp/t" check-rendered >/dev/null 2>&1; then echo "FAIL a header changed by hand stays green"; exit 1; fi
fresh
plant contract.d/plugin-db/plugin-db.json 's/"const": "files"/"const": "bytes"/'
if make --no-print-directory -C "$tmp/t" check-rendered >/dev/null 2>&1; then echo "FAIL the domain not rendered again stays green"; exit 1; fi
echo "ok   rendered sabotage: a header changed by hand and the domain not rendered are red"
