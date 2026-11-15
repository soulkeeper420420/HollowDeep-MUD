"""Private Round 71 validation of 100-room grids and failure atomicity."""
import copy
import json
import sys

import app
import round71_wilderness as wild


def expect_failure(label, fn):
    try:
        fn()
    except (ValueError, TypeError) as exc:
        print('PASS: Rejected', label, '-', str(exc), flush=True)
    else:
        raise AssertionError('Invalid wilderness configuration accepted: ' + label)


def test():
    assert app.area.EXTENDED_ROOMS and app.area.PLAN_CAPACITY >= 102
    original = app.new_plan(14, 15)
    saved = json.dumps(original, sort_keys=True)
    region = wild.grid(original, 14, 10001, 10, 10, 'up', 'HollowDeep Wilds')
    assert json.dumps(original, sort_keys=True) == saved, 'Input plan mutated'
    assert len(region['rooms']) == 102
    app.clean(region)
    ids = [room['room_id'] for room in region['rooms']]
    assert len(ids) == len(set(ids)) and ids[-1] == 10100
    as_ids = {room['room_id']: room for room in region['rooms']}
    assert as_ids[14]['name'] == original['rooms'][0]['name']
    for rid in range(10001, 10101):
        room = as_ids[rid]
        assert room['new_room'] is True and room['monsters'] == room['objects'] == []
        for direction in room['exits']:
            dest = direction['destination']
            reverse = wild.OPPOSITE[direction['direction']]
            assert any(e['direction'] == reverse and e['destination'] == rid for e in as_ids[dest]['exits'])
    print('ROUND 71: validated connected 100-room wilderness batch PASS', flush=True)

    expect_failure('reserved 9000', lambda: wild.grid(original, 14, 9000, 2, 2, 'up', 'Wilds'))
    expect_failure('reserved 9999', lambda: wild.grid(original, 14, 9999, 2, 2, 'up', 'Wilds'))
    expect_failure('out-of-range 15999 batch', lambda: wild.grid(original, 14, 15999, 2, 2, 'up', 'Wilds'))
    expect_failure('boolean room ID', lambda: wild.grid(original, 14, True, 2, 2, 'up', 'Wilds'))
    expect_failure('too many rows', lambda: wild.grid(original, 14, 10001, 11, 2, 'up', 'Wilds'))
    expect_failure('unsafe region name', lambda: wild.grid(original, 14, 10001, 2, 2, 'up', '../Bad'))
    expect_failure('nonexistent anchor', lambda: wild.grid(original, 17, 10001, 2, 2, 'up', 'Wilds'))
    expect_failure('duplicate ID', lambda: wild.grid(region, 15, 10001, 2, 2, 'up', 'Wilds'))
    expect_failure('occupied entrance', lambda: wild.grid(region, 14, 10150, 2, 2, 'up', 'Wilds'))
    assert json.dumps(original, sort_keys=True) == saved, 'Failed operation mutated original'
    print('ROUND 71: collision, unsafe input and atomic rejection PASS', flush=True)


if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
