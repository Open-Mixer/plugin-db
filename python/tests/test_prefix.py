# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The installed files the reader finds, the catalogs and omx-contract's catalog reader, under a venv (#14): the
venv's when the venv holds them, else the system prefix's, where the packages install them. Outside a venv the two
prefixes are one. Each case runs the source tree's plugin_db in a real venv's interpreter."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

PYTHON = os.path.join(os.path.dirname(__file__), "..")
# the module, not the package's text() of the same name
SHOW = ("import importlib, json, sys; text = importlib.import_module('plugin_db.text'); "
        "print(json.dumps({'catalogs': text.CATALOGS, 'reader': text.READER, "
        "'prefix': sys.prefix, 'base': sys.base_prefix}))")


def venv_paths(venv):
    """the two paths, and the two prefixes, as the venv's interpreter sees them"""
    python = os.path.join(venv, "bin", "python3")
    env = dict(os.environ, PYTHONPATH=os.path.abspath(PYTHON))
    out = subprocess.run([python, "-c", SHOW], env=env, check=True, capture_output=True, text=True).stdout
    return json.loads(out)


class Prefix(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.venv = os.path.join(self.dir.name, "venv")
        # --without-pip: no ensurepip, so a Debian build needs no python3-venv
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", self.venv], check=True)

    def tearDown(self):
        self.dir.cleanup()

    def test_a_venv_holding_neither_reads_the_system_prefix(self):
        got = venv_paths(self.venv)
        self.assertNotEqual(os.path.realpath(got["prefix"]), os.path.realpath(got["base"]), "a venv of its own prefix")
        self.assertEqual(got["catalogs"], os.path.join(got["base"], "share", "plugin-db", "catalogs"))
        self.assertEqual(got["reader"], os.path.join(got["base"], "share", "omx-contract", "omx_contract_catalog.py"))

    def test_a_venv_holding_the_catalogs_reads_its_own(self):
        os.makedirs(os.path.join(self.venv, "share", "plugin-db", "catalogs"))
        got = venv_paths(self.venv)
        self.assertEqual(got["catalogs"], os.path.join(got["prefix"], "share", "plugin-db", "catalogs"))
        self.assertEqual(got["reader"], os.path.join(got["base"], "share", "omx-contract", "omx_contract_catalog.py"))


if __name__ == "__main__":
    unittest.main()
