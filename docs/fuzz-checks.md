# The checks of the fuzz targets

Each property that a harness in `fuzz/` checks is one `abort()` in a `check_` function. This
document reads every one of them against three questions:

- does the comment above it state the property that the code tests, in both directions;
- does the expected value come from the documented format (the comment at the head of
  `include/plugin-db/pin.h`, `data/pin.json`, FIPS 180-4), computed by the harness itself and
  not by a function of the header under test;
- can the check fail: a mutant record in its comment (`mutant:` / `input:`, proved by
  `make fuzz-records`) or a patch in `fuzz/sabotage/` (proved by `make fuzz-sabotage`) makes it
  abort on a seed of the corpus.

A verdict is **OK** when all three hold, **WEAK** when the check holds for some wrong library
(the one-line change is named), and **WRONG** when the comment or the expected value is not
the format's. The stops marked `not a property:` are allocation and start-up failures of the
harness or of libcrypto; they are listed at the end and need no breakage.

The expected values come from `fuzz/spec.h` (the digest charset and a SHA-256 written from
FIPS 180-4, libc only), from the escape, sort and number rules written out in
`fuzz/fuzz_layout.c`, and from the words of `data/pin.json` copied into `fuzz/fuzz_pin.c`. No
check calls a `phd_` function for its expected value.

## fuzz_pin

| Check | Property | Expected value from | Breakage that fires it | Verdict |
|---|---|---|---|---|
| `fuzz/fuzz_pin.c:60` | A string of 64 characters is a digest exactly when each is 0-9 or a-f (both directions) | `spec_hex_ok`, pin.h:134 | 3 records (`<= 'g'`, `>= 'A'`, `<= ':'`); `pin-digest-charset.patch` | OK |
| `fuzz/fuzz_pin.c:72` | A string of any other length is never a digest | the string's own length, pin.h:134 | 2 records (NUL test dropped, loop one short); `pin-digest-length.patch` | OK |
| `fuzz/fuzz_pin.c:91` | A layout pin is accepted exactly when it splits at its last `:` into a non-empty scheme that fits and a digest | the harness's own split (`strrchr`, `spec_hex_ok`, the buffer size) | 4 records (empty scheme, digest at the colon, `strchr`, size off by one); `pin-token-refusal.patch` | OK |
| `fuzz/fuzz_pin.c:103` | The scheme given back is the bytes before the last `:`, then a NUL | the input bytes | 2 records; `pin-token-scheme.patch` | OK |
| `fuzz/fuzz_pin.c:115` | The digest given back is the 64 bytes after the last `:`, then a NUL | the input bytes | 2 records; `pin-token-digest.patch` | OK |
| `fuzz/fuzz_pin.c:129` | A verdict is exactly one of `in-process`, `isolated`, `refused`, whole | `data/pin.json` words, written in the harness | 3 records (always 1, count short, prefix match); `pin-verdict.patch` | OK |
| `fuzz/fuzz_pin.c:141` | A pool word is exactly one of `cores`, `off`, whole | `data/pin.json` words, written in the harness | 2 records (always 1, count short); `pin-pool.patch` | OK |

The acceptance check at line 91 is two-way, so the scheme and digest checks, which run only on an
accepted pin, cover every input between them.

## fuzz_digest

| Check | Property | Expected value from | Breakage that fires it | Verdict |
|---|---|---|---|---|
| `fuzz/fuzz_digest.c:83` | The digest of a message, in one call, is its SHA-256 | `spec_sha256` (FIPS 180-4) | 3 records (half the message, high nibble, low nibble); `digest-value.patch` | OK |
| `fuzz/fuzz_digest.c:93` | The digest is the same however the message is cut into updates | `spec_sha256` of the whole message, not the library's one-call result | 1 record (one-byte updates dropped); `digest-chunks.patch` | OK |
| `fuzz/fuzz_digest.c:105` | A digest is 64 lowercase hex digits and a NUL, and its call returned 0 | `spec_hex_ok` | 2 records (NUL dropped, upper-case digits); `digest-form.patch` | OK |
| `fuzz/fuzz_digest.c:118` | A finished digest leaves its pointer NULL and every libcrypto block freed | the harness's count of libcrypto blocks | 2 records (pointer kept, context not freed); `digest-state.patch`, `digest-state.free.patch` | OK |
| `fuzz/fuzz_digest.c:134` | A digest given up is refused: -1, empty string, no context, no block held | pin.h:81 and pin.h:73; the block count | 3 records (string kept, refusal skipped, context not freed); `digest-failed.patch`, `digest-failed.free.patch` | OK |

The block count covers both the one-call digest and the digest in pieces, since it is taken before
the first of them.

## fuzz_layout

The harness writes the expected layout itself, from pin.h:28-34, and reads the library's bytes
with a cursor; each check eats the text it expects at that place, and the last one asks that
nothing is left. Together they compare the whole output, byte for byte.

| Check | Property | Expected value from | Breakage that fires it | Verdict |
|---|---|---|---|---|
| `fuzz/fuzz_layout.c:126` | The first line is `omx-layout/1 clap` or `omx-layout/1 lv2` | pin.h:29 | 3 records (scheme name, format swapped both ways); `layout-scheme-line.patch` | OK |
| `fuzz/fuzz_layout.c:147` | Rows are sorted by id or index, written in decimal, then a tab | the harness's stable insertion sort; `%u` | 5 records (no sort for either format, reversed order, base 8, separator); `layout-row-index.patch` | OK |
| `fuzz/fuzz_layout.c:181` | A name or symbol is written with `\`, tab and newline escaped, a NULL one empty; equal ids keep the order given | the harness's escape, pin.h:34 | 10 records (each escape, escape length, run start, NULL as `-`, tie order for both formats, separator); `layout-row-name.patch` | OK |
| `fuzz/fuzz_layout.c:213` | A number is the 16 lowercase hex digits of its binary64 bits, or `-` when not declared | `%016` PRIx64 of the input bits, pin.h:33 | 8 records (declared ignored, one bit flipped, digit mask, the three LV2 `has` bits, max as min, separator); `layout-row-number.patch` | OK |
| `fuzz/fuzz_layout.c:228` | CLAP flags are 8 lowercase hex digits | `%08x`, pin.h:30 | 2 records (decimal, digit mask); `layout-row-flags.patch` | OK |
| `fuzz/fuzz_layout.c:238` | An LV2 port is `in` or `out` | the input's direction bit, pin.h:31 | 1 record (swapped); `layout-row-direction.patch` | OK |
| `fuzz/fuzz_layout.c:259` | Properties are sorted bytewise, one space apart, `-` when none | the harness's own sort with `strcmp`, pin.h:31-32 | 4 records (no sort, separator, `-` dropped, unsorted list written); `layout-row-props.patch` | OK |
| `fuzz/fuzz_layout.c:271` | Every row ends with one newline | pin.h:28 | 2 records (both formats); `layout-row-end.patch` | OK |
| `fuzz/fuzz_layout.c:283` | Nothing follows the last row | pin.h:28 | 2 records (an extra line, both formats); `layout-end.patch` | OK |
| `fuzz/fuzz_layout.c:296` | The fingerprint is the SHA-256 of the bytes written | `spec_sha256` over the bytes that the checks above held to the format | 1 record (hash sink drops a byte); `layout-digest.patch` | OK |

## Not a property

| Stop | Reason |
|---|---|
| `fuzz/fuzz.h:82` | the harness's own allocation failed |
| `fuzz/fuzz_digest.c:145` | libcrypto allocated before the harness could count its blocks |
| `fuzz/fuzz_digest.c:148` | libcrypto could not start |
| `fuzz/fuzz_digest.c:151` | the first digest, which fills libcrypto's caches, failed |
| `fuzz/fuzz_layout.c:65` | the harness's own allocation failed |
| `fuzz/fuzz_layout.c:343` | the layout writer returned -1, which it does only when its own allocation fails |
| `fuzz/fuzz_layout.c:416` | as above, for LV2 |
| `fuzz/fuzz_layout.c:482` | libcrypto could not start |

Each reason holds: none of these stops can be reached by an input on a host with memory.

## Summary

22 property checks: 22 OK, 0 WEAK, 0 WRONG. Every expected value is computed by the harness from
the documented format; no check takes it from the header under test. Every check fires on a seed
under at least one mutant record and one sabotage patch: `make fuzz-records` meets all 67
records and 24 patches, each by its own check, and `make fuzz-sabotage` finds all 24 patches.

The review corrected the `contract:` line numbers in the comments of `fuzz/fuzz_layout.c`,
`fuzz/fuzz_pin.c` and `fuzz/spec.h`, which pointed at lines of pin.h that had moved, and the
summary of the name property, which now says that a NULL name is written empty.
