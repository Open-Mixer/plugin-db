# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""No Python source of the package types a state, run, reason, tier (a record's verdict), bar or latency-standing
word, or a sentence of data/, as a string: they come from the generated vocabulary, as ts/test/conformance.test.ts
holds the C and TypeScript sources to. The generated vocabulary, data/ and the tests are the places that name them."""
import ast
import json
import os
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
PKG = os.path.join(ROOT, "python", "plugin_db")
ITEMS = ["PLUGIN_DB_STATES", "PLUGIN_DB_RUNS", "PLUGIN_DB_REASONS", "PLUGIN_DB_PIN_VERDICTS", "PLUGIN_DB_BAR", "PLUGIN_DB_LATENCY"]
GENERATED = {"vocabulary.py"}


def slurp(*path):
    with open(os.path.join(*path), encoding="utf-8") as f:
        return f.read()


def vocabulary():
    words, sentences = set(), set()
    for f in ("db.json", "pin.json"):
        for item, body in json.loads(slurp(ROOT, "data", f)).items():
            if not isinstance(body, dict) or body.get("kind") != "words":
                continue
            for w in body["words"].values():
                if item in ITEMS:
                    words.add(w["word"])
                if w.get("doc"):
                    sentences.add(w["doc"])
                sentences.update(w.get("text", {}).values())
    return words, sentences


def sources():
    return sorted(n for n in os.listdir(PKG) if n.endswith(".py") and n not in GENERATED)


def offenders(files):
    words, sentences = vocabulary()
    bad = []
    for name, source in files.items():
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and (node.value in words or node.value in sentences):
                bad.append(f"{name}: {node.value!r}")
    return bad


class Conformance(unittest.TestCase):
    def test_the_sources_are_found_and_the_vocabulary_is_read(self):
        self.assertIn("reader.py", sources())
        self.assertNotIn("vocabulary.py", sources())
        words, _ = vocabulary()
        for w in ("alone", "refused", "in-process", "no-cell", "within", "load-all"):
            self.assertIn(w, words)

    def test_no_source_types_a_word_or_a_sentence_of_data(self):
        self.assertEqual(offenders({n: slurp(PKG, n) for n in sources()}), [])

    def test_the_check_sees_a_typed_word_and_passes_the_generated_name(self):
        self.assertEqual(len(offenders({"a.py": 'if run == "alone":\n    pass\n'})), 1)
        self.assertEqual(len(offenders({"a.py": "tier = 'in-process'\n"})), 1)
        self.assertEqual(offenders({"a.py": 'run = v.runs.alone  # "alone" in a comment\n'}), [])


if __name__ == "__main__":
    unittest.main()
