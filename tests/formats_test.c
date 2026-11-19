/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* The address formats are plugin-db's domain item PLUGIN_DB_ADDRESS_FORMATS, read at start-up through the loader:
 *   formats_test unloaded          no format is loaded: the library entry reads the installed directory and never
 *                                  OMX_CONTRACT_PATH, so with that variable naming a good tree an address is still refused
 *   formats_test load <dir> <word> <other>
 *                                  this harness opens <dir> (a test may) and hands the domain to the library: <word>
 *                                  is then an address format (code 1, the second word) and <other> is not */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <plugin-db/db.h>

static int fails;
#define CHECK(c, what) do { if (!(c)) { printf("FAIL %s\n", what); fails++; } } while (0)

static int parses(const char *format, int *code)
{
    char text[128];
    pdb_address_t a;
    int rc;

    snprintf(text, sizeof(text), "%s:http://example.org/amp", format);
    rc = pdb_address_parse(text, &a);
    if (code)
        *code = a.format;
    return rc == 0;
}

int main(int argc, char **argv)
{
    int code = -1;

    if (argc == 2 && !strcmp(argv[1], "unloaded"))
    {
        pdb_address_t a;
        pdb_here_t here;
        pdb_answer_t answer;
        char why[PDB_PATH_MAX];
        const char *valid = "lv2:http://example.org/amp";

        CHECK(!parses("lv2", NULL) && !parses("clap", NULL), "an address is refused when no format was loaded and OMX_CONTRACT_PATH is not read");
        /* the installed domain cannot be read, and the library was handed none: that is its own result, never the one
         * of a text that is no address, and a valid address is never reported invalid or absent */
        CHECK(pdb_address_parse(valid, &a) == PDB_ERR_FORMATS, "a valid address is PDB_ERR_FORMATS when the domain cannot be read");
        CHECK(pdb_address_parse("no-colon-here", &a) == -1, "a text with no format is no address, whatever the domain");
        memset(&here, 0, sizeof(here));
        why[0] = '\0';
        CHECK(pdb_check("/nonexistent-store", valid, &here, NULL, &answer, NULL, why, sizeof(why)) == PDB_ERR_FORMATS &&
              strstr(why, "plugin-db"), "pdb_check passes the domain failure up, naming the domain");
        why[0] = '\0';
        CHECK(pdb_pin("/nonexistent-store", valid, "/nonexistent", NULL, why, sizeof(why)) == PDB_ERR_FORMATS && strstr(why, "plugin-db"),
              "pdb_pin passes the domain failure up, naming the domain");
        why[0] = '\0';
        CHECK(pdb_layer_put("/nonexistent-store", valid, PDB_LAYERS_MEASURED, "t", "{}", why, sizeof(why)) == PDB_ERR_FORMATS &&
              strstr(why, "plugin-db"), "pdb_layer_put passes the domain failure up, naming the domain");
    }
    else if (argc == 5 && !strcmp(argv[1], "load"))
    {
        omx_domain *d = NULL;
        omx_domain_error err;

        if (omx_domain_open_at(argv[2], "plugin-db", "1.0.0", &d, &err) != 0)
        {
            printf("FAIL the harness cannot open %s: %s %s\n", argv[2], err.code, err.message);
            return 1;
        }
        CHECK(pdb_formats_load(d) == 0, "the library takes the formats of the domain");
        omx_domain_close(d);
        CHECK(parses(argv[3], &code) && code == OMX_PLUGIN_DB_ADDRESS_FORMATS_LV2, "the second word of the domain is the LV2 format");
        CHECK(!parses(argv[4], NULL), "a word the domain does not hold is no format");
        CHECK(parses("clap", &code) && code == OMX_PLUGIN_DB_ADDRESS_FORMATS_CLAP, "the first word is the CLAP format");
    }
    else
        return 2;
    if (!fails)
        puts("ok   formats");
    return fails ? 1 : 0;
}
