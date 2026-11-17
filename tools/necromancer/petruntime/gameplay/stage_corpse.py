#!/usr/bin/env python3
"""Add the Undead Army corpse hooks to a staged private roster source tree."""
import argparse
import hashlib
from pathlib import Path
import shutil


def stage(src):
    path = src / 'hd_corpse.c'
    if (path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() !=
            '8fa9fde462ee588838d50c60d82de9fd4f34ad0e85a648839bf752208829cb09'):
        raise ValueError('Private corpse source fingerprint mismatch')
    body = path.read_text(encoding='latin-1')

    def replace(old, new):
        nonlocal body
        if body.count(old) != 1:
            raise ValueError('Unexpected corpse patch anchor: ' + old)
        body = body.replace(old, new)

    replace('#include <limits.h>', '''#include <limits.h>
#ifdef HD_UNDEAD_ARMY_PLAYTEST
#include "hd_army_corpse.h"
#include "hd_pet_roster.h"
#include <time.h>
#endif''')
    replace('    char name[80];', '''    char name[80];
#ifdef HD_UNDEAD_ARMY_PLAYTEST
    hd_army_corpse army;
    int revival_spent;
#endif''')
    replace('    c->name[j] = 0;', '''    c->name[j] = 0;
#ifdef HD_UNDEAD_ARMY_PLAYTEST
    memcpy(c->army.name, c->name, sizeof c->name);
    c->army.level = c->level;
    c->army.hp = c->hp > 0 ? (unsigned)c->hp : 0;
    c->army.mp = c->mp > 0 ? (unsigned)c->mp : 0;
    c->army.strength = MIN((unsigned)MAX(0, victim->strength), HD_ARMY_NATIVE_ATTRIBUTE_MAX);
    c->army.dexterity = MIN((unsigned)MAX(0, victim->dexterity), HD_ARMY_NATIVE_ATTRIBUTE_MAX);
    c->army.constitution = MIN((unsigned)MAX(0, victim->constitution), HD_ARMY_NATIVE_ATTRIBUTE_MAX);
    c->army.intelligence = MIN((unsigned)MAX(0, victim->intelligence), HD_ARMY_NATIVE_ATTRIBUTE_MAX);
    c->army.piety = MIN((unsigned)MAX(0, victim->piety), HD_ARMY_NATIVE_ATTRIBUTE_MAX);
    if (victim->experience > 0)
        c->army.experience = (unsigned long)victim->experience > UINT32_MAX ?
                            UINT32_MAX : (uint32_t)victim->experience;
    if (F_ISSET(victim, MPERMT) || F_ISSET(victim, MDMFOL))
        c->raisable = 0;
#endif''')
    replace('    if (mode == 2 && !strcmp(verb,"raiseskeleton")) {', '''#ifdef HD_UNDEAD_ARMY_PLAYTEST
    if (mode == 2 && !strcmp(verb, "rc")) {
        if (n > 2) return 0;
        if (n == 2) strcpy(number, noun);
        strcpy(noun, "corpse");
        strcpy(verb, "raise");
        ++n;
    }
#endif
    if (mode == 2 && !strcmp(verb,"raiseskeleton")) {''')
    replace('    otag *gold_tag = NULL;', '''#ifdef HD_UNDEAD_ARMY_PLAYTEST
    time_t now = 0;
    const struct lasttime *timer;
#endif
    otag *gold_tag = NULL;''')
    replace('    /* Prepare the normal gold object', '''#ifdef HD_UNDEAD_ARMY_PLAYTEST
    if (mode == 2) {
        if (c->revival_spent) {
            print(player->fd, "That corpse has already been used for a revival attempt.\\n");
            return 0;
        }
        timer = &player->lasttime[HD_ARMY_RAISE_TIMER];
        now = time(NULL);
        if (now <= 0 || (uintmax_t)now > (uintmax_t)LONG_MAX) {
            print(player->fd, "Raise Corpse is unavailable right now.\\n");
            return 0;
        }
        if (timer->interval == HD_ARMY_RAISE_COOLDOWN && timer->ltime > 0) {
            double elapsed = difftime(now, (time_t)timer->ltime);
            if (elapsed < HD_ARMY_RAISE_COOLDOWN) {
                long remaining = elapsed < 0 ? HD_ARMY_RAISE_COOLDOWN :
                                 HD_ARMY_RAISE_COOLDOWN - (long)elapsed;
                print(player->fd, "Raise Corpse is ready in %ld second%s.\\n", remaining, remaining == 1 ? "" : "s");
                return 0;
            }
        }
        if (!hd_army_raise_ready(player, &c->army))
            return 0;
    }
#endif
    /* Prepare the normal gold object''')
    replace('    if (mode == 2 && !hd_necro_raise_from_corpse(player,c->hp,c->mp,c->level)) {',
            '''#ifdef HD_UNDEAD_ARMY_PLAYTEST
    if (mode == 2) {
        unsigned chance = hd_roster_chance(player->level, c->army.level);
        hd_army_corpse raised = c->army;
        player->lasttime[HD_ARMY_RAISE_TIMER].ltime = (long)now;
        player->lasttime[HD_ARMY_RAISE_TIMER].interval = HD_ARMY_RAISE_COOLDOWN;
        c->revival_spent = 1;
        if ((unsigned)mrand(1, 100) > chance) {
            print(player->fd, "The corpse resists your call. Its loot is still here.\\n");
        } else {
            if (mrand(1, 100) <= 5) {
                raised.unique = 1;
                raised.hp = MIN(2 * raised.hp, (unsigned)SHRT_MAX);
                raised.mp = MIN(2 * raised.mp, (unsigned)SHRT_MAX);
                raised.strength = MIN(2 * raised.strength, HD_ARMY_NATIVE_ATTRIBUTE_MAX);
                raised.dexterity = MIN(2 * raised.dexterity, HD_ARMY_NATIVE_ATTRIBUTE_MAX);
                raised.constitution = MIN(2 * raised.constitution, HD_ARMY_NATIVE_ATTRIBUTE_MAX);
                raised.intelligence = MIN(2 * raised.intelligence, HD_ARMY_NATIVE_ATTRIBUTE_MAX);
                raised.piety = MIN(2 * raised.piety, HD_ARMY_NATIVE_ATTRIBUTE_MAX);
            }
            if (hd_army_raise_commit(player, &raised)) {
                if (raised.unique)
                    print(player->fd, "A unique undead %s answers your call!\\n", raised.name);
                goto release_loot;
            }
        }
        if (coins) free_obj(coins);
        free(gold_tag);
        return 0;
    }
release_loot:
#else
    if (mode == 2 && !hd_necro_raise_from_corpse(player,c->hp,c->mp,c->level)) {''')
    replace('    if (gold_tag) { gold_tag->next_tag', '''#endif
    if (gold_tag) { gold_tag->next_tag''')
    header = Path(__file__).with_name('hd_army_corpse.h')
    shutil.copyfile(header, src / header.name)
    path.write_text(body, encoding='latin-1')


def stage_command_and_login(src):
    table = src / 'global.c'
    player = src / 'player.c'
    commands = table.read_text(encoding='latin-1')
    login = player.read_text(encoding='latin-1')
    anchor = '\t{ "loot", 152, hd_corpse_loot },'
    loop = '\tfor(i=0; i<45; i++) {\n\t\tply_ptr->lasttime[i].ltime += tdiff;'
    if commands.count(anchor) != 1 or '"rc"' in commands or login.count(loop) != 1:
        raise ValueError('Unexpected command table or login timer layout')
    commands = commands.replace(anchor, '#ifdef HD_UNDEAD_ARMY_PLAYTEST\n'
        '\t{ "rc", 150, hd_corpse_raise },\n#endif\n' + anchor)
    login = login.replace(loop, '\tfor(i=0; i<45; i++) {\n'
        '#ifdef HD_UNDEAD_ARMY_PLAYTEST\n'
        '\t\tif (i == HD_ARMY_RAISE_TIMER) continue;\n#endif\n'
        '\t\tply_ptr->lasttime[i].ltime += tdiff;')
    login = '#ifdef HD_UNDEAD_ARMY_PLAYTEST\n#include "hd_army_corpse.h"\n#endif\n' + login
    table.write_text(commands, encoding='latin-1')
    player.write_text(login, encoding='latin-1')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    source = parser.parse_args().source
    stage(source)
    stage_command_and_login(source)
