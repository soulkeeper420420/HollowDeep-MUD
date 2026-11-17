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
    if (victim->experience > 0)
        c->army.experience = (unsigned long)victim->experience > UINT32_MAX ?
                            UINT32_MAX : (uint32_t)victim->experience;
    if (F_ISSET(victim, MPERMT) || F_ISSET(victim, MDMFOL))
        c->raisable = 0;
#endif''')
    replace('    /* Prepare the normal gold object', '''#ifdef HD_UNDEAD_ARMY_PLAYTEST
    if (mode == 2) {
        if (c->revival_spent) {
            print(player->fd, "That corpse has already been used for a revival attempt.\\n");
            return 0;
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
        c->revival_spent = 1;
        if ((unsigned)mrand(1, 100) > chance) {
            print(player->fd, "The corpse resists your call. Its loot is still here.\\n");
        } else if (hd_army_raise_commit(player, &c->army)) {
            goto release_loot;
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    stage(parser.parse_args().source)
