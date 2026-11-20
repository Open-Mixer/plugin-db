/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* The only source that includes plugin-hostd/protocol.h; it includes no header of plugin-db (see pinpath.h). */

#include <plugin-hostd/protocol.h>

#include "pinpath.h"

int pdb_pin_path_encode(const char *path, char *out, size_t size)
{
    return phd_pin_path_encode(path, out, size);
}

int pdb_pin_path_decode(const char *word, char *out, size_t size)
{
    return phd_pin_path_decode(word, out, size);
}
