# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The sentence of a word. The answer of the reader stays words; a menu shows the sentence of the word, from the
catalog of its language, else the owners' source sentence in English (data/, in the generated vocabulary)."""
import importlib.util
import json
import os
import sys

from . import vocabulary as v


def _installed(*parts):
    """an installed file or directory: the venv's when the venv holds it (the package installed into the venv), else
    the system prefix's, where the packages install it (#14); outside a venv the two prefixes are one"""
    for prefix in (sys.prefix, sys.base_prefix):
        path = os.path.join(prefix, *parts)
        if os.path.exists(path):
            return path
    return os.path.join(sys.base_prefix, *parts)


#: where the contract package installs the catalogs (<lang>.json, messages keyed <ITEM>.<word>)
CATALOGS = _installed("share", "plugin-db", "catalogs")
SOURCE = "en"
#: omx-contract's catalog reader (omx-contract-data, 3.16.0 or later): a catalog's entry is the sentence or
#: {text, by[, model, source]}, and one made from another English sentence is stale and gives the English
READER = _installed("share", "omx-contract", "omx_contract_catalog.py")
_reader = None


def _catalog_reader():
    global _reader
    if _reader is None:
        spec = importlib.util.spec_from_file_location("omx_contract_catalog", READER)
        _reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_reader)
    return _reader


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
            catalog = json.load(f)
    except (OSError, ValueError):
        return source
    said = _catalog_reader().sentence_of(catalog if isinstance(catalog, dict) else None, f"{item}.{word}", source)
    return said if isinstance(said, str) and said else source


def why(answer, lang=SOURCE, catalogs=None):
    """the sentence of the reason of an answer of read()"""
    return text(v.reasons, answer["reason"], lang, catalogs)
