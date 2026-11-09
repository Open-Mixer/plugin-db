// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
// GENERATED: DO NOT EDIT BY HAND.
// Produced by tools/render-ts.py from data/pin.json and data/db.json. Each words item is an object of its words in
// their order, keyed as data/ keys them; a grouped item has a <item>Group object (the group word of each word).

/** PLUGIN_DB_PIN_VERDICTS */
export const pinVerdicts = {
  inProcess: "in-process",
  isolated: "isolated",
  refused: "refused",
} as const;

/** PLUGIN_DB_PIN_POOLS */
export const pinPools = {
  cores: "cores",
  off: "off",
} as const;

/** PLUGIN_DB_PIN_KEYS */
export const pinKeys = {
  verdict: "verdict",
  pool: "pool",
} as const;

/** PLUGIN_DB_PIN_CHANGES */
export const pinChanges = {
  files: "files",
  layout: "layout",
} as const;

/** PLUGIN_DB_PIN_LAYOUT_FORMATS */
export const pinLayoutFormats = {
  clap: "clap",
  lv2: "lv2",
} as const;

/** PLUGIN_DB_ADDRESS_FORMATS */
export const addressFormats = {
  clap: "clap",
  lv2: "lv2",
} as const;

/** PLUGIN_DB_BUNDLE_RULES */
export const bundleRules = {
  newestVersion: "newest-version",
} as const;

/** PLUGIN_DB_LAYERS */
export const layers = {
  declared: "declared",
  scanned: "scanned",
  pinned: "pinned",
  measured: "measured",
  judged: "judged",
  reference: "reference",
  corrected: "corrected",
  warnedOverride: "warned-override",
  observed: "observed",
} as const;

/** PLUGIN_DB_FILES */
export const files = {
  same: "same",
  changed: "changed",
  absent: "absent",
  couldNotTest: "could-not-test",
} as const;

/** PLUGIN_DB_LAYOUT */
export const layout = {
  same: "same",
  changed: "changed",
  notYetKnown: "not-yet-known",
} as const;

/** PLUGIN_DB_RECORD */
export const record = {
  current: "current",
  stale: "stale",
  none: "none",
} as const;
/** the owners' text of each word of PLUGIN_DB_RECORD, en and ca */
export const recordText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"current": {"en": "Its record is current."}, "stale": {"en": "Its record no longer applies."}, "none": {"en": "It has no record."}};

/** PLUGIN_DB_RECORD_ACTIONS */
export const recordActions = {
  fullPath: "full-path",
  measureHere: "measure-here",
  convert: "convert",
  rejudge: "rejudge",
  remeasureBackground: "remeasure-background",
} as const;
/** the owners' text of each word of PLUGIN_DB_RECORD_ACTIONS, en and ca */
export const recordActionsText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"full-path": {"en": "Scan, measure and judge it again."}, "measure-here": {"en": "Measure it on this machine."}, "convert": {"en": "Convert the record; nothing is measured again."}, "rejudge": {"en": "Judge the measurements again; nothing is measured again."}, "remeasure-background": {"en": "The record still applies; it is measured again in the background."}};

/** PLUGIN_DB_RECORD_CHANGES */
export const recordChanges = {
  files: "files",
  layout: "layout",
  hostingChange: "hosting-change",
  machineClass: "machine-class",
  schema: "schema",
  rules: "rules",
  hostVersion: "host-version",
} as const;
/** the owners' text of each word of PLUGIN_DB_RECORD_CHANGES, en and ca */
export const recordChangesText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"files": {"en": "Its files changed."}, "layout": {"en": "Its parameters changed."}, "hosting-change": {"en": "The host changed how it hosts plugins."}, "machine-class": {"en": "This is another kind of machine."}, "schema": {"en": "The record format changed."}, "rules": {"en": "The qualification rules changed."}, "host-version": {"en": "The host is another release."}};

/** PLUGIN_DB_STATES */
export const states = {
  unqualified: "unqualified",
  qualified: "qualified",
  isolatedOnly: "isolated-only",
  conditionsUnmet: "conditions-unmet",
  refused: "refused",
  absent: "absent",
} as const;
/** the owners' text of each word of PLUGIN_DB_STATES, en and ca */
export const statesText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"unqualified": {"en": "Not qualified: it runs alone, in a worker of its own."}, "qualified": {"en": "Qualified: it runs as its record allows."}, "isolated-only": {"en": "Qualified to run alone only."}, "conditions-unmet": {"en": "Its record does not cover this machine's settings: it runs alone."}, "refused": {"en": "Refused: it is not loaded."}, "absent": {"en": "Its files are gone: it is not loaded."}};

/** PLUGIN_DB_RUNS */
export const runs = {
  shared: "shared",
  alone: "alone",
  notLoaded: "not-loaded",
} as const;
/** the owners' text of each word of PLUGIN_DB_RUNS, en and ca */
export const runsText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"shared": {"en": "Runs in a shared worker."}, "alone": {"en": "Runs alone, in a worker of its own."}, "not-loaded": {"en": "Not loaded: an effect passes audio through, an instrument is silent."}};

/** PLUGIN_DB_REASONS */
export const reasons = {
  neverPinned: "never-pinned",
  measurementPending: "measurement-pending",
  couldNotTest: "could-not-test",
  filesChanged: "files-changed",
  layoutChanged: "layout-changed",
  layoutNotYetKnown: "layout-not-yet-known",
  recordStale: "record-stale",
  notMeasuredUnderHost: "not-measured-under-host",
  verdictAllows: "verdict-allows",
  verdictIsolated: "verdict-isolated",
  referenceOnly: "reference-only",
  noCell: "no-cell",
  conditionFails: "condition-fails",
  recordRefused: "record-refused",
  shippedRefusal: "shipped-refusal",
  filesGone: "files-gone",
} as const;
/** the owners' text of each word of PLUGIN_DB_REASONS, en and ca */
export const reasonsText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"never-pinned": {"en": "It has never been scanned."}, "measurement-pending": {"en": "It has not been measured yet."}, "could-not-test": {"en": "Its files could not be read."}, "files-changed": {"en": "Its files have changed since they were scanned."}, "layout-changed": {"en": "Its parameters have changed since they were scanned."}, "layout-not-yet-known": {"en": "Its parameters are not known yet."}, "record-stale": {"en": "Its record no longer applies and it needs measuring again."}, "not-measured-under-host": {"en": "Its record says alone, but it was not measured under plugin-hostd."}, "verdict-allows": {"en": "Its record allows a shared worker."}, "verdict-isolated": {"en": "Its record says it is safe only alone."}, "reference-only": {"en": "Measured on another kind of machine: reference figures only."}, "no-cell": {"en": "Its record has no measurement at this rate and quantum."}, "condition-fails": {"en": "A condition of its record does not hold on this machine."}, "record-refused": {"en": "Its record says refused."}, "shipped-refusal": {"en": "These files are refused by the record shipped with them."}, "files-gone": {"en": "Its files are gone."}};

/** PLUGIN_DB_ISOLATION_HOSTS */
export const isolationHosts = {
  pluginHostd: "plugin-hostd",
} as const;

/** PLUGIN_DB_SOURCES */
export const sources = {
  none: "none",
  local: "local",
  reference: "reference",
} as const;
/** the owners' text of each word of PLUGIN_DB_SOURCES, en and ca */
export const sourcesText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"none": {"en": "No record."}, "local": {"en": "Measured on this machine."}, "reference": {"en": "Measured on a reference machine."}};

/** PLUGIN_DB_BAR */
export const bar = {
  qualifiedOnly: "qualified-only",
  warnOnCrashes: "warn-on-crashes",
  loadAll: "load-all",
} as const;
/** the owners' text of each word of PLUGIN_DB_BAR, en and ca */
export const barText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"qualified-only": {"en": "Offer qualified plugins only."}, "warn-on-crashes": {"en": "Offer every plugin that is not refused; ask only after a crash."}, "load-all": {"en": "Offer every plugin, refused ones included."}};

/** PLUGIN_DB_LATENCY */
export const latency = {
  within: "within",
  over: "over",
  unmeasured: "unmeasured",
} as const;
/** the owners' text of each word of PLUGIN_DB_LATENCY, en and ca */
export const latencyText: Readonly<Record<string, Readonly<Record<string, string>>>> = {"within": {"en": "Latency within the line."}, "over": {"en": "Latency over the line; it still loads."}, "unmeasured": {"en": "Latency not measured."}};

/** the PLUGIN_DB_RECORD word of each word of PLUGIN_DB_RECORD_ACTIONS */
export const recordActionsGroup = {
  [recordActions.fullPath]: record.stale,
  [recordActions.measureHere]: record.stale,
  [recordActions.convert]: record.stale,
  [recordActions.rejudge]: record.stale,
  [recordActions.remeasureBackground]: record.current,
} as const;

/** the PLUGIN_DB_RECORD_ACTIONS word of each word of PLUGIN_DB_RECORD_CHANGES */
export const recordChangesGroup = {
  [recordChanges.files]: recordActions.fullPath,
  [recordChanges.layout]: recordActions.fullPath,
  [recordChanges.hostingChange]: recordActions.fullPath,
  [recordChanges.machineClass]: recordActions.measureHere,
  [recordChanges.schema]: recordActions.convert,
  [recordChanges.rules]: recordActions.rejudge,
  [recordChanges.hostVersion]: recordActions.remeasureBackground,
} as const;

/** the PLUGIN_DB_RUNS word of each word of PLUGIN_DB_STATES */
export const statesGroup = {
  [states.unqualified]: runs.alone,
  [states.qualified]: runs.shared,
  [states.isolatedOnly]: runs.alone,
  [states.conditionsUnmet]: runs.alone,
  [states.refused]: runs.notLoaded,
  [states.absent]: runs.notLoaded,
} as const;

/** the PLUGIN_DB_STATES word of each word of PLUGIN_DB_REASONS */
export const reasonsGroup = {
  [reasons.neverPinned]: states.unqualified,
  [reasons.measurementPending]: states.unqualified,
  [reasons.couldNotTest]: states.unqualified,
  [reasons.filesChanged]: states.unqualified,
  [reasons.layoutChanged]: states.unqualified,
  [reasons.layoutNotYetKnown]: states.unqualified,
  [reasons.recordStale]: states.unqualified,
  [reasons.notMeasuredUnderHost]: states.unqualified,
  [reasons.verdictAllows]: states.qualified,
  [reasons.verdictIsolated]: states.isolatedOnly,
  [reasons.referenceOnly]: states.isolatedOnly,
  [reasons.noCell]: states.conditionsUnmet,
  [reasons.conditionFails]: states.conditionsUnmet,
  [reasons.recordRefused]: states.refused,
  [reasons.shippedRefusal]: states.refused,
  [reasons.filesGone]: states.absent,
} as const;

/** the keys a record must carry (data/store.schema.json, recordFields) and its host's */
export const recordRequired = ["verdict", "machineClass", "host", "rules", "recordSchema", "cells", "conditions"] as const;
export const recordHostRequired = ["name", "version", "hostingEpoch"] as const;
