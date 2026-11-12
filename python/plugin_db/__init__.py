# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""plugin-db's reader in Python: the twin of src/state.c and of ts/src/reader.ts.

    from plugin_db import read, why, vocabulary as v
    answer = read(entry, here)          # state, runs, reason, source, tier, figures: words of the vocabulary
    if answer["state"] == v.states.qualified: ...
    why(answer, "ca")                   # the sentence of its reason, from the catalog of the language
    answer = query("lv2:<uri>", here)   # the same answer for an entry of the store, through the command plugin-db

Every word is the vocabulary's, generated from data/; tests/golden/ holds the three readers equal.
"""
from . import vocabulary
from .query import QueryError, query
from .reader import read, standing
from .text import CATALOGS, text, why

__all__ = ["CATALOGS", "QueryError", "query", "read", "standing", "text", "vocabulary", "why"]
