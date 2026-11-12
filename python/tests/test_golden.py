# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The Python twin against tests/golden/*.json: the files tests/golden.py holds `plugin-db query --json` to and
ts/test/golden.test.ts holds the TypeScript twin to. Each is a plugin in one of the states of §4.2 (and the way to
it), and the answer the one reader gives. A fixture the readers split on is red here or there."""
import json
import os
import unittest

from plugin_db import read, vocabulary as v

DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "golden")
FILES, OTHER_FILES = "a" * 64, "e" * 64
LAYOUT, OTHER_LAYOUT = "omx-layout/1:" + "a" * 64, "omx-layout/1:" + "b" * 64


def entry_of(fx):
    layout = LAYOUT if fx["pinnedLayout"] else None

    def layer(name):
        spec = fx["layers"].get(name)
        if not spec:
            return None
        return {"pin": {"files": OTHER_FILES if spec["pin"] == "files" else FILES,
                        "layout": OTHER_LAYOUT if spec["pin"] == "layout" else layout},
                "body": spec["body"]}

    return {
        "files": fx["files"],
        "currentLayout": {"match": LAYOUT, "other": OTHER_LAYOUT}.get(fx["currentLayout"]),
        "pinned": {"pin": {"files": FILES, "layout": layout}, "body": {}} if fx["pinned"] else None,
        "judged": layer("judged"),
        "reference": layer("reference"),
        "warnedOverride": layer("warned-override"),
    }


def load(name):
    with open(os.path.join(DIR, name), encoding="utf-8") as f:
        return json.load(f)


def fixtures():
    return [load(n) for n in sorted(os.listdir(DIR)) if n.endswith(".json")]


class Golden(unittest.TestCase):
    maxDiff = None

    def test_there_are_fixtures_and_every_state_is_among_them(self):
        self.assertGreaterEqual(len(fixtures()), 20)
        reached = {fx["expect"]["state"] for fx in fixtures()}
        for state in v.states.values():
            self.assertIn(state, reached, f"no fixture reaches the state {state}")

    def test_the_twin_equals_every_fixture(self):
        for fx in fixtures():
            with self.subTest(fx["name"]):
                self.assertEqual(read(entry_of(fx), fx["here"]), fx["expect"])

    def test_the_answer_has_the_types_of_the_fixture(self):
        # 1 == 1.0 == True in Python: the JSON written from the answer must be the fixture's, not only equal to it
        for fx in fixtures():
            with self.subTest(fx["name"]):
                got = read(entry_of(fx), fx["here"])
                self.assertEqual(json.dumps(got, sort_keys=True), json.dumps(fx["expect"], sort_keys=True))

    def test_one_byte_changed_makes_the_twin_say_unqualified(self):
        fx = load("qualified.json")
        self.assertEqual(read(entry_of(fx), fx["here"])["state"], v.states.qualified)
        self.assertEqual(read({**entry_of(fx), "files": v.files.changed}, fx["here"])["state"], v.states.unqualified)

    def test_a_true_is_no_number(self):
        fx = load("qualified.json")
        e = entry_of(fx)
        for c in e["judged"]["body"]["cells"]:
            c["latencyMs"] = True
        figures = read(e, fx["here"])["figures"]
        self.assertIsNone(figures["latencyMs"])
        self.assertEqual(figures["standing"], v.latency.unmeasured)

    def test_a_record_of_another_layout_is_stale(self):
        fx = load("qualified.json")
        e = entry_of(fx)
        self.assertEqual(e["pinned"]["pin"]["layout"], LAYOUT)
        e["judged"]["pin"]["layout"] = OTHER_LAYOUT
        got = read(e, fx["here"])
        self.assertEqual((got["record"], got["change"]), (v.record.stale, v.record_changes.layout))
        e["judged"]["pin"]["layout"] = None
        self.assertEqual(read(e, fx["here"])["change"], v.record_changes.layout)


if __name__ == "__main__":
    unittest.main()
