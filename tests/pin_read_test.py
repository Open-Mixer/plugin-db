#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""tests/pin_read_test.py: the verdict and pool words of a pin are plugin-hostd-protocol's (its domain `pin`, PIN_VERDICTS and
PIN_POOLS, installed by plugin-hostd-protocol-contract 0.8.0); plugin-db reads them there (sorting pass, V12).

The readers are the validators phd_pin_verdict_valid and phd_pin_pool_valid of include/plugin-db/pin.h (through
plugin_db_tables.h, which tools/render-db.py writes), the Python twin's pin_verdicts and pin_pools (tools/render-py.py) and
the TypeScript twin's pinVerdicts and pinPools (tools/render-ts.py).

(a) golden: the validators accept the five words and refuse their neighbours, and the twins' words are the golden ones, as
    plugin-db's own pin words were before V12 (in-process, isolated, refused; cores, off), in the tree as it is;
(b) the domain's words are the golden ones (the only holder: tests/pin_old_items_test.py holds plugin-db to none);
(c) sabotage, through the real readers: a domain with the word `refused` and the word `off` removed makes the validators
    of a tree rendered from it refuse them, and the twins of that render lack them;
(e) packaging: packaging/deps.txt, the spec and debian/control floor plugin-hostd-protocol-contract at 0.8.0 or above,
    the release that carries the domain (floors only: no ceiling, no Breaks, Replaces, Conflicts or Provides);

Environment: PIN_DOMAIN_DIR (a contract directory holding pin/pin.json: protocol's contract.d, or the installed contract
directory, the default), CC. Exit 0 all green, 1 a FAIL line."""
import json, os, shlex, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC = shlex.split(os.environ.get("CC", "cc"))
VERDICTS = ["in-process", "isolated", "refused"]
POOLS = ["cores", "off"]
failed = 0


def check(cond, what):
    global failed
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        failed += 1


def domain_dir():
    d = os.environ.get("PIN_DOMAIN_DIR")
    if d:
        return d
    return subprocess.run(["pkg-config", "--variable=contractdir", "omx-contract"], capture_output=True, text=True).stdout.strip()


PROBE = r'''
#include <stdio.h>
#include <plugin-db/pin.h>
int main(void)
{
    const char *v[] = { "in-process", "isolated", "refused", "in_process", "", "Refused", "refuse" };
    const char *p[] = { "cores", "off", "on", "", "core" };
    unsigned i;
    for (i = 0; i < sizeof v / sizeof *v; i++) printf("%d", phd_pin_verdict_valid(v[i]));
    printf(" ");
    for (i = 0; i < sizeof p / sizeof *p; i++) printf("%d", phd_pin_pool_valid(p[i]));
    printf("\n");
    return 0;
}
'''
GOLDEN_PROBE = "1110000 11000\n"


def tree(tmp, name, edit=None):
    """a scratch copy of the parts of the tree the renders and the header read"""
    t = os.path.join(tmp, name)
    for d in ("include", "tools", "data", "contract.d"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(t, d))
    if edit:
        edit(t)
    return t


def render(t, domain, what):
    """run the three renders of the tree t against the domain directory; (ok, {name: output path})"""
    env = dict(os.environ, PIN_DOMAIN_DIR=domain)
    outs = {"tables": os.path.join(t, "include", "plugin-db", "plugin_db_tables.h"), "py": os.path.join(t, "vocabulary.py"),
            "ts": os.path.join(t, "vocabulary.ts")}
    for tool, out in (("render-db.py", outs["tables"]), ("render-py.py", outs["py"]), ("render-ts.py", outs["ts"])):
        r = subprocess.run([sys.executable, os.path.join(t, "tools", tool), os.path.join(t, "data"), out], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print("note %s: %s: %s" % (what, tool, r.stderr.strip()[-160:]))
            return False, outs
    return True, outs


def probe(t, tmp, name):
    src = os.path.join(tmp, name + ".probe.c")
    open(src, "w").write(PROBE)
    exe = os.path.join(tmp, name + ".bin")
    b = subprocess.run(CC + ["-Wall", "-Wextra", "-Werror", "-I" + os.path.join(t, "include"), "-o", exe, src,
                             "-lcrypto"], capture_output=True, text=True)
    if b.returncode != 0:
        return "build failed: " + b.stderr.strip()[-200:]
    return subprocess.run([exe], capture_output=True, text=True).stdout


def twin_words(outs):
    """{item: [words]} of the python and typescript twins' pin items, as the render wrote them"""
    got = {}
    py = open(outs["py"]).read() if os.path.exists(outs["py"]) else ""
    ts = open(outs["ts"]).read() if os.path.exists(outs["ts"]) else ""
    import re
    for key, name in (("pin_verdicts", "pinVerdicts"), ("pin_pools", "pinPools")):
        m = re.search(r"^%s = Words\((.*?)^\)" % key, py, re.S | re.M)
        got["py." + key] = re.findall(r'=\"([^\"]*)\"', m.group(1)) if m else None
        m = re.search(r"export const %s = \{(.*?)\} as const;" % name, ts, re.S)
        got["ts." + name] = re.findall(r': \"([^\"]*)\"', m.group(1)) if m else None
    return got


GOLD_TWINS = {"py.pin_verdicts": VERDICTS, "py.pin_pools": POOLS, "ts.pinVerdicts": VERDICTS, "ts.pinPools": POOLS}


def main():
    dom = domain_dir()
    path = os.path.join(dom, "pin", "pin.json")
    check(os.path.isfile(path), "the domain pin is found (%s)" % path)
    with tempfile.TemporaryDirectory() as tmp:
        # (a) golden, the tree as it is
        t = tree(tmp, "as-is")
        ok, outs = render(t, dom, "as-is")
        check(ok, "(a) the three renders run against the domain pin")
        check(probe(t, tmp, "as-is") == GOLDEN_PROBE, "(a) phd_pin_verdict_valid and phd_pin_pool_valid accept the five words and refuse their neighbours")
        check(twin_words(outs) == GOLD_TWINS, "(a) the twins' pin words are the golden ones, in their order")
        for what, tool, out, committed in (("tables", "render-db.py", outs["tables"], "include/plugin-db/plugin_db_tables.h"),
                                           ("python", "render-py.py", outs["py"], "python/plugin_db/vocabulary.py"),
                                           ("typescript", "render-ts.py", outs["ts"], "ts/src/vocabulary.ts")):
            same = os.path.exists(out) and open(out).read() == open(os.path.join(ROOT, committed)).read()
            check(same, "(a) %s is what the render writes from the domain pin" % committed)
        # (b) both sources
        if os.path.isfile(path):
            doc = json.load(open(path))["components"]["schemas"]
            for item, want in (("PIN_VERDICTS", VERDICTS), ("PIN_POOLS", POOLS)):
                new = [w["const"] for w in sorted(doc[item]["oneOf"], key=lambda w: w["x-code"])]
                check(new == want, "(b) %s of the domain is the golden words" % item)
            # (c) sabotage through the real readers
            cut = os.path.join(tmp, "cut")
            os.makedirs(os.path.join(cut, "pin"))
            d = json.loads(json.dumps(json.load(open(path))))
            for item, title in (("PIN_VERDICTS", "refused"), ("PIN_POOLS", "off")):
                d["components"]["schemas"][item]["oneOf"] = [w for w in d["components"]["schemas"][item]["oneOf"] if w["title"] != title]
            json.dump(d, open(os.path.join(cut, "pin", "pin.json"), "w"), indent=2)
            t2 = tree(tmp, "cut")
            ok, outs2 = render(t2, cut, "cut")
            check(ok, "(c) the renders run against the cut domain")
            check(probe(t2, tmp, "cut") == "1100000 10000\n", "(c) a domain without refused and off makes the validators refuse them")
            tw = twin_words(outs2)
            check(tw == {"py.pin_verdicts": VERDICTS[:2], "py.pin_pools": POOLS[:1], "ts.pinVerdicts": VERDICTS[:2], "ts.pinPools": POOLS[:1]},
                  "(c) the twins of that render lack them")
        # (e) packaging
        import re
        floors = []
        for f, rx in (("packaging/deps.txt", r"^plugin-hostd-protocol-contract\s+\S+\s+(\d+\.\d+\.\d+)\s*$"),
                      ("packaging/plugin-db.spec", r"^BuildRequires:\s*plugin-hostd-protocol-contract\s*>=\s*(\d+\.\d+\.\d+)\s*$"),
                      ("debian/control", r"plugin-hostd-protocol-contract \(>= (\d+\.\d+\.\d+)~\)")):
            m = re.search(rx, open(os.path.join(ROOT, f)).read(), re.M)
            floors.append((f, m.group(1) if m else None))
        check(all(v and tuple(map(int, v.split("."))) >= (0, 8, 0) for _, v in floors),
              "(e) plugin-hostd-protocol-contract is floored at 0.8.0 or above in %s" % ", ".join("%s (%s)" % f for f in floors))
    return 1 if failed else 0


sys.exit(main())
