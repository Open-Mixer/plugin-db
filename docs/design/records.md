<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# The record and the probe output as layers of an entry

## The question

What shape a qualification record and a probe's output take as layers of a plugin-db entry, so that a menu reads one
fixed answer and never a record file.

## What is ruled

- Each fact belongs to one layer and each layer has one writer. A later layer never overwrites an earlier one.
- The store is one directory per entry and one declared JSON file per layer, written atomically, each recording the
  pin it was written for, so a stale layer is found and never trusted. The entry is joined at read time.
- Every layer's schema is declared in `data/`, the record's included, and the readers are derived from it. Existing
  records and the shipped files are converted, not discarded; a change of record schema converts, it does not
  re-measure.
- The measured layer holds latency, cost and behaviour per rate and quantum, with the conditions they were taken
  under, written by the probes; it may be wiped. The judged layer is the record: verdict, conditions, version tested,
  written by plugin-qualify's judgement. The tier rule lives once, in that judgement, as a field of the record.
- Measurements never enter a descriptor. A measurement names the host it truly ran under.
- The menu reads through the one reader: `plugin-db query --json` for Python and scripts, the TypeScript twin for
  the console. Neither parses a record nor computes a tier, a state or a verdict.

## The shape, as built

Every layer file is the envelope of `data/store.schema.json`: `envelope` (1), `layer`, `address`, `pin` (`files`, the
`omx-files/1` digest, and `layout`), `writer`, `body`. The pinned body is declared whole. The judged and reference
bodies carry at least the fields the state function reads: `verdict`, `machineClass`, `host` (`name`, `version`,
`hostingEpoch`), `rules`, `recordSchema`, `cells` (`rate`, `quantum`, `latencyMs`), `conditions` and `latencyLineMs`.
The schema leaves the rest of the record to be declared beside them; the record converted is plugin-qualify's
`QualificationRecord`.

What the menu reads is the answer, not the layers: `address`, `files`, `layout`, `record`, `change`, `action`,
`state`, `runs`, `reason`, `source`, `tier` and `figures` (`rate`, `quantum`, `latencyMs`, `lineMs`, `standing`).
`tests/golden/` holds 25 examples, one for each state and the way to it, each with the layers it starts from and the
answer `query --json` and the twin must both give. They are the examples a reader is written against.

## Divergences, as the code stands

1. **The record is a TypeScript interface.** plugin-qualify writes `plugin-qualify.qualification-record/1` beside a
   byte copy of the probe output it judged, and publishes no schema file.
2. **One verdict or many.** The record holds one verdict per host (`verdicts`, a rating each, mapped to a pin word by
   `pinVerdictOf`); the judged body holds one `verdict` and one `host`.
3. **Fields with no source in the record:** `hostingEpoch`, `rules`, `conditions` as facts, `latencyLineMs`. It
   names its machine class as an object (`probe.machineClass`), not a word, and its latency in frames, not
   milliseconds.
4. **The tier.** The record carries `tiers`; the reader takes the verdict word as the tier.
5. **The probe output.** Its schema is plugin-hostd's (`protocol/probe-output.schema.json`, `formatVersion` 1.1);
   plugin-qualify keeps copies of its examples at 1.0, held to nothing.
6. **The reference writer.** `data/db.json` names `plugin-db-qualification` as the reference layer's writer; the
   shipped records are `omx-qualification-records`.

## Open

- Whether a host's verdict is one judged layer per host, or one layer holding every host's.
- Whether the measured layer is the probe output as it is, declared here, or a body that carries it.
- What a judged record keeps once the measured layer is wiped: today a byte copy and its SHA-256.
- Which word is the machine class, and where the hosting epoch is declared.

## The menu column (spec 7.15), as it stands

Built: the reader's answer (state, run, reason, source, the record's tier, the figures at a rate and quantum), the run
word `alone`, the bar words, `query --json` and the twin, held equal by `tests/golden/`. What a menu still cannot have
from it:

1. **Owner text: written.** omx-contract 3.12.0 gives a word `text`, the source sentence in English, with `args`, and
   every word a menu says (state, run, reason, source, record, change, action, bar, standing) carries plugin-db's in
   `data/db.json`. The Catalan is `catalogs/ca.json` (`<ITEM>.<word>` keys), installed to
   `/usr/share/plugin-db/catalogs/ca.json` with the contract package and checked by `make check-contract-dir`. The C
   vocabulary header has the source sentence as `OMX_<ITEM>_<WORD>_TEXT_EN`, the twin's vocabulary as `<item>Text`.
   The answer stays words: a menu shows the sentence of the word the reader gives, from the catalog of its language,
   else the source sentence.
2. **No judged layer is written.** plugin-qualify writes `plugin-qualify.qualification-record/1` files to its own
   directory and packages them as `plugin-db-qualification-*`; it puts no judged or reference layer in the store.
   On every machine the reader answers `unqualified` with `never-pinned` or `measurement-pending`. A record given to
   `put` as a judged layer is refused, which is right: the reader never parses a record.
3. **What a conversion lacks.** With no `hostingEpoch` the record reads as a hosting change, and with no `rules` or
   `recordSchema` as changed, so a converted record that leaves them out answers `stale`. With no `latencyLineMs` the
   standing is `unmeasured`. The line is plugin-qualify's to declare (7.15's order puts it before the reader); the
   epoch, the rules version and the machine class word need their owners too, and the converter is plugin-qualify's,
   the judged layer's one writer.
4. **The console's call.** The twin's `read(entry, here)` is given the layers and the files finding; finding the files
   (the bundle rule) and hashing them is the C library's. Until the twin can be given an entry from the store without
   the console reading a layer, `plugin-db query --json <address> <here>` is the one complete answer.
