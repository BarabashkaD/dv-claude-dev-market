#!/usr/bin/env python
"""Scan files (or stdin) for personal data that must not reach a public repo.

Usage: check_public.py [--denylist PATH] [--stdin] [--allowlist PATH] [ROOT]

Exit 0 when clean, 1 when findings were printed as `file:line: reason`.
Without --denylist only paths and e-mail addresses are checked (CI mode).
Patterns are assembled by concatenation so this file does not match itself.
"""
import argparse
import os
import re
import sys

PATH_MARKERS = [
    (re.escape("/Us" + "ers/"), "user home path"),
    (re.escape("~/" + "."), "home dotfile path"),
    (re.escape("~/") + "[A-Za-z]", "home folder path"),
    (re.escape("$HO" + "ME") + r"(?![A-Za-z0-9_])", "home variable"),
    (re.escape("c:\\" + "users"), "windows user path"),
]
PATH_MARKERS = [(re.compile(p, re.IGNORECASE), why) for p, why in PATH_MARKERS]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
ALLOWED_EMAIL_SUFFIX = "@users.noreply." + "github.com"
ALLOWED_EMAILS = {"noreply@" + "anthropic.com"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}


def read_list(path):
    """Entries of a list file: one per line, `#` comments and blanks ignored."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            s = line.strip()
            if s and not s.startswith("#"):
                out.append((n, s))
    return out


def email_allowed(addr):
    low = addr.lower()
    return low.endswith(ALLOWED_EMAIL_SUFFIX) or low in ALLOWED_EMAILS


def scan_line(line, denylist, allowlist):
    """Return reasons for one line."""
    # Masking replaces only the matched allowlisted fragment with a space, not the
    # whole line, and runs before every check (paths, e-mail, denylist) on purpose:
    # an allowlisted snippet is exempt, but anything else on the same line (a new
    # private path or denylisted word) is still caught.
    for a in allowlist:
        line = re.sub(re.escape(a), " ", line, flags=re.IGNORECASE)
    low = line.lower()
    reasons = []
    for marker, why in PATH_MARKERS:
        if marker.search(line):
            reasons.append(why)
    for m in EMAIL_RE.finditer(line):
        if not email_allowed(m.group(0)):
            reasons.append("e-mail address")
    for n, word in denylist:
        if word.lower() in low:
            reasons.append("denylist entry #%d" % n)
    return reasons


def scan_text(name, text, denylist, allowlist):
    found = []
    for i, line in enumerate(text.splitlines(), 1):
        for why in scan_line(line, denylist, allowlist):
            found.append("%s:%d: %s" % (name, i, why))
    return found


def scan_name(rel, denylist, allowlist):
    """Findings for the relative file/path name itself, as `path: name: reason`."""
    return ["%s: name: %s" % (rel, why) for why in scan_line(rel, denylist, allowlist)]


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for f in sorted(filenames):
            yield os.path.join(dirpath, f)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--denylist")
    ap.add_argument("--allowlist", action="append", default=[],
                    help="file of substrings to ignore; may be repeated")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("root", nargs="?", default=".")
    args = ap.parse_args(argv)

    deny = read_list(args.denylist) if args.denylist else []
    allow = [w for p in args.allowlist for _, w in read_list(p)]

    findings = []
    if args.stdin:
        data = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        findings = scan_text("<stdin>", data, deny, allow)
    else:
        for path in iter_files(args.root):
            with open(path, "rb") as fh:
                raw = fh.read()
            data = raw.decode("utf-8", errors="replace")
            rel = os.path.relpath(path, args.root).replace(os.sep, "/")
            findings += scan_name(rel, deny, allow)
            if b"\0" in raw[:8192]:
                continue  # binary: random bytes, names already checked
            findings += scan_text(rel, data, deny, allow)
    for f in findings:
        print(f)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
