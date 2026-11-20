/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */

/* The door of pdb_state (contracts audit 2026-11-16, row 11): a NULL pointer or an enum outside its declared range is
 * REFUSED, by name and counted, and never crashes, aborts or indexes a table past its end. The refusal's answer runs
 * nothing: state unqualified, source none, reason could-not-test. */

#include <stdio.h>
#include <string.h>

#include <plugin-db/db.h>

static const long g_cells[][2] = { { 48000, 128 } };
static const char *const g_conditions[] = { "cpu=cortex-a76" };

static void good(pdb_state_in_t *in, pdb_here_t *h)
{
    pdb_record_t r = { 1, 1, 1, PDB_PIN_VERDICTS_IN_PROCESS, "rpi5", "plugin-hostd", "1.4.0", 2, "rules-7", "record-3",
                       g_cells, 1, g_conditions, 1 };
    static const char *const facts[] = { "cpu=cortex-a76" };
    pdb_here_t here = { "rpi5", "plugin-hostd", "1.4.0", 2, "rules-7", "record-3", 48000, 128, facts, 1 };

    memset(in, 0, sizeof(*in));
    in->pinned = 1;
    in->files = PDB_FILES_SAME;
    in->layout = PDB_LAYOUT_SAME;
    in->local = r;
    *h = here;
}

static int fail;

static void refused(const char *what, const pdb_state_in_t *in, const pdb_here_t *h, pdb_answer_t *out)
{
    long before = pdb_state_refusals();
    pdb_state(in, h, out);
    if (pdb_state_refusals() != before + 1)
    {
        printf("FAIL %s: not counted as a refusal\n", what);
        fail = 1;
        return;
    }
    if (out && (out->state != PDB_STATES_UNQUALIFIED || out->reason != PDB_REASONS_COULD_NOT_TEST ||
                out->source != PDB_SOURCES_NONE))
    {
        printf("FAIL %s: refused with the wrong answer\n", what);
        fail = 1;
        return;
    }
    printf("ok   %s is refused and counted\n", what);
}

int main(void)
{
    pdb_state_in_t in;
    pdb_here_t here;
    pdb_answer_t out;
    long before;

    good(&in, &here);
    before = pdb_state_refusals();
    pdb_state(&in, &here, &out);
    if (pdb_state_refusals() != before) { printf("FAIL a good input is counted as a refusal\n"); fail = 1; }

    refused("a NULL input", NULL, &here, &out);
    refused("a NULL here", &in, NULL, &out);
    refused("a NULL answer", &in, &here, NULL);
    good(&in, &here); in.files = PDB_FILES_COUNT;     refused("files one past its range", &in, &here, &out);
    good(&in, &here); in.files = -1;                  refused("files below its range", &in, &here, &out);
    good(&in, &here); in.layout = PDB_LAYOUT_COUNT;   refused("layout one past its range", &in, &here, &out);
    good(&in, &here); in.layout = 1000;               refused("layout far past its range", &in, &here, &out);
    good(&in, &here); in.local.verdict = PDB_PIN_VERDICTS_COUNT; refused("a local verdict past its range", &in, &here, &out);
    good(&in, &here); in.reference = in.local; in.reference.verdict = -2; refused("a reference verdict below -1", &in, &here, &out);
    good(&in, &here); in.local.cells = NULL;          refused("cells NULL with ncells > 0", &in, &here, &out);
    good(&in, &here); in.local.conditions = NULL;     refused("conditions NULL with nconditions > 0", &in, &here, &out);
    good(&in, &here); in.local.host_name = NULL;      refused("a present record with no host name", &in, &here, &out);
    good(&in, &here); in.local.verdict = -1;          /* -1 is a word that is none: in range */
    before = pdb_state_refusals();
    pdb_state(&in, &here, &out);
    if (pdb_state_refusals() != before) { printf("FAIL verdict -1 is refused\n"); fail = 1; }
    if (fail) return 1;
    printf("ok   state door: NULLs and out-of-range enums are refused, a good input and a none verdict pass\n");
    return 0;
}
