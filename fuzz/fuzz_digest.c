// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>

/* libFuzzer harness: THE SHA-256 OF BYTES (include/plugin-db/pin.h, phd_sha256_*), the digest
 * every pin is made of, over any bytes. Nothing here opens a descriptor: phd_pin_fd_digest()
 * reads a descriptor, and these are the steps it takes (init, update, final) on bytes the
 * harness holds.
 *
 * Input: byte 0 is the mode, the rest is the message, copied into an allocation of exactly its
 * length. The message is hashed in one call and again in chunks, whose size is the low seven
 * bits of the mode plus one; bit 7 of the mode also gives up a digest half made
 * (phd_sha256_abandon) and asks for its end. The harness hashes the message itself with its
 * own SHA-256 of FIPS 180-4 (fuzz/spec.h).
 *
 * Properties, each an abort() in a check_ function:
 *   - value: the digest of a message is the SHA-256 of it, in one call.
 *   - chunks: it is the same however the message is cut into updates.
 *   - form: it is 64 lowercase hex digits and a NUL, written whole.
 *   - state: a digest finished leaves no context behind: its pointer is NULL and every block
 *     libcrypto took for it is freed.
 *   - failed: a digest given up before its end is refused with -1 and an empty string, never
 *     with the digest of what it had, and it holds no block either.
 *
 * The harness counts the blocks libcrypto holds through CRYPTO_set_mem_functions, set in
 * LLVMFuzzerInitialize before libcrypto allocates anything. A first digest there fills the
 * caches libcrypto keeps for good, so a run's count changes only by what the digests under
 * test take and give back. libcrypto is started without its configuration file: the digest
 * needs none, and the run then opens no file.
 */
#include <plugin-db/pin.h>

#include <openssl/crypto.h>

#include "fuzz.h"
#include "spec.h"

/* the blocks libcrypto holds now */
static long held;

static void *count_malloc(size_t n, const char *file, int line)
{
	void *p = malloc(n);

	(void)file;
	(void)line;
	if (p)
		held++;
	return p;
}

static void count_free(void *p, const char *file, int line)
{
	(void)file;
	(void)line;
	if (p) {
		held--;
		free(p);
	}
}

static void *count_realloc(void *p, size_t n, const char *file, int line)
{
	if (!p)
		return count_malloc(n, file, line);
	if (n == 0) {
		count_free(p, file, line);
		return NULL;
	}
	return realloc(p, n);
}

FUZZ_CHECK check_value(const char *got, const char *want)
{
	/* The digest of the message is its SHA-256.
	 * contract: include/plugin-db/pin.h:82; FIPS 180-4 section 6.2
	 * mutant: include/plugin-db/pin.h:109 `data, size` -> `data, size / 2`
	 * input: abc
	 * mutant: include/plugin-db/pin.h:97 `md[n] >> 4` -> `md[n] & 15`
	 * input: abc
	 * mutant: include/plugin-db/pin.h:98 `md[n] & 15` -> `md[n] & 7`
	 * input: abc */
	if (strcmp(got, want) != 0)
		abort();
}

FUZZ_CHECK check_chunks(const char *got, const char *want)
{
	/* Feeding the message in pieces gives the same digest as feeding it whole.
	 * contract: include/plugin-db/pin.h:69 (update appends)
	 * mutant: include/plugin-db/pin.h:71 `data, size` -> `data, size > 1 ? size : 0`
	 * input: chunked-1 */
	if (strcmp(got, want) != 0)
		abort();
}

FUZZ_CHECK check_form(const char *hex, int rc)
{
	/* A digest is 64 lowercase hex digits and a NUL, and the call that wrote it returned 0.
	 * contract: include/plugin-db/pin.h:82
	 * mutant: include/plugin-db/pin.h:100 `hex[PHD_SHA256_HEX_LEN] = '\0';` -> ``
	 * input: abc
	 * mutant: include/plugin-db/pin.h:85 `0123456789abcdef` -> `0123456789ABCDEF`
	 * input: abc */
	if (rc != 0 || !spec_hex_ok(hex))
		abort();
}

FUZZ_CHECK check_state(const phd_sha256_t *c, long kept)
{
	/* A finished digest has freed its context and holds none: the pointer is NULL, and the
	 * blocks libcrypto holds are as many as before the digests began (kept is the difference).
	 * contract: include/plugin-db/pin.h:83
	 * mutant: include/plugin-db/pin.h:91 `c->ctx = NULL;` -> ``
	 * input: abc
	 * mutant: include/plugin-db/pin.h:90 `EVP_MD_CTX_free(c->ctx);` -> ``
	 * input: abc */
	if (c->ctx != NULL || kept != 0)
		abort();
}

FUZZ_CHECK check_failed(const phd_sha256_t *c, const char *hex, int rc, long kept)
{
	/* A digest given up is refused: -1, the string empty, no context kept, and no block of
	 * libcrypto held for it.
	 * contract: include/plugin-db/pin.h:82 `0, or -1 (and an empty string) when libcrypto failed`
	 * contract: include/plugin-db/pin.h:74 (abandon frees the context)
	 * mutant: include/plugin-db/pin.h:92 `hex[0] = '\0';` -> ``
	 * input: abandoned
	 * mutant: include/plugin-db/pin.h:93 `!c->ok` -> `0`
	 * input: abandoned
	 * mutant: include/plugin-db/pin.h:77 `EVP_MD_CTX_free(c->ctx);` -> ``
	 * input: abandoned */
	if (rc != -1 || hex[0] != '\0' || c->ctx != NULL || kept != 0)
		abort();
}

int LLVMFuzzerInitialize(int *argc, char ***argv)
{
	char hex[SPEC_HEX_LEN + 1];

	(void)argc;
	(void)argv;
	/* not a property: libcrypto allocated before the harness could count its blocks */
	if (CRYPTO_set_mem_functions(count_malloc, count_realloc, count_free) != 1)
		abort();
	/* not a property: libcrypto could not start */
	if (OPENSSL_init_crypto(OPENSSL_INIT_NO_LOAD_CONFIG, NULL) != 1)
		abort();
	/* not a property: the first digest, which fills libcrypto's caches, failed */
	if (phd_sha256_hex("", 0, hex) != 0)
		abort();
	return 0;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	char got[SPEC_HEX_LEN + 2], whole[SPEC_HEX_LEN + 2], want[SPEC_HEX_LEN + 1];
	struct fuzz_in in = fuzz_in(data, size);
	unsigned mode = fuzz_u8(&in);
	size_t chunk = (mode & 0x7f) + 1, n = in.n, at;
	const uint8_t *msg = in.p;
	phd_sha256_t c;
	uint8_t *copy;
	long before;
	int rc;

	if (size >= FUZZ_INPUT_MAX)
		return -1;
	copy = fuzz_alloc(n);
	if (n)
		memcpy(copy, msg, n);
	spec_sha256(copy, n, want);

	before = held;

	/* the message whole */
	memset(whole, 'x', sizeof whole - 1);
	whole[sizeof whole - 1] = '\0';
	rc = phd_sha256_hex(copy, n, whole);
	check_form(whole, rc);
	check_value(whole, want);

	/* the message in pieces */
	memset(got, 'x', sizeof got - 1);
	got[sizeof got - 1] = '\0';
	phd_sha256_init(&c);
	for (at = 0; at < n; at += chunk)
		phd_sha256_update(&c, copy + at, n - at < chunk ? n - at : chunk);
	rc = phd_sha256_final(&c, got);
	check_state(&c, held - before);
	check_form(got, rc);
	check_chunks(got, want);

	/* a digest given up */
	if (mode & 0x80) {
		memset(got, 'x', sizeof got - 1);
		got[sizeof got - 1] = '\0';
		before = held;
		phd_sha256_init(&c);
		phd_sha256_update(&c, copy, n);
		phd_sha256_abandon(&c);
		rc = phd_sha256_final(&c, got);
		check_failed(&c, got, rc, held - before);
	}

	free(copy);
	return 0;
}
