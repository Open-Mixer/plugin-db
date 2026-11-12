# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The sentence of a word: the owners' English from data/ (in the generated vocabulary), another language from its
catalog, and the English where a catalog has no sentence for the word."""
import json
import os
import tempfile
import unittest

from plugin_db import text, why, vocabulary as v

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CATALOGS = os.path.join(ROOT, "catalogs")


def load(*path):
    with open(os.path.join(*path), encoding="utf-8") as f:
        return json.load(f)


def write(path, said):
    with open(path, "w", encoding="utf-8") as f:
        f.write(said)


class Text(unittest.TestCase):
    def setUp(self):
        self.db = load(ROOT, "data", "db.json")
        self.ca = load(CATALOGS, "ca.json")["messages"]

    def test_english_is_the_sentence_of_data(self):
        for key, w in self.db["PLUGIN_DB_REASONS"]["words"].items():
            self.assertEqual(text(v.reasons, w["word"]), w["text"]["en"])
        self.assertEqual(text(v.states, v.states.refused), self.db["PLUGIN_DB_STATES"]["words"]["refused"]["text"]["en"])

    def test_catalan_is_the_catalog_s(self):
        for word in v.reasons.values():
            self.assertEqual(text(v.reasons, word, "ca", CATALOGS), self.ca[f"PLUGIN_DB_REASONS.{word}"])
        self.assertEqual(text(v.latency, v.latency.over, "ca", CATALOGS), self.ca["PLUGIN_DB_LATENCY.over"])

    def test_a_language_with_no_catalog_or_no_sentence_gives_the_english(self):
        en = text(v.reasons, v.reasons.noCell)
        self.assertEqual(text(v.reasons, v.reasons.noCell, "xx", CATALOGS), en)
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "ca.json"), json.dumps({"kind": "catalog", "lang": "ca", "messages": {}}))
            self.assertEqual(text(v.reasons, v.reasons.noCell, "ca", d), en)
            write(os.path.join(d, "fr.json"), "{ not json")
            self.assertEqual(text(v.reasons, v.reasons.noCell, "fr", d), en)

    def test_english_is_never_a_catalog_s(self):
        with tempfile.TemporaryDirectory() as d:
            key = f"PLUGIN_DB_REASONS.{v.reasons.noCell}"
            write(os.path.join(d, "en.json"), json.dumps({"kind": "catalog", "lang": "en", "messages": {key: "other"}}))
            self.assertEqual(text(v.reasons, v.reasons.noCell, "en", d), self.db["PLUGIN_DB_REASONS"]["words"]["noCell"]["text"]["en"])

    def test_a_word_that_is_not_the_item_s_is_refused(self):
        with self.assertRaises(KeyError):
            text(v.reasons, v.states.qualified)
        with self.assertRaises(KeyError):
            text({"a": "b"}, "b")

    def test_why_is_the_sentence_of_the_answer_s_reason(self):
        answer = {"reason": v.reasons.filesGone}
        self.assertEqual(why(answer), text(v.reasons, v.reasons.filesGone))
        self.assertEqual(why(answer, "ca", CATALOGS), self.ca[f"PLUGIN_DB_REASONS.{v.reasons.filesGone}"])


if __name__ == "__main__":
    unittest.main()
