# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""query(): the command line it gives the command, the answer it reads back, and a command that cannot answer.
tests/golden.py holds query() to the real command over every fixture; here the command is a stand-in."""
import os
import stat
import tempfile
import unittest

from plugin_db import QueryError, query
from plugin_db.query import arguments

HERE = {"machineClass": "desk", "hostName": "plugin-hostd", "hostVersion": "0.20.3", "hostingEpoch": 3, "rules": "r1",
        "recordSchema": "s1", "rate": 48000, "quantum": 256, "facts": ["governor=performance", "rt=yes"]}


class Query(unittest.TestCase):
    def test_here_is_given_as_the_command_takes_it(self):
        self.assertEqual(arguments("lv2:urn:a", HERE, store="/s", layout="omx-layout/1:ab"), [
            "--store", "/s", "query", "--json", "lv2:urn:a", "--machine-class", "desk", "--host", "plugin-hostd",
            "--host-version", "0.20.3", "--hosting-epoch", "3", "--rules", "r1", "--record-schema", "s1",
            "--rate", "48000", "--quantum", "256", "--fact", "governor=performance", "--fact", "rt=yes",
            "--layout", "omx-layout/1:ab"])

    def test_a_fact_not_known_here_is_not_given(self):
        self.assertEqual(arguments("lv2:urn:a", {"rate": 96000, "hostName": None}), ["query", "--json", "lv2:urn:a", "--rate", "96000"])
        self.assertEqual(arguments("lv2:urn:a", {}, system=True), ["--system", "query", "--json", "lv2:urn:a"])
        self.assertEqual(arguments("lv2:urn:a", {"hostingEpoch": 0}), ["query", "--json", "lv2:urn:a", "--hosting-epoch", "0"])

    def command(self, d, body):
        path = os.path.join(d, "stand-in")
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n" + body)
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path

    def test_the_answer_is_what_the_command_prints(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.command(d, 'printf \'{"address": "%s", "asked": "%s"}\' "$3" "$*"\n')
            got = query("lv2:urn:a", {"rate": 48000}, command=c)
            self.assertEqual(got, {"address": "lv2:urn:a", "asked": "query --json lv2:urn:a --rate 48000"})

    def test_a_command_that_cannot_answer_raises_what_it_said(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.command(d, "echo 'plugin-db: no entry' >&2\nexit 1\n")
            with self.assertRaises(QueryError) as e:
                query("lv2:urn:a", {}, command=c)
            self.assertEqual((e.exception.status, str(e.exception)), (1, "plugin-db: no entry"))


if __name__ == "__main__":
    unittest.main()
