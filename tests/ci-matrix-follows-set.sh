#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# We build and serve Debian trixie only, never bookworm (owner 2026-11-28; the shared build-deb.yml publishes trixie):
# a bookworm cell installs from a channel that serves nothing for it and turns every pull request red (#104). A workflow
# line that names bookworm outside a comment is refused.
# `ci-matrix-follows-set.sh [workflow...]`; with --self-test it also plants a hand cell and expects red.
set -eu
check() {
  bad=$(awk '/^[[:space:]]*#/ { next } /bookworm/ { print FILENAME ":" FNR ": " $0 }' "$@")
  if [ -n "$bad" ]; then
    printf '%s\n' "$bad" >&2
    echo "FAIL a bookworm cell: we build and serve Debian trixie only (owner 2026-11-28)" >&2
    return 1
  fi
}
self_test=
[ "${1:-}" = --self-test ] && { self_test=1; shift; }
[ $# -gt 0 ] || set -- .github/workflows/*.yml
check "$@"
echo "ok   no workflow names bookworm ($#)"
if [ -n "$self_test" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  printf '    strategy:\n      matrix:\n        image: [%s]\n' "'fedora:45', 'debian:bookworm'" > "$tmp/planted.yml"
  if check "$tmp/planted.yml" 2>/dev/null; then echo "FAIL the self-test's hand bookworm cell passed" >&2; exit 1; fi
  echo "ok   a hand bookworm cell is red"
fi
