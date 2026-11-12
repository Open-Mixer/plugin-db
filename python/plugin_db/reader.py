# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The Python twin of plugin-db's reader (src/state.c and the check of src/store.c; ts/src/reader.ts is the TypeScript
one): the entry's layers and what a check of its files found, here, to the one answer of the plugin-db spec §4.2 and
§5: state, run, reason, source, the record's tier and the figure at this rate and quantum. Nothing here is a word:
every word is the vocabulary's, generated from data/, and tests/golden/ holds this file equal to the C reader, to
`plugin-db query --json` and to the TypeScript twin. Neither this nor a surface computes a tier, a state or an RT
verdict of its own.

The entry, here and the answer are the JSON of tests/golden/ and of `plugin-db query --json`, as dicts:

    entry   files (a word of v.files), currentLayout (text or None), and the layers pinned, judged, reference and
            warnedOverride, each None or {"pin": {"files": text, "layout": text or None}, "body": {...}}
    here    machineClass, hostName, hostVersion, hostingEpoch, rules, recordSchema, rate, quantum, facts; absent or
            None is not known here, which no record matches
    answer  files, layout, record, change, action, state, runs, reason, source, tier, figures
"""
import math

from . import vocabulary as v


def _str(x):
    return x if isinstance(x, str) else None


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


_NONE = {
    "present": False, "pinFiles": False, "pinLayout": False, "verdict": None, "machineClass": None, "hostName": None,
    "hostVersion": None, "hostingEpoch": -1, "rules": None, "recordSchema": None, "cells": [], "conditions": [],
    "lineMs": None,
}


def _valid(body):
    """a layer that does not carry the fields of a record, or whose verdict is no word of the vocabulary, is no record"""
    host = body.get("host") if isinstance(body, dict) else None
    return (isinstance(body, dict) and all(k in body for k in v.record_required) and isinstance(host, dict)
            and all(k in host for k in v.record_host_required)
            and any(_str(body["verdict"]) == w for w in v.pin_verdicts.values()))


def _load(layer, pinned):
    """a record from its layer, against the pinned layer's pin"""
    if not layer or not _valid(layer["body"]):
        return _NONE
    body, host = layer["body"], layer["body"]["host"]
    cells = []
    if isinstance(body.get("cells"), list):
        for c in body["cells"]:
            rate = _num(c.get("rate")) if isinstance(c, dict) else None
            quantum = _num(c.get("quantum")) if isinstance(c, dict) else None
            if rate is not None and quantum is not None:
                cells.append({"rate": int(rate), "quantum": int(quantum), "latencyMs": _num(c.get("latencyMs"))})
    # conditions that cannot be read are conditions no fact here meets
    conditions = ([f"{k}={_str(x) or ''}" for k, x in body["conditions"].items()]
                  if isinstance(body.get("conditions"), dict) else [""])
    epoch = _num(host.get("hostingEpoch"))
    pin, ours = layer["pin"], pinned["pin"] if pinned else None
    return {
        "present": True,
        "pinFiles": ours is not None and pin["files"] == ours["files"],
        "pinLayout": ours is not None and pin.get("layout") == ours.get("layout"),
        "verdict": _str(body.get("verdict")),
        "machineClass": _str(body.get("machineClass")),
        "hostName": _str(host.get("name")),
        "hostVersion": _str(host.get("version")),
        "hostingEpoch": -1 if epoch is None else int(epoch),
        "rules": _str(body.get("rules")),
        "recordSchema": _str(body.get("recordSchema")),
        "cells": cells,
        "conditions": conditions,
        "lineMs": _num(body.get("latencyLineMs")),
    }


def _differs(a, b):
    """a fact a record names and here does not know differs"""
    return a is None or b is None or a != b


def _changed(change, files, layout, r, h):
    """whether one row of the changes table holds for the record"""
    c = v.record_changes
    if change == c.files:
        return files != v.files.same or not r["pinFiles"]
    if change == c.layout:
        return layout != v.layout.same or not r["pinLayout"]
    if change == c.hostingChange:
        epoch = _num(h.get("hostingEpoch"))
        return epoch is None or epoch < 0 or r["hostingEpoch"] < epoch
    if change == c.machineClass:
        return _differs(r["machineClass"], h.get("machineClass"))
    if change == c.schema:
        return _differs(r["recordSchema"], h.get("recordSchema"))
    if change == c.rules:
        return _differs(r["rules"], h.get("rules"))
    if change == c.hostVersion:
        return _differs(r["hostName"], h.get("hostName")) or _differs(r["hostVersion"], h.get("hostVersion"))
    return True  # a change with no test here is never passed


def _change_of(files, layout, r, h):
    """the first change, in the changes table's order, since the record was written"""
    return next((c for c in v.record_changes.values() if _changed(c, files, layout, r, h)), None)


def _current(change):
    return change is None or v.record_actions_group[v.record_changes_group[change]] == v.record.current


def _cell_here(r, h):
    rate, quantum = _num(h.get("rate")), _num(h.get("quantum"))
    if rate is None or quantum is None or rate <= 0 or quantum <= 0:
        return None
    return next((c for c in r["cells"] if c["rate"] == rate and c["quantum"] == quantum), None)


def _conditions_here(r, h):
    facts = h.get("facts") or []
    return all(c in facts for c in r["conditions"])


def _answer(state, reason, source):
    return {"state": state, "runs": v.states_group[state], "reason": reason, "source": source}


def _alone(r, reason, source):
    """alone, if it may: isolated only needs a measurement under a host of the isolation hosts"""
    if r["hostName"] is not None and r["hostName"] in v.isolation_hosts.values():
        return _answer(v.states.isolatedOnly, reason, source)
    return _answer(v.states.unqualified, v.reasons.notMeasuredUnderHost, v.sources.none)


def _state(files, layout, pinned, local, reference, warned_override, h):
    """THE state function, as src/state.c has it: (record, change, answer)"""
    change, record = None, v.record.none
    if local["present"]:
        change = _change_of(files, layout, local, h)
        record = v.record.current if _current(change) else v.record.stale

    if files == v.files.absent:
        return record, change, _answer(v.states.absent, v.reasons.filesGone, v.sources.none)
    # a shipped refusal of these bytes wins over everything, a warned override included
    if (reference["present"] and files == v.files.same and reference["pinFiles"]
            and reference["verdict"] == v.pin_verdicts.refused):
        return record, change, _answer(v.states.refused, v.reasons.shippedRefusal, v.sources.reference)

    rec, source = None, v.sources.none
    if record == v.record.current:
        rec, source = local, v.sources.local
    elif not local["present"] and reference["present"]:
        # a local measurement wins; with none, a shipped record of these bytes answers on its class of machine and
        # gives reference figures only on another
        c = _change_of(files, layout, reference, h)
        if _current(c):
            rec, source = reference, v.sources.reference
        elif c == v.record_changes.machineClass:
            return record, change, _alone(reference, v.reasons.referenceOnly, v.sources.reference)

    if rec is None:
        if not pinned:
            reason = v.reasons.neverPinned
        elif files == v.files.couldNotTest:
            reason = v.reasons.couldNotTest
        elif files == v.files.changed:
            reason = v.reasons.filesChanged
        elif layout == v.layout.changed:
            reason = v.reasons.layoutChanged
        elif layout == v.layout.notYetKnown:
            reason = v.reasons.layoutNotYetKnown
        elif record == v.record.stale:
            reason = v.reasons.recordStale
        else:
            reason = v.reasons.measurementPending
        return record, change, _answer(v.states.unqualified, reason, v.sources.none)
    if rec["verdict"] == v.pin_verdicts.refused:
        a = _answer(v.states.refused, v.reasons.recordRefused, source)
        if warned_override:
            a["runs"] = v.runs.alone
        return record, change, a
    if rec["verdict"] not in (v.pin_verdicts.inProcess, v.pin_verdicts.isolated):
        return record, change, _answer(v.states.unqualified, v.reasons.couldNotTest, v.sources.none)
    if _cell_here(rec, h) is None:
        return record, change, _answer(v.states.conditionsUnmet, v.reasons.noCell, source)
    if not _conditions_here(rec, h):
        return record, change, _answer(v.states.conditionsUnmet, v.reasons.conditionFails, source)
    if rec["verdict"] == v.pin_verdicts.isolated:
        return record, change, _alone(rec, v.reasons.verdictIsolated, source)
    return record, change, _answer(v.states.qualified, v.reasons.verdictAllows, source)


def standing(latency_ms, line_ms):
    """where a figure stands against the line: unmeasured when either is missing, never a guess"""
    if latency_ms is None or line_ms is None:
        return v.latency.unmeasured
    return v.latency.over if latency_ms > line_ms else v.latency.within


def read(entry, here):
    """the entry's one answer, here"""
    pinned = entry.get("pinned")
    files = entry["files"] if pinned else v.files.couldNotTest
    pinned_layout = pinned["pin"].get("layout") if pinned else None
    current_layout = entry.get("currentLayout")
    if pinned_layout is None:
        layout = v.layout.notYetKnown
    elif current_layout is not None:
        layout = v.layout.changed if current_layout != pinned_layout else v.layout.same
    else:
        layout = v.layout.same if files == v.files.same else v.layout.notYetKnown
    local, reference = _load(entry.get("judged"), pinned), _load(entry.get("reference"), pinned)
    override = entry.get("warnedOverride")
    warned_override = bool(override and pinned and files == v.files.same
                           and override["pin"]["files"] == pinned["pin"]["files"])
    record, change, a = _state(files, layout, bool(pinned), local, reference, warned_override, here)

    # the tier is the answering record's verdict when it says where the plugin runs; a refusal has none
    answering = reference if a["source"] == v.sources.reference else local if a["source"] == v.sources.local else _NONE
    tier = answering["verdict"] if answering["verdict"] in (v.pin_verdicts.inProcess, v.pin_verdicts.isolated) else None
    cell = _cell_here(answering, here) if tier else None
    return {
        "files": files, "layout": layout, "record": record,
        "change": change,
        "action": None if change is None else v.record_changes_group[change],
        "state": a["state"], "runs": a["runs"], "reason": a["reason"], "source": a["source"],
        "tier": tier,
        "figures": None if cell is None else {
            "rate": cell["rate"], "quantum": cell["quantum"], "latencyMs": cell["latencyMs"],
            "lineMs": answering["lineMs"], "standing": standing(cell["latencyMs"], answering["lineMs"]),
        },
    }
