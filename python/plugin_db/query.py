# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The answer for an entry of the store, through the command: `plugin-db query --json <address> <here>`. Finding a
plugin's files (the bundle rule) and hashing them is the C library's, so this is the one complete answer for a plugin
on this machine; read() answers for layers already in hand. Both give the same dict."""
import json
import subprocess

COMMAND = "plugin-db"

# here, as the command takes it
_HERE = (("machineClass", "--machine-class"), ("hostName", "--host"), ("hostVersion", "--host-version"),
         ("hostingEpoch", "--hosting-epoch"), ("rules", "--rules"), ("recordSchema", "--record-schema"),
         ("rate", "--rate"), ("quantum", "--quantum"))


class QueryError(Exception):
    """the command could not answer: its exit status and what it said"""

    def __init__(self, status, said):
        super().__init__(said.strip() or f"{COMMAND} exits {status}")
        self.status = status


def arguments(address, here, store=None, system=False, layout=None):
    """the command line after the command's name"""
    args = ["--store", store] if store else ["--system"] if system else []
    args += ["query", "--json", address]
    for key, option in _HERE:
        if here.get(key) is not None:
            args += [option, str(here[key])]
    for fact in here.get("facts") or []:
        args += ["--fact", fact]
    if layout:
        args += ["--layout", layout]
    return args


def query(address, here, store=None, system=False, layout=None, command=COMMAND):
    """the reader's answer for `address` in the store, here; `layout` is the parameter layout the plugin shows now
    (<scheme>:<sha256>), when the caller knows it. QueryError when the command cannot answer."""
    r = subprocess.run([command, *arguments(address, here, store, system, layout)], capture_output=True, text=True)
    if r.returncode:
        raise QueryError(r.returncode, r.stderr)
    return json.loads(r.stdout)
