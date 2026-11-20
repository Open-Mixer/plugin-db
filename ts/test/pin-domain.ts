// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
// The verdict and pool words of a pin are plugin-hostd-protocol's, its domain pin (<contract directory>/pin/pin.json): the
// contract directory is $PIN_DOMAIN_DIR, else the installed one (pkg-config omx-contract, contractdir).
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export function pinDomain(): Record<string, { oneOf: { const: string; title: string; description?: string; "x-code": number }[] }> {
  const dir = process.env.PIN_DOMAIN_DIR || execFileSync("pkg-config", ["--variable=contractdir", "omx-contract"], { encoding: "utf8" }).trim();
  return JSON.parse(readFileSync(join(dir, "pin", "pin.json"), "utf8")).components.schemas;
}

/** the words of PIN_VERDICTS or PIN_POOLS, in the order of their codes */
export function pinWords(item: "PIN_VERDICTS" | "PIN_POOLS"): { key: string; word: string; doc: string }[] {
  return [...pinDomain()[item].oneOf].sort((a, b) => a["x-code"] - b["x-code"]).map((w) => ({ key: w.title, word: w.const, doc: w.description ?? "" }));
}
