#!/usr/bin/env python3
"""Remove the text metadata chunks (tEXt, zTXt, iTXt, eXIf) from PNG files, in place.

Every other chunk (IHDR, IDAT, PLTE, gAMA, iCCP, IEND, ...) is copied byte for byte, so the pixels and
colour data are untouched. A file that is not a well-formed PNG is left alone and reported.

Run:  python3 -I strip_png_text.py FILE.png ...
Prints `file: removed N chunk(s)` per file; exits 1 if any file could not be processed, else 0.
Standard library only, Python 3.8+.
"""
import struct
import sys

SIGNATURE = b"\x89PNG\r\n\x1a\n"
TEXT_CHUNKS = (b"tEXt", b"zTXt", b"iTXt", b"eXIf")


def chunks(data):
    """Yield (type, raw chunk bytes including length and CRC); raise ValueError on bad structure."""
    if data[:8] != SIGNATURE:
        raise ValueError("not a PNG")
    i = 8
    while i < len(data):
        if i + 12 > len(data):
            raise ValueError("truncated chunk header")
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        end = i + 12 + n
        if end > len(data):
            raise ValueError("truncated %s chunk" % kind.decode("latin-1"))
        yield kind, data[i:end]
        i = end
        if kind == b"IEND":
            return
    raise ValueError("no IEND chunk")


def strip(data):
    """Return (new bytes, number of chunks removed)."""
    kept, removed = [SIGNATURE], 0
    for kind, raw in chunks(data):
        if kind in TEXT_CHUNKS:
            removed += 1
        else:
            kept.append(raw)
    return b"".join(kept), removed


def main(argv=None):
    files = sys.argv[1:] if argv is None else argv
    if not files:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    bad = 0
    for path in files:
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            new, removed = strip(data)
        except (OSError, ValueError, struct.error) as e:
            print("%s: not changed (%s)" % (path, e))
            bad += 1
            continue
        if removed:
            with open(path, "wb") as fh:
                fh.write(new)
        print("%s: removed %d chunk(s)" % (path, removed))
    sys.stdout.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
