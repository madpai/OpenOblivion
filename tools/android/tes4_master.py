#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stream the records of a TES4 plugin in file order (private build input).

Records inside GRUPs are yielded in the order they appear, so a consumer that
needs a parent (an INFO belongs to the DIAL before it) tracks it itself.
"""
import struct
import zlib


class Record:
    __slots__ = ('type', 'formid', 'flags', 'subs')

    def __init__(self, type_, formid, flags, subs):
        self.type = type_
        self.formid = formid
        self.flags = flags
        self.subs = subs

    def first(self, tag, default=None):
        for name, data in self.subs:
            if name == tag:
                return data
        return default

    def all(self, tag):
        return [data for name, data in self.subs if name == tag]

    def editor_id(self):
        raw = self.first(b'EDID')
        return raw.rstrip(b'\0').decode('latin1') if raw else None

    def full_name(self):
        raw = self.first(b'FULL')
        return raw.rstrip(b'\0').decode('latin1') if raw else None


def subrecords(body):
    position, result, long_size = 0, [], None
    while position + 6 <= len(body):
        tag = body[position:position + 4]
        size = struct.unpack_from('<H', body, position + 4)[0]
        if tag == b'XXXX':
            long_size = struct.unpack_from('<I', body, position + 6)[0]
            position += 10
            continue
        if long_size is not None:
            size, long_size = long_size, None
        result.append((tag, body[position + 6:position + 6 + size]))
        position += 6 + size
    return result


def records(path, wanted=None):
    """Yield Records in file order; `wanted` is an optional set of 4-byte types."""
    data = path.read_bytes() if hasattr(path, 'read_bytes') else open(path, 'rb').read()
    position = 0
    while position < len(data):
        tag = data[position:position + 4]
        size = struct.unpack_from('<I', data, position + 4)[0]
        if tag == b'GRUP':
            position += 20  # descend: the group's records follow its header
            continue
        flags, formid = struct.unpack_from('<II', data, position + 8)
        body = data[position + 20:position + 20 + size]
        position += 20 + size
        if wanted is not None and tag not in wanted:
            continue
        if flags & 0x40000:
            body = zlib.decompress(body[4:])
        yield Record(tag, formid, flags, subrecords(body))
