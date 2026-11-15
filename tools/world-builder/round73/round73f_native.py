"""Round 73F: actual native in-game showmap replay on disposable world."""
import secrets
import string


def replay(stage, scope, check):
    root = stage / 'mapped/rootfs'
    assert root.name == 'rootfs' and (root / 'rooms/wilderness.map').is_file()
    scope.update(root=root, PORT=4052, process=None, clients=[])
    scope['start_server']()
    try:
        token = lambda n: ''.join(secrets.choice(string.ascii_lowercase) for _ in range(n))
        player = scope['new_character']('Hd' + token(7), 'Test' + token(9))
        command = lambda value: scope['command'](player, value).lower()
        marker = 'copperreach (column '
        check('automatic wilderness map is off' in command('showmap status'),
              'Showmap disabled by default in native session')
        old = command('north')
        check('goldenrod avenue' in old and marker not in old,
              'Old-world movement does not show a map by default')
        entry = command('up')
        check('copperreach 1,1' in entry and marker not in entry,
              'Wilderness arrival keeps auto-map disabled by default')
        check('automatic wilderness map is now on' in command('showmap on'),
              'Showmap on accepts text argument in native parser')
        check('automatic wilderness map is on' in command('showmap status'),
              'Showmap status reflects enabled setting')
        check(marker not in command('look'),
              'Look does not trigger unsolicited automatic map redraw')
        check(marker not in command('west'),
              'Blocked wilderness movement does not trigger map redraw')
        go_east = command('go east')
        check('copperreach 1,2' in go_east and
              'copperreach (column 2, row 1)' in go_east and go_east.count(marker) == 1,
              'Native go/enter wrapper redraws map exactly once on successful exit')
        back = command('west')
        check('copperreach 1,1' in back and
              'copperreach (column 1, row 1)' in back and back.count(marker) == 1,
              'Native directional move redraws map exactly once')
        check('automatic wilderness map is now off' in command('showmap off'),
              'Explicit off disables automatic redraw')
        check(marker not in command('east'),
              'Disabled showmap preserves original wilderness movement')
        check('automatic wilderness map is now on' in command('showmap'),
              'Bare showmap toggles on')
        check(marker in command('west'), 'Toggle-on redraws again')
        check('map radius set to 0' in command('mapradius 0'),
              'Showmap respects native radius-off setting')
        check(marker not in command('east'),
              'Radius zero suppresses automatic redraw')
        check('map radius set to 1' in command('mapradius 1'),
              'Showmap shares user radius session setting')
        small = command('west')
        check(small.count(marker) == 1 and 'copperreach (column 1, row 1)' in small,
              'Auto map resumes with custom radius 1')
        check('use showmap on, off, toggle, or status' in command('showmap on extra'),
              'Invalid showmap multi-token input is rejected')
        check('automatic wilderness map is on' in command('showmap status'),
              'Invalid showmap input does not change setting')
        down = command('down')
        check('goldenrod avenue' in down and marker not in down,
              'Leaving wilderness produces no automatic map')
        check(marker not in command('look'),
              'Old-world look remains unaffected')
    finally:
        for client in scope['clients']:
            client.close()
        scope['stop_server']()
    print('ROUND 73F: native showmap movement, named-go, toggle, radius and suppression PASS',flush=True)
