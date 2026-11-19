#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# plugin-hostd-protocol's headers carry their own render of plugin-db's installed vocabulary, which still declares
# OMX_PLUGIN_DB_ADDRESS_FORMATS_* as strings while plugin_db_codes.h declares them as codes. No translation unit of this
# repository may see both: the code that needs the protocol (the pin path codec) is in its own file, which includes no
# header of plugin-db, and the rest reaches it through src/pinpath.h. Separation, not guards: nothing is #undef'd.
#   env: CC, CFLAGS (the flags the build uses, -I of both headers' places)
set -eu
: "${CC:=cc}"
fail=0
for f in src/*.c tests/*.c; do
    # shellcheck disable=SC2086 # the flags are words
    deps=$($CC -MM -Iinclude -Isrc $CFLAGS "$f" 2>/dev/null) || { echo "FAIL $f: the dependencies cannot be read"; fail=1; continue; }
    if printf '%s\n' "$deps" | grep -q "plugin-hostd/protocol.h" && printf '%s\n' "$deps" | grep -q "plugin_db_codes.h"; then
        echo "FAIL $f includes plugin-hostd/protocol.h and plugin_db_codes.h"; fail=1
    fi
done
[ "$fail" = 0 ] || exit 1
echo "ok   no translation unit sees both plugin-hostd/protocol.h and plugin_db_codes.h"
