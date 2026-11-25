/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */

/* The one address form of PLUGIN_DB_ADDRESS_FORMATS: <format>:<id> or <format>@<sha256>:<id>. */

#include <pthread.h>
#include <stdio.h>
#include <string.h>

#include <plugin-db/db.h>

#define FORMAT_WORD_MAX 32

/* the words of PLUGIN_DB_ADDRESS_FORMATS, copied at start-up from the domain; an empty first word is not loaded */
static char g_formats[OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT][FORMAT_WORD_MAX];

int pdb_formats_load(const omx_domain *domain)
{
    char words[OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT][FORMAT_WORD_MAX];
    omx_domain_word_info w;
    int n;

    if (omx_domain_word_count(domain, "PLUGIN_DB_ADDRESS_FORMATS") != (int)OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT)
        return -1;
    for (n = 0; n < (int)OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT; n++)
    {
        if (omx_domain_word_at(domain, "PLUGIN_DB_ADDRESS_FORMATS", n, &w) != 0 || w.code != n || !*w.word ||
            strlen(w.word) >= FORMAT_WORD_MAX)
            return -1;
        memcpy(words[n], w.word, strlen(w.word) + 1);
    }
    memcpy(g_formats, words, sizeof(g_formats));
    return 0;
}

/* the library entry: the installed directory, never OMX_CONTRACT_PATH, opened once whatever the number of threads; what
 * pdb_formats_load already took is kept, and the reason of a failure is kept for pdb_formats_why */
static pthread_once_t g_once = PTHREAD_ONCE_INIT;
static char g_why[320];

static void open_installed(void)
{
    omx_domain *d = NULL;
    omx_domain_error err;

    if (g_formats[0][0])
        return;
    if (omx_domain_open("plugin-db", NULL, &d, &err) != 0)
    {
        snprintf(g_why, sizeof(g_why), "%s: %s", err.code, err.message);
        return;
    }
    if (pdb_formats_load(d) != 0)
        snprintf(g_why, sizeof(g_why), "it does not hold PLUGIN_DB_ADDRESS_FORMATS as two words, in the order of its codes");
    omx_domain_close(d);
}

static int formats_ready(void)
{
    pthread_once(&g_once, open_installed);
    return g_formats[0][0] != '\0';
}

const char *pdb_formats_why(void)
{
    return g_why[0] ? g_why : "no reason: the formats were handed over";
}

const char *pdb_format_word(int format)
{
    return format >= 0 && format < (int)OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT && g_formats[format][0] ? g_formats[format] : "?";
}

const char *pdb_word(const char *const *words, int count, int index)
{
    return index >= 0 && index < count ? words[index] : "?";
}

int pdb_address_parse(const char *text, pdb_address_t *a)
{
    const char *colon = text ? strchr(text, ':') : NULL, *at, *c;
    size_t len;
    int n;

    memset(a, 0, sizeof(*a));
    a->format = -1;
    if (!colon)
        return -1;
    if (!formats_ready())
        return PDB_ERR_FORMATS;
    at = memchr(text, '@', (size_t)(colon - text));
    len = (size_t)((at ? at : colon) - text);
    for (n = 0; n < (int)OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT; n++)
        if (strlen(g_formats[n]) == len && !strncmp(text, g_formats[n], len))
            a->format = n;
    if (a->format < 0)
        return -1;
    /* the bundle rule makes one bundle the plugin, so an LV2 id never needs a pin to tell files apart */
    if (at)
    {
        if (a->format != OMX_PLUGIN_DB_ADDRESS_FORMATS_CLAP || colon - at - 1 != PHD_SHA256_HEX_LEN)
            return -1;
        memcpy(a->pin, at + 1, PHD_SHA256_HEX_LEN);
        a->pin[PHD_SHA256_HEX_LEN] = '\0';
        if (!phd_pin_hex_valid(a->pin))
            return -1;
    }
    a->id = colon + 1;
    if (!*a->id || (a->format == OMX_PLUGIN_DB_ADDRESS_FORMATS_CLAP && a->id[0] == '/'))
        return -1;
    for (c = a->id; *c; c++)
        if ((unsigned char)*c <= 0x20 || *c == 0x7f)
            return -1;
    return 0;
}
