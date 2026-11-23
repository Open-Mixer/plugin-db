/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of plugin-db.
 *
 * plugin-db is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * plugin-db is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with plugin-db.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/* The plugin database: the one address form, which files are a plugin (the LV2 bundle rule of
 * PLUGIN_DB_BUNDLE_RULES included), the store of layers, and the one state function. libplugin-db.a, on libc and
 * libcrypto; nothing here loads a plugin. The words are data/db.json's (plugin_db_vocabulary.h) and their indexes,
 * the store's layout and the schema's keys are derived from data/ (plugin_db_tables.h). */

#ifndef PLUGIN_DB_DB_H
#define PLUGIN_DB_DB_H

#include <stddef.h>

#include <omxcontract/omx_domain.h>

#include <plugin-db/pin.h>
#include <plugin-db/plugin_db_codes.h>
#include <plugin-db/plugin_db_tables.h>

#define PDB_PATH_MAX 4096

/* ---------------------------------------------------------------- the one address form */

/* <format>:<id>, or clap@<sha256>:<id> when several files share one CLAP id */
typedef struct PDB_ADDRESS_T {
    int format;                         /* OMX_PLUGIN_DB_ADDRESS_FORMATS_* */
    char pin[PHD_SHA256_HEX_LEN + 1];   /* the sha256 of the file of the plugin's code, or "" */
    const char *id;                     /* into the text parsed */
} pdb_address_t;

/* 0; -1 when text is not an address: no format, an unknown format, a pin on an LV2 address or one that is not 64
 * lowercase hex digits, an empty id, a CLAP id that begins with '/' (a path: clap:<path>#<id> is no address) or a byte
 * below 0x21 in the id; or PDB_ERR_FORMATS when the words of the formats could not be read (see pdb_formats_load), in
 * which case nothing is known of text */
int pdb_address_parse(const char *text, pdb_address_t *address);

/* The result of a function of this library that needs the words of the formats when they could not be read: the domain
 * plugin-db is absent, below 1.0.0 or does not hold the formats. It is never the result of an address that is merely
 * wrong (-1): pdb_address_parse, pdb_pin, pdb_layer_put and pdb_check return it, with the reason in why naming the
 * domain, and a caller must not report such an address as invalid or absent. */
#define PDB_ERR_FORMATS (-2)

/* The words of the formats are plugin-db's domain item PLUGIN_DB_ADDRESS_FORMATS, read at start-up through
 * omx-contract's loader, never copied here; the codes (OMX_PLUGIN_DB_ADDRESS_FORMATS_CLAP, _LV2) are the header rendered
 * from the domain. A program opens the domain "plugin-db" (floor 1.0.0) once and hands it over: 0, or -1 when the domain
 * does not hold exactly OMX_PLUGIN_DB_ADDRESS_FORMATS_COUNT words. The library never reads OMX_CONTRACT_PATH: only a
 * command-line program or a test harness may, and it passes the directory to omx_domain_open_at. A program that never
 * hands one over has the library open the installed directory (omx_domain_open) on its first need, once, through
 * pthread_once, so any number of threads may call pdb_address_parse; when that fails the result is PDB_ERR_FORMATS.
 * pdb_formats_load itself is not thread-safe: a threaded program calls it before it starts its threads. Not for an
 * audio thread. */
int pdb_formats_load(const omx_domain *domain);

/* the reason the installed domain could not be read (the loader's code and message), for a message; only meaningful after
 * PDB_ERR_FORMATS */
const char *pdb_formats_why(void);

/* the word of a format code, or "?" */
const char *pdb_format_word(int format);

/* ---------------------------------------------------------------- which files are a plugin */

typedef struct PDB_NAMES_T {
    char **name;
    int n;
} pdb_names_t;

/* what a host loads for a plugin: the root, and each file relative to it as a pin names it (percent-encoded) */
typedef struct PDB_COLLECTION_T {
    char root[PDB_PATH_MAX];
    pdb_names_t files;
} pdb_collection_t;

enum { PDB_COLLECT_OK, PDB_COLLECT_ABSENT, PDB_COLLECT_REFUSED, PDB_COLLECT_ERROR };

/* the bundle of the search path that is the LV2 plugin by PLUGIN_DB_BUNDLE_RULES, malloc'd, or NULL when no bundle
 * names it; a search path is directories joined by ':', a leading "~/" the home directory */
char *pdb_lv2_bundle(const char *search, const char *uri);

/* the files of the plugin at address: for LV2 its bundle in `where`, a search path (NULL: PDB_STORE_LV2_DEFAULT_SEARCH,
 * or LV2_PATH when it is set), the manifest and every file it names for the plugin with lv2:binary or rdfs:seeAlso;
 * for CLAP the file `where`, the .clap the plugin's code is loaded from. PDB_COLLECT_OK; PDB_COLLECT_ABSENT when no
 * bundle names it or the file is gone; PDB_COLLECT_REFUSED when it cannot be pinned (a manifest that sets a base, a name
 * that is no percent-encoded name), with the reason in why; PDB_COLLECT_ERROR when memory runs out */
int pdb_collect(const pdb_address_t *address, const char *where, pdb_collection_t *out, char *why, size_t why_size);
void pdb_collection_free(pdb_collection_t *collection);

/* ---------------------------------------------------------------- the store */

/* the store's directory: $PLUGIN_DB_STORE, else the system's for a system service, else the user's under
 * $XDG_STATE_HOME (or ~/.local/state); 0, or -1 when it does not fit or there is no home */
int pdb_store_default(int system, char *out, size_t size);

/* the layer written for the current pin: the files pin and the layout of the entry's pinned layer, which must be
 * there (except to write the pinned layer itself, which pdb_pin does). 0, or -1 with the reason in why: no pinned
 * layer, a body that is not a JSON object or lacks a field the schema requires of its layer, a layer outside
 * PLUGIN_DB_LAYERS, or the file could not be written and renamed; PDB_ERR_FORMATS when the formats could not be read */
int pdb_layer_put(const char *store, const char *address, int layer, const char *writer, const char *body, char *why,
                  size_t why_size);

/* collect the plugin's files, hash them and write the entry's pinned layer, with layout ("<scheme>:<sha256>") or
 * NULL when no host has found it yet. 0, or -1 with the reason in why; PDB_ERR_FORMATS when the formats could not be read */
int pdb_pin(const char *store, const char *address, const char *where, const char *layout, char *why, size_t why_size);

/* ---------------------------------------------------------------- the state */

/* the facts of here a record is compared with; NULL or -1 is not known here, which no record matches */
typedef struct PDB_HERE_T {
    const char *machine_class;
    const char *host_name, *host_version;
    long hosting_epoch;
    const char *rules, *record_schema;
    long rate, quantum;
    const char *const *facts;           /* "<key>=<value>", each a condition a record may require */
    int nfacts;
} pdb_here_t;

/* a record as the state function reads it: the judged layer, or a shipped one from the reference layer */
typedef struct PDB_RECORD_T {
    int present;
    int pin_files, pin_layout;          /* it was written for the pinned files, and for the pinned layout */
    int verdict;                        /* PDB_PIN_VERDICTS_*, -1 for a word that is none */
    const char *machine_class;
    const char *host_name, *host_version;
    long hosting_epoch;
    const char *rules, *record_schema;
    const long (*cells)[2];             /* rate, quantum */
    int ncells;
    const char *const *conditions;      /* "<key>=<value>" */
    int nconditions;
} pdb_record_t;

typedef struct PDB_STATE_IN_T {
    int pinned;                         /* there is a pinned layer */
    int files, layout;                  /* PDB_FILES_*, PDB_LAYOUT_* */
    pdb_record_t local, reference;
    int warned_override;                /* a warned override written for the pinned files */
} pdb_state_in_t;

typedef struct PDB_ANSWER_T {
    int files, layout, record;          /* PDB_FILES_*, PDB_LAYOUT_*, PDB_RECORD_* */
    int change, action;                 /* PDB_RECORD_CHANGES_* and PDB_RECORD_ACTIONS_* of the local record, or -1 */
    int state, runs, reason, source;    /* PDB_STATES_*, PDB_RUNS_*, PDB_REASONS_*, PDB_SOURCES_* */
} pdb_answer_t;

/* THE state function: what the plugin is, from its attributes, its records and a warned override, here. No reader
 * computes this for itself. */
void pdb_state(const pdb_state_in_t *in, const pdb_here_t *here, pdb_answer_t *out);

/* THE door of pdb_state: a NULL in, here or out, an enum outside its declared range (files, layout, a record's verdict
 * but -1, which is a word that is none), a present record with no host name, or cells/conditions NULL with a count above 0 is
 * REFUSED: never a crash, an abort or a table read past its end, and counted here. A refused call with an out answers
 * state unqualified (it runs nothing), source none, reason could-not-test. The count since the process began. */
long pdb_state_refusals(void);

/* what show and verify print beside the answer */
typedef struct PDB_DETAIL_T {
    char address[PDB_PATH_MAX];         /* the entry's, resolved */
    char entry[PDB_PATH_MAX];
    char root[PDB_PATH_MAX];
    char layout[128];
    char problem[PDB_PATH_MAX];         /* the first thing the check found, or "" */
    char verdict[16];
    char machine_class[64], host_name[64], host_version[64];
    /* the figures of the answering record at the rate and quantum here: has_cell is 0 when no record answers or it
     * has no cell here; a record without latencyMs or latencyLineMs has no figure or no line, and standing says so */
    int has_cell, has_latency, has_line;
    long rate, quantum;
    double latency_ms, line_ms;
    int standing;                       /* PDB_LATENCY_* */
} pdb_detail_t;

/* where a figure stands against the line: unmeasured when either is missing, never a guess */
int pdb_latency_standing(int has_latency, double latency_ms, int has_line, double line_ms);

/* the check of one entry: its pinned files collected and hashed again, its layout against current_layout (what a host
 * found, or NULL), its records, then pdb_state. 0, or -1 when address is no address or names no entry (why says
 * which, and that a CLAP id several entries share needs its pin); PDB_ERR_FORMATS when the formats could not be read,
 * which says nothing of the address. detail may be NULL */
int pdb_check(const char *store, const char *address, const pdb_here_t *here, const char *current_layout,
              pdb_answer_t *out, pdb_detail_t *detail, char *why, size_t why_size);

/* each entry's address in the store, in byte order of the entries' names, to fn; the count, or -1 when the store
 * cannot be read. fn returns nonzero to stop */
int pdb_entries(const char *store, int (*fn)(void *ctx, const char *address), void *ctx);

/* the word of an index of a words item, or "?" */
const char *pdb_word(const char *const *words, int count, int index);

#endif
