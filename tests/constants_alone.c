/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* A consumer that needs the length of a digest's hex and nothing of the digest itself (plugin-hostd's command parser,
 * and its fuzz build where no OpenSSL exists): the constants header alone gives it, with no OpenSSL header on the way. */
#include <plugin-db/plugin_db_constants.h>

static char g_hex[OMX_PLUGIN_DB_PIN_SHA256_HEX_LEN + 1];

int main(void)
{
    return (int)sizeof(g_hex) == OMX_PLUGIN_DB_PIN_SHA256_HEX_LEN + 1 ? 0 : 1;
}
