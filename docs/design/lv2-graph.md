<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# LV2 files and the bundle rule: what plugin-db exports, what plugin-hostd links

## The question

Does plugin-db export a Turtle or LV2 graph API, or only the collection of a plugin's files; and is the bundle rule
first in path or newest version. Without an answer plugin-hostd keeps its own tokenizer.

## What is ruled

- plugin-db owns which files are a plugin and the one bundle rule, with the file-collection code that sits in
  plugin-hostd's `src/lv2.c` and `src/formats.c`. It loads no plugin code.
- Controls and ports are facts of the scanned layer, written by plugin-qualify under its runner. plugin-hostd does not
  scan; once the layers are declared it reads the entry only, through the one reader.
- Nothing is parsed twice: one reader for one fact.

## The answer

**plugin-db exports the collection, not a graph.** `<plugin-db/db.h>` installs `pdb_address_parse`, `pdb_lv2_bundle`
and `pdb_collect`. The manifest reader behind them (`src/manifest.c`) is private and reads, of one plugin in one
`manifest.ttl`, only what the rule and the pin need: the objects of `lv2:binary` and `rdfs:seeAlso`, and
`lv2:minorVersion` and `lv2:microVersion`. A Turtle graph of a plugin's own files (its ports, units, groups) is the
scanned layer's to hold, and no graph API is added to plugin-db.

**The bundle rule is `newest-version`**, the only word of `PLUGIN_DB_BUNDLE_RULES` in `data/db.json`: of the bundles
that realise the plugin (an `lv2:binary`), or when none does the bundles that name it, the highest minor, then micro
version; of equal versions the first in the search path, the bundles of one directory in byte order of their names.

**The plugin-hostd change.** It links `pdb_lv2_bundle` and `pdb_collect` and deletes what they replace:
`proc_find_lv2_bundle` and `manifest_prefixed` (`src/proc.c`), the tokenizer, `lv2_pin_collect` and `lv2_binary`
(`src/lv2.c`), and `clap_pin_collect` (`src/formats.c`). The triple graph of `src/lv2.c` (`graph_parse`,
`ports_load`), which answers `param_info` and the remote pages for the LV2 row whose worker is mod-host, is not
replaced by plugin-db: it goes when plugin-hostd reads the entry only.

## Divergences, as the code stands

1. **Two rules today.** plugin-hostd takes the first bundle that holds a binary in path order, the bundles of one
   directory in `readdir` order (`src/proc.c`, `proc_find_lv2_bundle`); plugin-db takes the newest version. Its
   narrowed world hands the worker the bundle it chose, so the pin plugin-hostd checks and the pin plugin-db records
   can name two bundles.
2. **"lilv's rule".** plugin-db ranks a bundle that realises the plugin above one that only names it before it
   compares versions (`src/collect.c`, `better`). omx-panel's account of lilv describes a version comparison alone.
   The two agree unless a bundle with no binary states the higher version.
3. **The complement bundle.** omx-panel's complement restates `lv2:binary` as the installed library's absolute
   `file:` IRI and raises the micro version. Under `newest-version` it is the plugin's bundle, and `pdb_collect` then
   refuses it, the binary not being a file of the bundle. Read, not run.
4. **"Moved here".** `src/manifest.c` says the tokenizer was moved from plugin-hostd; plugin-hostd still holds its
   copy and calls no `pdb_` function.
5. **The ceiling.** plugin-hostd builds against `plugin-db < 0.3`; the collection is in 0.3.0.
6. **The way in.** The README says plugin-db depends on libc and libcrypto only; it builds against
   plugin-hostd-protocol's headers for the pin path codec.

## Open

- How a complement bundle is pinned: its binary lies outside it (divergence 3).
- Whether the mod-host LV2 row keeps `param_info` and remote pages until the scanned layer has a schema, or loses them.
- How the JavaScript readers (plugin-qualify's `src/lv2-loader.ts`, omx-panel's `tools/turtle-read.mjs`) reach the
  collection: `plugin-db` has no command that prints one.
