/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* The pin path codec of plugin-hostd-protocol, reached through this one file. plugin-hostd-protocol's headers carry their
 * own render of plugin-db's installed vocabulary, whose address format macros are strings where plugin_db_codes.h's are
 * codes: a source that includes plugin-hostd/protocol.h includes no header of plugin-db (tests/tu-split.sh holds it), so
 * the rest of the library calls these two functions and sees only plain C types. */
#ifndef PDB_PINPATH_H
#define PDB_PINPATH_H

#include <stddef.h>

/* phd_pin_path_encode: 0, or -1 when out is too small or path is no path */
int pdb_pin_path_encode(const char *path, char *out, size_t size);
/* phd_pin_path_decode: 0, or -1 when word is no pin word or out is too small */
int pdb_pin_path_decode(const char *word, char *out, size_t size);

#endif
