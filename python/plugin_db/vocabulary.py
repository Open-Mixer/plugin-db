# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# GENERATED: DO NOT EDIT BY HAND.
# Produced by tools/render-py.py from data/pin.json and data/db.json. Each words item is a Words object of its words
# in their order, keyed as data/ keys them; a grouped item has <item>_group (the group word of each word).


class Words(dict):
    """the words of one item: words.key is the word, and iterating the values gives them in the order of data/"""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None


# PLUGIN_DB_PIN_VERDICTS
pin_verdicts = Words(
    inProcess="in-process",
    isolated="isolated",
    refused="refused",
)

# PLUGIN_DB_PIN_POOLS
pin_pools = Words(
    cores="cores",
    off="off",
)

# PLUGIN_DB_PIN_KEYS
pin_keys = Words(
    verdict="verdict",
    pool="pool",
)

# PLUGIN_DB_PIN_CHANGES
pin_changes = Words(
    files="files",
    layout="layout",
)

# PLUGIN_DB_PIN_LAYOUT_FORMATS
pin_layout_formats = Words(
    clap="clap",
    lv2="lv2",
)

# PLUGIN_DB_ADDRESS_FORMATS
address_formats = Words(
    clap="clap",
    lv2="lv2",
)

# PLUGIN_DB_BUNDLE_RULES
bundle_rules = Words(
    newestVersion="newest-version",
)

# PLUGIN_DB_LAYERS
layers = Words(
    declared="declared",
    scanned="scanned",
    pinned="pinned",
    measured="measured",
    judged="judged",
    reference="reference",
    corrected="corrected",
    warnedOverride="warned-override",
    observed="observed",
)

# PLUGIN_DB_FILES
files = Words(
    same="same",
    changed="changed",
    absent="absent",
    couldNotTest="could-not-test",
)

# PLUGIN_DB_LAYOUT
layout = Words(
    same="same",
    changed="changed",
    notYetKnown="not-yet-known",
)

# PLUGIN_DB_RECORD
record = Words(
    current="current",
    stale="stale",
    none="none",
)
# the owners' text of each word of PLUGIN_DB_RECORD, by language
record_text = {
    "current": {
        "en": "Its record is current."
    },
    "stale": {
        "en": "Its record no longer applies."
    },
    "none": {
        "en": "It has no record."
    }
}

# PLUGIN_DB_RECORD_ACTIONS
record_actions = Words(
    fullPath="full-path",
    measureHere="measure-here",
    convert="convert",
    rejudge="rejudge",
    remeasureBackground="remeasure-background",
)
# the owners' text of each word of PLUGIN_DB_RECORD_ACTIONS, by language
record_actions_text = {
    "full-path": {
        "en": "Scan, measure and judge it again."
    },
    "measure-here": {
        "en": "Measure it on this machine."
    },
    "convert": {
        "en": "Convert the record; nothing is measured again."
    },
    "rejudge": {
        "en": "Judge the measurements again; nothing is measured again."
    },
    "remeasure-background": {
        "en": "The record still applies; it is measured again in the background."
    }
}

# PLUGIN_DB_RECORD_CHANGES
record_changes = Words(
    files="files",
    layout="layout",
    hostingChange="hosting-change",
    machineClass="machine-class",
    schema="schema",
    rules="rules",
    hostVersion="host-version",
)
# the owners' text of each word of PLUGIN_DB_RECORD_CHANGES, by language
record_changes_text = {
    "files": {
        "en": "Its files changed."
    },
    "layout": {
        "en": "Its parameters changed."
    },
    "hosting-change": {
        "en": "The host changed how it hosts plugins."
    },
    "machine-class": {
        "en": "This is another kind of machine."
    },
    "schema": {
        "en": "The record format changed."
    },
    "rules": {
        "en": "The qualification rules changed."
    },
    "host-version": {
        "en": "The host is another release."
    }
}

# PLUGIN_DB_STATES
states = Words(
    unqualified="unqualified",
    qualified="qualified",
    isolatedOnly="isolated-only",
    conditionsUnmet="conditions-unmet",
    refused="refused",
    absent="absent",
)
# the owners' text of each word of PLUGIN_DB_STATES, by language
states_text = {
    "unqualified": {
        "en": "Not qualified: it runs alone, in a worker of its own."
    },
    "qualified": {
        "en": "Qualified: it runs as its record allows."
    },
    "isolated-only": {
        "en": "Qualified to run alone only."
    },
    "conditions-unmet": {
        "en": "Its record does not cover this machine's settings: it runs alone."
    },
    "refused": {
        "en": "Refused: it is not loaded."
    },
    "absent": {
        "en": "Its files are gone: it is not loaded."
    }
}

# PLUGIN_DB_RUNS
runs = Words(
    shared="shared",
    alone="alone",
    notLoaded="not-loaded",
)
# the owners' text of each word of PLUGIN_DB_RUNS, by language
runs_text = {
    "shared": {
        "en": "Runs in a shared worker."
    },
    "alone": {
        "en": "Runs alone, in a worker of its own."
    },
    "not-loaded": {
        "en": "Not loaded: an effect passes audio through, an instrument is silent."
    }
}

# PLUGIN_DB_REASONS
reasons = Words(
    neverPinned="never-pinned",
    measurementPending="measurement-pending",
    couldNotTest="could-not-test",
    filesChanged="files-changed",
    layoutChanged="layout-changed",
    layoutNotYetKnown="layout-not-yet-known",
    recordStale="record-stale",
    notMeasuredUnderHost="not-measured-under-host",
    verdictAllows="verdict-allows",
    verdictIsolated="verdict-isolated",
    referenceOnly="reference-only",
    noCell="no-cell",
    conditionFails="condition-fails",
    recordRefused="record-refused",
    shippedRefusal="shipped-refusal",
    filesGone="files-gone",
)
# the owners' text of each word of PLUGIN_DB_REASONS, by language
reasons_text = {
    "never-pinned": {
        "en": "It has never been scanned."
    },
    "measurement-pending": {
        "en": "It has not been measured yet."
    },
    "could-not-test": {
        "en": "Its files could not be read."
    },
    "files-changed": {
        "en": "Its files have changed since they were scanned."
    },
    "layout-changed": {
        "en": "Its parameters have changed since they were scanned."
    },
    "layout-not-yet-known": {
        "en": "Its parameters are not known yet."
    },
    "record-stale": {
        "en": "Its record no longer applies and it needs measuring again."
    },
    "not-measured-under-host": {
        "en": "Its record says alone, but it was not measured under plugin-hostd."
    },
    "verdict-allows": {
        "en": "Its record allows a shared worker."
    },
    "verdict-isolated": {
        "en": "Its record says it is safe only alone."
    },
    "reference-only": {
        "en": "Measured on another kind of machine: reference figures only."
    },
    "no-cell": {
        "en": "Its record has no measurement at this rate and quantum."
    },
    "condition-fails": {
        "en": "A condition of its record does not hold on this machine."
    },
    "record-refused": {
        "en": "Its record says refused."
    },
    "shipped-refusal": {
        "en": "These files are refused by the record shipped with them."
    },
    "files-gone": {
        "en": "Its files are gone."
    }
}

# PLUGIN_DB_ISOLATION_HOSTS
isolation_hosts = Words(
    pluginHostd="plugin-hostd",
)

# PLUGIN_DB_SOURCES
sources = Words(
    none="none",
    local="local",
    reference="reference",
)
# the owners' text of each word of PLUGIN_DB_SOURCES, by language
sources_text = {
    "none": {
        "en": "No record."
    },
    "local": {
        "en": "Measured on this machine."
    },
    "reference": {
        "en": "Measured on a reference machine."
    }
}

# PLUGIN_DB_BAR
bar = Words(
    qualifiedOnly="qualified-only",
    warnOnCrashes="warn-on-crashes",
    loadAll="load-all",
)
# the owners' text of each word of PLUGIN_DB_BAR, by language
bar_text = {
    "qualified-only": {
        "en": "Offer qualified plugins only."
    },
    "warn-on-crashes": {
        "en": "Offer every plugin that is not refused; ask only after a crash."
    },
    "load-all": {
        "en": "Offer every plugin, refused ones included."
    }
}

# PLUGIN_DB_LATENCY
latency = Words(
    within="within",
    over="over",
    unmeasured="unmeasured",
)
# the owners' text of each word of PLUGIN_DB_LATENCY, by language
latency_text = {
    "within": {
        "en": "Latency within the line."
    },
    "over": {
        "en": "Latency over the line; it still loads."
    },
    "unmeasured": {
        "en": "Latency not measured."
    }
}

# the PLUGIN_DB_RECORD word of each word of PLUGIN_DB_RECORD_ACTIONS
record_actions_group = {
    record_actions.fullPath: record.stale,
    record_actions.measureHere: record.stale,
    record_actions.convert: record.stale,
    record_actions.rejudge: record.stale,
    record_actions.remeasureBackground: record.current,
}

# the PLUGIN_DB_RECORD_ACTIONS word of each word of PLUGIN_DB_RECORD_CHANGES
record_changes_group = {
    record_changes.files: record_actions.fullPath,
    record_changes.layout: record_actions.fullPath,
    record_changes.hostingChange: record_actions.fullPath,
    record_changes.machineClass: record_actions.measureHere,
    record_changes.schema: record_actions.convert,
    record_changes.rules: record_actions.rejudge,
    record_changes.hostVersion: record_actions.remeasureBackground,
}

# the PLUGIN_DB_RUNS word of each word of PLUGIN_DB_STATES
states_group = {
    states.unqualified: runs.alone,
    states.qualified: runs.shared,
    states.isolatedOnly: runs.alone,
    states.conditionsUnmet: runs.alone,
    states.refused: runs.notLoaded,
    states.absent: runs.notLoaded,
}

# the PLUGIN_DB_STATES word of each word of PLUGIN_DB_REASONS
reasons_group = {
    reasons.neverPinned: states.unqualified,
    reasons.measurementPending: states.unqualified,
    reasons.couldNotTest: states.unqualified,
    reasons.filesChanged: states.unqualified,
    reasons.layoutChanged: states.unqualified,
    reasons.layoutNotYetKnown: states.unqualified,
    reasons.recordStale: states.unqualified,
    reasons.notMeasuredUnderHost: states.unqualified,
    reasons.verdictAllows: states.qualified,
    reasons.verdictIsolated: states.isolatedOnly,
    reasons.referenceOnly: states.isolatedOnly,
    reasons.noCell: states.conditionsUnmet,
    reasons.conditionFails: states.conditionsUnmet,
    reasons.recordRefused: states.refused,
    reasons.shippedRefusal: states.refused,
    reasons.filesGone: states.absent,
}

# the data/ item of each words object: a catalog keys a message as <item>.<word>
ITEMS = {
    "pin_verdicts": "PLUGIN_DB_PIN_VERDICTS",
    "pin_pools": "PLUGIN_DB_PIN_POOLS",
    "pin_keys": "PLUGIN_DB_PIN_KEYS",
    "pin_changes": "PLUGIN_DB_PIN_CHANGES",
    "pin_layout_formats": "PLUGIN_DB_PIN_LAYOUT_FORMATS",
    "address_formats": "PLUGIN_DB_ADDRESS_FORMATS",
    "bundle_rules": "PLUGIN_DB_BUNDLE_RULES",
    "layers": "PLUGIN_DB_LAYERS",
    "files": "PLUGIN_DB_FILES",
    "layout": "PLUGIN_DB_LAYOUT",
    "record": "PLUGIN_DB_RECORD",
    "record_actions": "PLUGIN_DB_RECORD_ACTIONS",
    "record_changes": "PLUGIN_DB_RECORD_CHANGES",
    "states": "PLUGIN_DB_STATES",
    "runs": "PLUGIN_DB_RUNS",
    "reasons": "PLUGIN_DB_REASONS",
    "isolation_hosts": "PLUGIN_DB_ISOLATION_HOSTS",
    "sources": "PLUGIN_DB_SOURCES",
    "bar": "PLUGIN_DB_BAR",
    "latency": "PLUGIN_DB_LATENCY",
}

# the keys a record must carry (data/store.schema.json, recordFields) and its host's
record_required = ["verdict", "machineClass", "host", "rules", "recordSchema", "cells", "conditions"]
record_host_required = ["name", "version", "hostingEpoch"]
