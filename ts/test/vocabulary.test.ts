// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
// The vocabulary the twin reads is the one data/ declares, in its order, and the bar and the latency standings are
// declared once, here, for plugin-hostd and both surfaces to read.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as v from "../src/vocabulary.ts";

const data = { ...JSON.parse(readFileSync(new URL("../../data/pin.json", import.meta.url), "utf8")),
               ...JSON.parse(readFileSync(new URL("../../data/db.json", import.meta.url), "utf8")) };
const words = (item: string) => Object.values<any>(data[item].words).map((w) => w.word);

test("each words item of data/ is in the vocabulary, its words in their order", () => {
  assert.deepEqual(Object.values(v.states), words("PLUGIN_DB_STATES"));
  assert.deepEqual(Object.values(v.runs), words("PLUGIN_DB_RUNS"));
  assert.deepEqual(Object.values(v.reasons), words("PLUGIN_DB_REASONS"));
  assert.deepEqual(Object.values(v.pinVerdicts), words("PLUGIN_DB_PIN_VERDICTS"));
});

test("the bar's three words are declared once", () => {
  assert.deepEqual(Object.values(v.bar), ["qualified-only", "warn-on-crashes", "load-all"]);
});

test("the latency standings are within, over and unmeasured", () => {
  assert.deepEqual(Object.values(v.latency), ["within", "over", "unmeasured"]);
});

test("a state runs by its group", () => {
  assert.equal(v.statesGroup[v.states.unqualified], v.runs.alone);
  assert.equal(v.statesGroup[v.states.qualified], v.runs.shared);
  assert.equal(v.statesGroup[v.states.refused], v.runs.notLoaded);
});

// The sentences a menu shows are plugin-db's own, beside its words (omx-contract 3.12 gives a word `text`): every
// word of what a menu says (state, run, reason, source, record, change, action, bar, standing) has one in en and ca,
// in the twin's vocabulary and in the C vocabulary header both, so no surface keeps a sentence of its own.
const SAID = ["PLUGIN_DB_STATES", "PLUGIN_DB_RUNS", "PLUGIN_DB_REASONS", "PLUGIN_DB_SOURCES", "PLUGIN_DB_RECORD",
              "PLUGIN_DB_RECORD_CHANGES", "PLUGIN_DB_RECORD_ACTIONS", "PLUGIN_DB_BAR", "PLUGIN_DB_LATENCY"];
const camel = (item: string) => item.slice("PLUGIN_DB_".length).toLowerCase().replace(/_([a-z])/g, (_, c) => c.toUpperCase());
const snake = (n: string) => n.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toUpperCase();

test("every word a menu says has plugin-db's sentence in en and ca, in the twin's vocabulary", () => {
  for (const item of SAID) {
    const texts = (v as any)[`${camel(item)}Text`];
    assert.ok(texts, `${item}: no ${camel(item)}Text`);
    for (const w of words(item)) {
      for (const lang of ["en", "ca"]) assert.ok(texts[w]?.[lang], `${item} ${w}: no ${lang} sentence`);
    }
  }
  assert.equal(v.reasonsText["measurement-pending"].en, "It has not been measured yet.");
});

test("every word a menu says has its sentence in the C vocabulary header too", () => {
  const h = readFileSync(new URL("../../include/plugin-db/plugin_db_vocabulary.h", import.meta.url), "utf8");
  for (const item of SAID) {
    for (const n of Object.keys(data[item].words)) {
      for (const lang of ["EN", "CA"]) {
        const m = `OMX_${item}_${snake(n)}_TEXT_${lang}`;
        assert.match(h, new RegExp(`^#define ${m} "`, "m"), m);
      }
    }
  }
});
