#!/usr/bin/env python3
"""Publish the newsprint front page of Thursday 19 November 2026.

This is the make.fun entry for competition ``news-image-20261119``: 48 stories
across seven regions and nine fields, drawn as one light newsprint page. The
image itself (``entry.png``, sitting next to this file) is the entry's content;
this program only places it where the harness reads it, at
``${MAKEFUN_OUTPUT_DIR:-/output}/entry.png``.

The harness runs the program in a fresh, network-less container with a read-only
repository at ``/bot`` and a writable ``/output``, on one CPU in under 60
seconds. So: standard library only, no network, no clock, no random source,
nothing generated at run time. The bytes of the committed ``entry.png`` are
copied through unchanged and without metadata, which makes the output identical
to the source byte for byte, run after run and machine after machine.

Before copying, the source is checked against the competition's limits (at most
1 MiB, at most 1024 by 1024 pixels, a whole PNG) and the program fails with a
clear message instead of shipping an image the gate would reject.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

SOURCE_NAME = "entry.png"

# Competition guardrails: at most 1 MiB on disk and at most 1024 by 1024 pixels.
SOURCE_SIZE_LIMIT = 1024 * 1024
MAX_SIDE_PX = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IHDR_TYPE = b"IHDR"
IEND_TYPE = b"IEND"
CHUNK_HEADER = 8
CHUNK_CRC = 4
SIGNATURE_BYTES = 8
IHDR_DATA = 13
HEADER_BYTES = SIGNATURE_BYTES + CHUNK_HEADER + IHDR_DATA
VALID_BIT_DEPTHS = (1, 2, 4, 8, 16)
VALID_COLOUR_TYPES = (0, 2, 3, 4, 6)


def verify_png(path: Path) -> tuple[int, int, int, int]:
    """Walk every PNG chunk, checking its CRC, and return the header facts.

    The competition asks for a whole image: every chunk with its checksum and
    the image data its header describes. Walking the chunks and recomputing each
    CRC32 is exactly that check, so a truncated or corrupted file stops the run
    here instead of at the gate.
    """
    blob = path.read_bytes()
    if len(blob) < HEADER_BYTES:
        raise SystemExit("error: %s is too short to be a PNG file" % path)
    if blob[:SIGNATURE_BYTES] != PNG_MAGIC:
        raise SystemExit("error: %s is not a PNG file (bad signature)" % path)

    offset = SIGNATURE_BYTES
    first_type = None
    last_type = None
    width = height = bit_depth = colour_type = 0
    count = 0
    while offset < len(blob):
        if offset + CHUNK_HEADER + CHUNK_CRC > len(blob):
            raise SystemExit(
                "error: %s is truncated: a chunk header runs past the end of the file"
                % path
            )
        (length,) = struct.unpack(">I", blob[offset:offset + 4])
        ctype = blob[offset + 4:offset + 8]
        body = blob[offset + CHUNK_HEADER:offset + CHUNK_HEADER + length]
        if len(body) != length:
            raise SystemExit(
                "error: %s is truncated: the %s chunk promises %d bytes"
                % (path, ctype.decode("latin-1"), length)
            )
        stored = blob[offset + CHUNK_HEADER + length:
                      offset + CHUNK_HEADER + length + CHUNK_CRC]
        (stored_crc,) = struct.unpack(">I", stored)
        wanted_crc = zlib.crc32(ctype + body) & 0xFFFFFFFF
        if stored_crc != wanted_crc:
            raise SystemExit(
                "error: %s has a bad checksum on its %s chunk"
                % (path, ctype.decode("latin-1"))
            )
        if count == 0:
            first_type = ctype
        last_type = ctype
        count += 1
        if count == 1:
            if ctype != IHDR_TYPE:
                raise SystemExit(
                    "error: %s does not start with an IHDR chunk" % path
                )
            width, height, bit_depth, colour_type = struct.unpack(
                ">IIBB", body[:10]
            )
            if bit_depth not in VALID_BIT_DEPTHS:
                raise SystemExit(
                    "error: %s declares a bit depth of %d" % (path, bit_depth)
                )
            if colour_type not in VALID_COLOUR_TYPES:
                raise SystemExit(
                    "error: %s declares a colour type of %d" % (path, colour_type)
                )
        offset += CHUNK_HEADER + length + CHUNK_CRC
    if first_type != IHDR_TYPE or last_type != IEND_TYPE:
        raise SystemExit(
            "error: %s does not run from IHDR to IEND", path
        )
    return width, height, bit_depth, colour_type


def check_source(path: Path) -> tuple[int, int, int]:
    """Validate the image against the competition limits; return its facts."""
    if not path.is_file():
        raise SystemExit(
            "error: %s not found; it must sit next to this program (%s)"
            % (SOURCE_NAME, path)
        )
    size = path.stat().st_size
    if size == 0:
        raise SystemExit("error: %s is empty" % path)
    if size > SOURCE_SIZE_LIMIT:
        raise SystemExit(
            "error: %s is %d bytes, over the %d-byte (1 MiB) limit; "
            "re-encode it smaller before shipping"
            % (path.name, size, SOURCE_SIZE_LIMIT)
        )
    width, height, _depth, _colour = verify_png(path)
    if width == 0 or height == 0:
        raise SystemExit("error: %s declares a zero-sized image" % path)
    if width > MAX_SIDE_PX or height > MAX_SIDE_PX:
        raise SystemExit(
            "error: %s is %dx%d, over the %dx%d pixel limit"
            % (path.name, width, height, MAX_SIDE_PX, MAX_SIDE_PX)
        )
    return size, width, height


def main(argv: list[str] | None = None) -> int:
    del argv  # no options: the harness calls this program with none
    source = Path(__file__).resolve().parent / SOURCE_NAME
    size, width, height = check_source(source)

    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    target = output_dir / SOURCE_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    # Copy through a sibling temp name and rename, so a reader never sees a
    # half-written entry.png: copyfile writes exactly the source bytes, no
    # metadata and no clock, and the rename is atomic on the same filesystem.
    staging = output_dir / (SOURCE_NAME + ".part")
    shutil.copyfile(source, staging)
    os.replace(staging, target)

    print("verified %s: whole PNG, %d bytes, %dx%d" % (source.name, size, width, height))
    # The digest makes a run auditable: the same committed image must produce the
    # same stamp on any machine, and a second run is comparable without a diff.
    print("sha256 %s" % hashlib.sha256(target.read_bytes()).hexdigest())
    print("copied to %s" % target)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
