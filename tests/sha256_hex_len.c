/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* The declared length of a digest's hex is two characters a byte of OpenSSL's SHA-256, and pin.h's name says the same. */
#include <openssl/sha.h>

#include <plugin-db/pin.h>

_Static_assert(OMX_PLUGIN_DB_PIN_SHA256_HEX_LEN == 2 * SHA256_DIGEST_LENGTH, "the hex of a SHA-256 digest");
_Static_assert(PHD_SHA256_HEX_LEN == OMX_PLUGIN_DB_PIN_SHA256_HEX_LEN, "pin.h names the declared length");

int main(void)
{
    return 0;
}
