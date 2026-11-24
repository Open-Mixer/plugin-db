#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# omx-contract translate over plugin-db's catalogs/ and its words, which are the domain plugin-db (render --with-domain
# reads the items that carry an x-file as the data files they rebuild): the langpacks gate runs it with --check, the fill
# with --lang and --model appended. $OMX_CONTRACT names the omx-contract command (default omx-contract).
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/data"
${OMX_CONTRACT:-omx-contract} translate --data "$tmp/data" --with-domain contract.d/plugin-db --catalogs catalogs --package plugin-db "$@"
