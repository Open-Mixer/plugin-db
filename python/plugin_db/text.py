# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The sentence of a word. The answer of the reader stays words; a menu shows the sentence of the word, from the
catalog of its language, else the owners' source sentence in English (data/, in the generated vocabulary)."""
import json
import os
import sys

from . import vocabulary as v

#: where the contract package installs the catalogs (<lang>.json, messages keyed <ITEM>.<word>)
CATALOGS = os.path.join(sys.prefix, "share", "plugin-db", "catalogs")
SOURCE = "en"


def _item(words):
    for name, item in v.ITEMS.items():
        if getattr(v, name) is words:
            return name, item
    raise KeyError("not a words item of the vocabulary")


def text(words, word, lang=SOURCE, catalogs=None):
    """the sentence of `word` of the item `words` (v.reasons, v.states, ...) in `lang`; KeyError when the word is
    not the item's or the item's words carry no sentence"""
    name, item = _item(words)
    source = getattr(v, name + "_text")[word][SOURCE]
    if lang == SOURCE:
        return source
    try:
        with open(os.path.join(CATALOGS if catalogs is None else catalogs, lang + ".json"), encoding="utf-8") as f:
            said = json.load(f)["messages"].get(f"{item}.{word}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return source
    return said if isinstance(said, str) and said else source


def why(answer, lang=SOURCE, catalogs=None):
    """the sentence of the reason of an answer of read()"""
    return text(v.reasons, answer["reason"], lang, catalogs)
