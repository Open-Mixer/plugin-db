<!-- SPDX-License-Identifier: GPL-3.0-or-later
     Copyright (C) 2026 Pau Aliagas -->

# Threat model

## What it is and where it runs

plugin-db has three parts, all in this repository:

- `include/plugin-db/pin.h`: a header-only C library on libc and libcrypto. It computes the SHA-256 of a file over an
  open descriptor and the `omx-layout/1` fingerprint of a plugin's parameters, and checks the words of a pin. A plugin
  host links it and fills its records from the plugin it has loaded.
- `libplugin-db.a` (`src/`) and the `plugin-db` command (`src/cli.c`): pin, put, show, query and verify over a store
  of JSON layer files. It reads LV2 manifests as text and hashes files; it loads no plugin. It is not a daemon and runs
  as whoever invokes it. `--system` selects `/var/lib/plugin-db`; no service unit is shipped (`packaging/`, `debian/`).
- `ts/src/reader.ts`: a TypeScript twin of the reader. It does no I/O; it is given already-parsed layers.

None of this is real-time code. The layout writers call `malloc` and `qsort`, the digest reads a file, and the code
makes no real-time claim. Its users, as the README names them, are plugin hosts, the judgement writer that calls
`put`, the console (through the TypeScript twin) and scripts through `query --json`.

## Inputs

| Input | Read by | Who can write it | Trusted |
| --- | --- | --- | --- |
| Plugin files hashed (`.clap`, LV2 binaries, `manifest.ttl`, `rdfs:seeAlso` files) | `phd_pin_fd_digest()`, `digest_of()` in `src/store.c` | plugin author, packager, local user (`~/.lv2`) | untrusted |
| LV2 `manifest.ttl` text, of every bundle in the search path | `pdb_manifest_read()`, `pdb_manifest_scan()` in `src/manifest.c`, `pdb_lv2_bundle()` in `src/collect.c` | plugin author, packager, local user | untrusted |
| LV2 bundle directory names in the search path | `bundles_of()` in `src/collect.c` | plugin author, packager, local user | untrusted |
| CLAP parameter info and LV2 control-port data (names, symbols, numbers, flags, property URIs) handed in by a host | `phd_layout_clap_write()`, `phd_layout_lv2_write()`, `*_digest()` in `pin.h` | plugin author | untrusted |
| Pin text read back: digest, layout pin `<scheme>:<sha256>`, verdict, pool word | `phd_pin_hex_valid()`, `phd_pin_layout_parse()`, `phd_pin_verdict_valid()`, `phd_pin_pool_valid()` in `pin.h` | whoever writes the store or the host's pin line | untrusted |
| Store layer files `entries/<sha256>/<layer>.json` | `read_all()`, `layer_read()` in `src/store.c`, `pdb_json_parse()` in `src/json.c` | local user (user store); whoever owns `/var/lib/plugin-db` or `$PLUGIN_DB_STORE` | untrusted |
| Layer body on standard input (`put`) | `read_stdin()` in `src/cli.c`, then `pdb_json_parse()` | the caller, e.g. a judgement writer | untrusted |
| Command-line arguments: address, `--file`, `--lv2-path`, `--layout`, `--store`, facts of here | `src/cli.c`, `pdb_address_parse()` in `src/address.c` | local user | trusted (caller's own) |
| Environment: `LV2_PATH`, `PLUGIN_DB_STORE`, `XDG_STATE_HOME`, `HOME` | `pdb_lv2_search()`, `pdb_store_default()` | local user | trusted (caller's own) |
| `data/*.json`, rendered into `include/plugin-db/plugin_db_tables.h` and `ts/src/vocabulary.ts` at build time | `tools/render-db.py`, `tools/render-ts.py` | maintainer, packager | trusted |
| Layers and file findings given to the TypeScript reader | `read()` in `ts/src/reader.ts` | the console process that parsed them from the store | untrusted content, trusted caller |

## Trust boundary

A plugin author controls every byte of the plugin's files, its LV2 manifest and Turtle, its bundle and file names,
and every name, number, flag and property the host reads from the loaded plugin and passes to `pin.h`. A packager
controls the same for the files it installs under `/usr/lib/lv2` and `/usr/lib/clap`. The local user controls
`~/.lv2`, the user store under `$XDG_STATE_HOME`, standard input and the arguments. The store is plain files: anyone
who can write the store directory controls the layers read back, including the search path and `.clap` path that
`verify` re-collects and hashes. The command takes no input from the network or from a graph client.

## What the code assumes and enforces

- Manifest: `pdb_manifest_read()` refuses a file that is not regular or is larger than `PDB_MANIFEST_MAX` (4 MiB,
  `src/manifest.h`). The scanner holds at most 64 prefixes of 255 bytes each and truncates a token to `PATH_MAX`;
  further prefixes are ignored, not refused.
- Bundle files: `lv2_collect()` refuses a manifest that sets `@base`, a name that is not percent-encoded, and a name
  that `pdb_path_valid()` rejects (empty, absolute, a `..` component, a trailing `/`, or containing space, tab,
  newline, `,` or `=`). `pdb_full_path()` refuses a name whose decoding adds a `/`.
- Symbolic links inside a bundle or the store are followed; `O_NOFOLLOW` is not used. Not enforced.
- CLAP file: `clap_collect()` requires an absolute path to a regular file (`stat()`).
- Hashing: `digest_of()` hashes only a regular file (`fstat()`); `phd_pin_fd_digest()` returns -1 on a read error and
  on a libcrypto failure. There is no size cap on a hashed file.
- Store reads: `read_all()` refuses a non-regular file and one over 64 MiB. `layer_read()` requires the envelope keys,
  the layer and address it was written for, a 64-hex files digest, an `omx-layout/1` layout pin, the body keys of
  its layer and a verdict word of `data/pin.json`. An entry directory name must be 64 lowercase hex digits.
- JSON: `pdb_json_parse()` is strict RFC 8259, refuses nesting deeper than 64 (`DEPTH_MAX`), a string holding NUL
  a repeated key, and a number of 64 bytes or more.
- Store writes: `write_atomic()` writes to a `mkstemp` name, `fchmod` 0644, `fsync`, then `rename`; directories are
  made 0755.
- Standard input for `put`: `read_stdin()` grows without a cap. Not enforced.
- Addresses: `pdb_address_parse()` accepts only a format of `data/db.json`, a 64-hex pin on `clap@`, a non-empty id,
  no control byte or space in the id, and no leading `/` in a CLAP id.
- Pin words: `phd_pin_hex_valid()` takes exactly 64 lowercase hex digits; `phd_pin_layout_parse()` splits at the last
  `:` and refuses a scheme that does not fit its buffer.
- Layout: a NULL CLAP name is written as empty; `\`, tab and newline in a name are escaped; `phd_layout_*_write()`
  returns -1 when memory runs out. There is no cap on the parameter or property count.
- Paths built with `snprintf` into `PDB_PATH_MAX` (4096) buffers are refused when truncated.

## Fuzz coverage

`fuzz/README.md` describes the harnesses; each runs under ASan and UBSan in `.github/workflows/fuzz.yml`.

| Untrusted input | Harness |
| --- | --- |
| Pin text read back: digest, layout pin, verdict, pool word | `fuzz/fuzz_pin.c` |
| CLAP parameter and LV2 control-port data, and their layout fingerprint | `fuzz/fuzz_layout.c` |
| Bytes hashed (whole, chunked, abandoned) | `fuzz/fuzz_digest.c` |

### Gaps

- `src/manifest.c` (Turtle scanner) has no fuzz target, though it parses every manifest of the search path.
- `src/json.c` (store layer files and `put` bodies) has no fuzz target.
- `pdb_address_parse()`, `pdb_path_valid()`, `pdb_full_path()` and the percent decoding they rely on are not fuzzed.
- `phd_pin_fd_digest()` and all file and directory I/O (`src/collect.c`, `src/store.c`) have no harness; a harness
  here may not open a descriptor.
- `ts/src/reader.ts` is not fuzzed; it is tested against `tests/golden/` only.
- Not checked anywhere: symbolic links in bundles or the store, the size of a hashed file, the size of standard input
  for `put`, and concurrent writers to one entry beyond the atomic rename.

## Reporting

Report a vulnerability privately through GitHub: the repository's Security tab, "Report a vulnerability".
The policy is the organisation's `SECURITY.md`.
