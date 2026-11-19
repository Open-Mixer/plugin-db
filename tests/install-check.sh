#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A scratch install, and a consumer built with only what `pkg-config plugin-db` says of it, its digests compared with
# python's hashlib over the bytes the format's text prescribes and an address read through libplugin-db. And the arms:
# a pc file that does not require libcrypto cannot link the consumer, one without its Libs cannot either, and one
# without its Cflags cannot compile it. The install holds the command and the store's schema.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
PREFIX=$tmp/prefix
make --no-print-directory install PREFIX="$PREFIX" >/dev/null

# The compiler's own system include dirs, each rebuilt as a symlink farm WITHOUT a plugin-db entry where it holds one: a
# build with -nostdinc and these cannot find a plugin-db-devel installed on the host, so the Cflags arm tests the pc
# file's Cflags and not the host's /usr/include.
SHIELD=
n=0
for d in $(cc -E -xc -v /dev/null 2>&1 | sed -n '/^#include <...> search starts here:/,/^End of search list/{/^ /p}'); do
    if [ -e "$d/plugin-db" ]; then
        n=$((n + 1)); mkdir "$tmp/farm$n"
        for e in "$d"/*; do [ "$(basename "$e")" = plugin-db ] || ln -s "$e" "$tmp/farm$n/"; done
        d=$tmp/farm$n
    fi
    SHIELD="$SHIELD -isystem $d"
done

base_pc=${PKG_CONFIG_PATH:-}
build() { # <PKG_CONFIG_PATH> <output> [shield flags]; the caller's own path stays after it
    set -- "$1${base_pc:+:$base_pc}" "$2" "${3:-}"
    # shellcheck disable=SC2046,SC2086 # the flags are words
    PKG_CONFIG_PATH=$1 cc -std=gnu99 -Wall -Wextra -Werror ${3:-} $(PKG_CONFIG_PATH=$1 pkg-config --cflags plugin-db) \
        -o "$2" tests/consumer.c $(PKG_CONFIG_PATH=$1 pkg-config --libs plugin-db) 2>"$tmp/cc.log"
}

pcdir=$PREFIX/lib/pkgconfig
test "$(PKG_CONFIG_PATH=$pcdir pkg-config --modversion plugin-db)" = "$(cat VERSION)"
build "$pcdir" "$tmp/consumer" || { cat "$tmp/cc.log"; echo "FAIL a consumer does not build with pkg-config plugin-db"; exit 1; }

printf 'abc' > "$tmp/fixture"
"$tmp/consumer" "$tmp/fixture" > "$tmp/got"
python3 - "$tmp/got" <<'PY'
import hashlib, sys
want = [hashlib.sha256(b).hexdigest() for b in (
    b"abc",
    b"omx-layout/1 clap\n1\tGain\t0000000000000000\t3ff0000000000000\t3fe0000000000000\t00000001\n",
    b"omx-layout/1 lv2\n0\tgain\tin\t0000000000000000\t3ff0000000000000\t-\thttp://lv2plug.in/ns/lv2core#integer\n",
)]
want.append("lv2")
got = open(sys.argv[1]).read().split()
sys.exit(0 if got == want else print("FAIL the consumer's digests and address", got, want) or 1)
PY

mkdir "$tmp/bad"
sed '/^Requires:/d' "$pcdir/plugin-db.pc" > "$tmp/bad/plugin-db.pc"
if build "$tmp/bad" "$tmp/bad/consumer"; then echo "FAIL a pc file without libcrypto still links the consumer"; exit 1; fi
sed 's/^Requires:.*/Requires: libcrypto/' "$pcdir/plugin-db.pc" > "$tmp/bad/plugin-db.pc"
if build "$tmp/bad" "$tmp/bad/consumer"; then echo "FAIL a pc file without libomx-domain still builds the consumer"; exit 1; fi
sed '/^Libs:/d' "$pcdir/plugin-db.pc" > "$tmp/bad/plugin-db.pc"
if build "$tmp/bad" "$tmp/bad/consumer"; then echo "FAIL a pc file without Libs still links the consumer"; exit 1; fi
sed '/^Cflags:/d' "$pcdir/plugin-db.pc" > "$tmp/bad/plugin-db.pc"
build "$pcdir" "$tmp/shielded" "-nostdinc $SHIELD" || { cat "$tmp/cc.log"; echo "FAIL the shielded build (no host plugin-db headers) does not compile the consumer with the pc file's Cflags"; exit 1; }
if build "$tmp/bad" "$tmp/bad/consumer" "-nostdinc $SHIELD"; then echo "FAIL a pc file without Cflags still compiles the consumer"; exit 1; fi
test -x "$PREFIX/bin/plugin-db" || { echo "FAIL no plugin-db command in the install"; exit 1; }
"$PREFIX/bin/plugin-db" --store "$tmp/store" verify || { echo "FAIL the installed command is red on an empty store"; exit 1; }
test -s "$PREFIX/share/man/man1/plugin-db.1" || { echo "FAIL the command has no manual page"; exit 1; }
cmp -s data/store.schema.json "$PREFIX/share/plugin-db/store.schema.json" || { echo "FAIL the store's schema is not installed"; exit 1; }
echo "ok   install: a consumer builds with only pkg-config plugin-db, its digests are hashlib's, the pc file's lines are needed, the command, its manual page and the schema are installed"
