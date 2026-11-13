import json
from pathlib import Path
import struct


def normalize_entities(parsed):
    layout = Path(__file__).with_name('entity_layout.json')
    obj_size, crt_size, obj_pointers, crt_pointers, ready, ready_size, width = json.loads(layout.read_text())
    if (obj_size, crt_size, width) != (352, 1184, 4):
        raise ValueError('Unsupported native entity ABI')

    def normalize(records, count, creature=False):
        data = bytearray(records)
        pos = 0

        def record(is_creature=False):
            nonlocal pos
            pointers = crt_pointers if is_creature else obj_pointers
            for offset in pointers:
                data[pos + offset:pos + offset + width] = bytes(width)
            if is_creature:
                data[pos + ready:pos + ready + ready_size] = bytes(ready_size)
            pos += crt_size if is_creature else obj_size
            children, = struct.unpack_from('<i', data, pos)
            pos += 4
            for _ in range(children):
                record()

        for _ in range(count):
            record(creature)
        if pos != len(data):
            raise ValueError('Unexpected native entity record boundary')
        return bytes(data)

    result = dict(parsed)
    for key in ('creatures', 'objects'):
        result[key] = normalize(parsed[key], parsed[key + '_count'], key == 'creatures')
    return result
