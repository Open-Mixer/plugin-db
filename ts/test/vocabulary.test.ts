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

// The sentences a menu shows are plugin-db's own: the source sentence beside the word (omx-contract 3.12 gives a word
// `text`), and its Catalan in catalogs/ca.json keyed <ITEM>.<word> (spec 7.11). Every word of what a menu says (state,
// run, reason, source, record, change, action, bar, standing) has both, so no surface keeps a sentence of its own.
const SAID = ["PLUGIN_DB_STATES", "PLUGIN_DB_RUNS", "PLUGIN_DB_REASONS", "PLUGIN_DB_SOURCES", "PLUGIN_DB_RECORD",
              "PLUGIN_DB_RECORD_CHANGES", "PLUGIN_DB_RECORD_ACTIONS", "PLUGIN_DB_BAR", "PLUGIN_DB_LATENCY"];
const camel = (item: string) => item.slice("PLUGIN_DB_".length).toLowerCase().replace(/_([a-z])/g, (_, c) => c.toUpperCase());
const snake = (n: string) => n.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toUpperCase();
const ca = JSON.parse(readFileSync(new URL("../../catalogs/ca.json", import.meta.url), "utf8"));

test("every word a menu says has its source sentence in the twin's vocabulary, and only that", () => {
  for (const item of SAID) {
    const texts = (v as any)[`${camel(item)}Text`];
    assert.ok(texts, `${item}: no ${camel(item)}Text`);
    for (const w of words(item)) assert.deepEqual(Object.keys(texts[w] ?? {}), ["en"], `${item} ${w}: the source sentence alone`);
  }
  assert.equal(v.reasonsText["measurement-pending"].en, "It has not been measured yet.");
});

test("every word a menu says has its Catalan in catalogs/ca.json under <ITEM>.<word>", () => {
  assert.deepEqual([ca.kind, ca.lang, ca.owner], ["catalog", "ca", "plugin-db"]);
  for (const item of SAID) for (const w of words(item)) assert.ok(ca.messages[`${item}.${w}`], `${item}.${w}: no Catalan`);
});

test("every word a menu says has its source sentence in the C vocabulary header too, and no translation", () => {
  const h = readFileSync(new URL("../../include/plugin-db/plugin_db_vocabulary.h", import.meta.url), "utf8");
  for (const item of SAID) {
    for (const n of Object.keys(data[item].words)) {
      const m = `OMX_${item}_${snake(n)}_TEXT_EN`;
      assert.match(h, new RegExp(`^#define ${m} "`, "m"), m);
    }
  }
  assert.doesNotMatch(h, /_TEXT_CA /);
});
