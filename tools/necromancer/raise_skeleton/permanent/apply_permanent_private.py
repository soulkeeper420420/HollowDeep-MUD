#!/usr/bin/env python3
"""Stage corpse-HP/MP, untimed skeletal allies and healing in disposable native source.

Run AFTER the published Raise Skeleton private patch and pinned Necromancer
identity prototype. Every input is SHA-checked before any source mutation.
"""
from pathlib import Path
import hashlib
import shutil
import sys

BASE_SHA256 = {
    "hd_necro_skeleton.c": "f5fd9afcb7aeec17169905f7e6339d8f3df688c613fce6677da4aa676d8d6a46",
    "hd_necro_skeleton.h": "ac209c240ba9556c81e84c54fa7053052ec24f42e24ab6505f8ebfc9424c23a8",
    "creature.c": "9a1c158811a1c96d4f0190f4c88876afb9dc16d1edba12e08a4dcc18c7f21243",
    "command1.c": "1e60aedd9f21b7700663268668fcff56c4320f0f83ca6fb61cea1736e0ee3356",
    "magic1.c": "e2f5e8bc59b74ea3cbe0b467903990800b27b588e7c6ffa58fb5a3ba3d9c3585",
    "magic2.c": "1b3cffcead2bb037425f181fc72bb90ecc11bd16baeabec9702bf458a273ced1",
    "magic3.c": "a044f83e1d82fe5ebfc41b609c78d4a982062934822d3e00f9fa4aa9c044ca65",
}

# Two *coupled*, exact source profiles are approved.  The integrated version
# was recovered from the operator's complete creature.c diff and reproduced
# byte-for-byte from the pinned original archive (SHA-256 verified).
# command1.c's paired fingerprint is the exact output from the same private
# Linode candidate. We do not accept a mixture or arbitrary new source edits.
ROUND74B_INTEGRATED_SHA256 = {
    "creature.c": "6df6f74bce702363c9eae7506d96c962b9b3e3d3e178f07f7ea61015b07c9001",
    "command1.c": "c8525fb2615c49e9c5cebcf321b83b28a3eaa0fea2a8c8bb372904bef20ddd1e",
}
PROFILE_FILES = ("creature.c", "command1.c")

def accepted_source_profile(hashes):
    current = tuple(hashes[name] for name in PROFILE_FILES)
    if current == tuple(BASE_SHA256[name] for name in PROFILE_FILES):
        return "first-skill-only"
    if current == tuple(ROUND74B_INTEGRATED_SHA256[name] for name in PROFILE_FILES):
        return "round74b-integrated"
    return None


def repl(source, old, new, title):
    n = source.count(old)
    if n != 1:
        raise ValueError('%s: anchor count %d' % (title, n))
    return source.replace(old,new)

def main():
    if len(sys.argv) != 3: raise SystemExit('Usage: apply_permanent_private.py NECROMANCER_DISPOSABLE_SRC THIS_PACKAGE')
    raw = Path(sys.argv[1]); src=raw.resolve(strict=True); pkg=Path(sys.argv[2]).resolve(strict=True)
    if (raw.is_symlink() or src.is_symlink() or src.name!='src' or
        not src.parent.name.startswith('necromancer-playtest-') or
        any(str(src).startswith(prefix) for prefix in ['/srv/','/var/www/','/usr/','/etc/','/opt/'])):
        raise SystemExit('Refusing non-disposable source')
    actual_hashes = {}
    for name, sha in BASE_SHA256.items():
        p = src / name
        if not p.is_file() or p.is_symlink():
            raise SystemExit('Source missing or symlinked: ' + name)
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        actual_hashes[name] = actual
        if name not in PROFILE_FILES and actual != sha:
            raise SystemExit(
                'Source SHA mismatch: %s\nExpected: %s\nActual:   %s\n'
                'No source files were changed; do not force-patch.'
                % (name, sha, actual))
    profile = accepted_source_profile(actual_hashes)
    if profile is None:
        raise SystemExit(
            'Refusing unknown or mixed creature.c + command1.c source profiles.\n'
            'Expected first-skill pair: %s / %s\n'
            'Approved Round74B pair: %s / %s\n'
            'Actual pair: %s / %s\nNo source files were changed.'
            % (BASE_SHA256['creature.c'], BASE_SHA256['command1.c'],
               ROUND74B_INTEGRATED_SHA256['creature.c'],
               ROUND74B_INTEGRATED_SHA256['command1.c'],
               actual_hashes['creature.c'], actual_hashes['command1.c']))
    if profile == 'round74b-integrated':
        # No reversion of first-life death, quest XP, or five-level banking.
        for name in ('hd74_xp.c', 'hd74_xp.h'):
            p = src / name
            if not p.is_file() or p.is_symlink():
                raise SystemExit('Missing trusted Round74B helper: ' + name)
        native = (src / 'creature.c').read_text('latin-1')
        creation = (src / 'command1.c').read_text('latin-1')
        for term in ('hd74_xp_add_banked(', 'hd74_verified_remorts(',
                     'hd74_level_from_xp_for_life(', 'hd74_xp_for_life_next('):
            if term not in native:
                raise SystemExit('Round74B source contract missing: ' + term)
        if 'hd_store_create_necromancer(' not in creation:
            raise SystemExit('Necromancer creation contract missing')
    print('NECROMANCER: accepted exact private input profile: ' + profile)
    for f in ('hd_necro_skeleton.c','hd_necro_skeleton.h'):
        if not (pkg/f).is_file() or (pkg/f).is_symlink(): raise SystemExit('Untrusted missing package: '+f)
    out={f:(src/f).read_text('latin-1') for f in BASE_SHA256 if f not in ('hd_necro_skeleton.c','hd_necro_skeleton.h')}
    # The pet is NEVER a loot, XP or corpse source. Check before all death hooks.
    f='creature.c';s=out[f]
    s=repl(s, '   str[0] =0;\n    hd_treasure_guardian_death(crt_ptr, att_ptr);',
'''#ifdef HD_NECROMANCER_PLAYTEST
    if (hd_necro_skeleton_is_pet(crt_ptr)) {
        if (crt_ptr->parent_rom)
            del_crt_rom(crt_ptr, crt_ptr->parent_rom);
        free_crt(crt_ptr);
        return;
    }
    hd_necro_skeleton_record_kill(crt_ptr, att_ptr);
#endif
   str[0] =0;
    hd_treasure_guardian_death(crt_ptr, att_ptr);''',f+' death')
    s=repl(s,
'''#ifdef HD_NECROMANCER_PLAYTEST
        hd_necro_skeleton_logout(crt_ptr);
#endif''',
'''#ifdef HD_NECROMANCER_PLAYTEST
        /* Owner death is not skeleton death: keep the pet alive. */
#endif''', f+' owner death persistence')
    out[f]=s
    # Rebind a surviving in-process pet to the new creature object on login.
    f='command1.c';s=out[f]
    s=repl(s,'#include "mextern.h"', '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif',f+' include')
    s=repl(s, '\t\t\tinit_ply(Ply[fd].ply);\n\t\t\tRETURN(fd, command, 1);',
'''\t\t\tinit_ply(Ply[fd].ply);
#ifdef HD_NECROMANCER_PLAYTEST
            hd_necro_skeleton_reconnect(Ply[fd].ply);
#endif
\t\t\tRETURN(fd, command, 1);''',f+' relog')
    out[f]=s
    # Potion feeding: targeted healing POTION may use only the owner's pet;
    # command syntax "drink <potion> on skeleton". Other potions unchanged.
    f='magic1.c';s=out[f]
    s=repl(s,'#include "mextern.h"', '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif',f+' include')
    start=s.index("int drink(");end=s.index("int zap(")
    dr=s[start:end]
    dr=repl(dr,'    int fd, n, match=0, c, splno;\n\n    fd = ply_ptr->fd;',
'''    int fd, n, match=0, c, splno;
#ifdef HD_NECROMANCER_PLAYTEST
    int target_pet = 0;
    cmd target_command;
#endif

    fd = ply_ptr->fd;''',f+' vars')
    dr=repl(dr,
'''    splno = obj_ptr->magicpower-1;
    fn = spllist[splno].splfn;

    if(fn == offensive_spell) {''',
'''    splno = obj_ptr->magicpower-1;
    fn = spllist[splno].splfn;
#ifdef HD_NECROMANCER_PLAYTEST
    if (cmnd->num == 4 && !strcmp(cmnd->str[2], "on") &&
        !strcmp(cmnd->str[3], "skeleton")) {
        if (!hd_necro_skeleton_can_heal(ply_ptr) ||
            !(spllist[splno].splno == SVIGOR ||
              spllist[splno].splno == SMENDW ||
              spllist[splno].splno == SRESTO)) {
            print(fd, "You may only pour healing potions onto your own living skeleton.\\n");
            return 0;
        }
        target_pet = 1;
        target_command = *cmnd;
        target_command.num = 3;
        strcpy(target_command.str[2], "skeleton");
        target_command.val[2] = 1;
    }
    if (target_pet)
        n = (*fn)(ply_ptr, &target_command, WAND);
    else
#endif
    if(fn == offensive_spell) {''',f+' potion targeting')
    dr=repl(dr,
'''        print(fd, "Potion drank.\\n");
        broadcast_rom(fd, ply_ptr->rom_num, "%M drank %1i.", 
                  ply_ptr, obj_ptr);''',
'''#ifdef HD_NECROMANCER_PLAYTEST
        if (target_pet) {
            print(fd, "Healing potion poured on your skeleton.\\n");
            broadcast_rom(fd, ply_ptr->rom_num,
                          "%M used a potion on a skeleton.", ply_ptr);
        } else
#endif
        {
            print(fd, "Potion drank.\\n");
            broadcast_rom(fd, ply_ptr->rom_num, "%M drank %1i.",
                          ply_ptr, obj_ptr);
        }''',f+' potion message')
    out[f]=s[:start]+dr+s[end:]
    # Vigor/Mend already heal monsters; don't attempt output on fd=-1.
    f='magic2.c';s=out[f]
    s=repl(s,'            print(crt_ptr->fd, "%M casts a vigor spell on you.\\n",\n                  ply_ptr);',
'''#ifdef HD_NECROMANCER_PLAYTEST
            if (crt_ptr->fd >= 0)
#endif
            print(crt_ptr->fd, "%M casts a vigor spell on you.\\n",
                  ply_ptr);''',f+' vigor')
    s=repl(s,'            print(crt_ptr->fd, \n                  "%M casts a mend-wounds spell on you.\\n", ply_ptr);',
'''#ifdef HD_NECROMANCER_PLAYTEST
            if (crt_ptr->fd >= 0)
#endif
            print(crt_ptr->fd, "%M casts a mend-wounds spell on you.\\n", ply_ptr);''',f+' mend')
    # The original short hpcur arithmetic wraps near SHRT_MAX on healing.
    # Use int intermediate for summoned high-HP monsters only.
    old_heal = ('        crt_ptr->hpcur += MAX(1, heal);\n\n'
                '        if(crt_ptr->hpcur > crt_ptr->hpmax)\n'
                '            crt_ptr->hpcur = crt_ptr->hpmax;')
    new_heal = '''#ifdef HD_NECROMANCER_PLAYTEST
        if (hd_necro_skeleton_is_pet(crt_ptr))
            crt_ptr->hpcur = (short)MIN((int)crt_ptr->hpmax,
                                        (int)crt_ptr->hpcur + MAX(1, heal));
        else
#endif
        {
            crt_ptr->hpcur += MAX(1, heal);
            if(crt_ptr->hpcur > crt_ptr->hpmax)
                crt_ptr->hpcur = crt_ptr->hpmax;
        }'''
    if s.count(old_heal)!=2: raise SystemExit('Unknown native healer patterns')
    s=s.replace(old_heal,new_heal)
    out[f]=s
    # Restore is normally player-only. Allow wand/potion on an authenticated
    # Necromancer pet, guarding the same monster fd issue.
    f='magic3.c';s=out[f]
    s=repl(s,'#include "mextern.h"', '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif',f+' include')
    start=s.index('int restore(')
    end=s.index('int befuddle(',start)
    body=s[start:end]
    old = ('\t\tcrt_ptr = find_crt(ply_ptr, rom_ptr->first_ply,\n'
           '\t\t\t\t   cmnd->str[2], cmnd->val[2]);')
    new = old + '''
#ifdef HD_NECROMANCER_PLAYTEST
        if (!crt_ptr && hd_necro_skeleton_can_heal(ply_ptr)) {
            cmnd->str[2][0] = low(cmnd->str[2][0]);
            crt_ptr = find_crt(ply_ptr, rom_ptr->first_mon,
                               cmnd->str[2], cmnd->val[2]);
            if (crt_ptr && !hd_necro_skeleton_is_pet(crt_ptr)) crt_ptr = NULL;
        }
#endif'''
    body=repl(body,old,new,f+' restore target')
    old = ('\t\t\tprint(crt_ptr->fd, \n'
           '\t\t\t      "%M casts a restore spell on you.\\n", ply_ptr);')
    new = '''#ifdef HD_NECROMANCER_PLAYTEST
            if (crt_ptr->fd >= 0)
#endif
''' + old
    body=repl(body,old,new,f+' restore fd')
    # Saturate a high-HP skeleton before converting back to native short.
    old_heal = ('\t\tcrt_ptr->hpcur += dice(2,10,0);\n'
                '\t\tcrt_ptr->hpcur = MIN(crt_ptr->hpcur, crt_ptr->hpmax);')
    new_heal = '''#ifdef HD_NECROMANCER_PLAYTEST
        if (hd_necro_skeleton_is_pet(crt_ptr)) {
            int amount = dice(2,10,0);
            crt_ptr->hpcur = (short)MIN((int)crt_ptr->hpmax,
                                        (int)crt_ptr->hpcur + amount);
        } else
#endif
        {
            crt_ptr->hpcur += dice(2,10,0);
            crt_ptr->hpcur = MIN(crt_ptr->hpcur, crt_ptr->hpmax);
        }'''
    body=repl(body,old_heal,new_heal,f+' restore saturation')
    out[f] = s[:start]+body+s[end:]
    # All patches must be valid before writing. No binary ABI changes.
    if any(out[f]==(src/f).read_text('latin-1') for f in out):
        raise SystemExit('A native source file was not changed')
    for f,content in out.items(): (src/f).write_text(content,'latin-1')
    for f in ('hd_necro_skeleton.c','hd_necro_skeleton.h'):
        shutil.copyfile(pkg/f,src/f)
    print('NECROMANCER: no-timer corpse HP/MP and healing patch staged privately')
    print('No live world, service, player files or class-ID edits')

if __name__=='__main__':main()
