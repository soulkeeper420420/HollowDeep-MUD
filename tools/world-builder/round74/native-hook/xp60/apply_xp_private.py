#!/usr/bin/env python3
# Round 74B private XP/train patch on top of exact Round 74B stat/hprogress candidate.
from pathlib import Path
import hashlib
import shutil
import sys

BASE_HASHES = {'command7.c': '8cc7ce96fadce02e08514848e8a976b4c543f9534d1cff233d226ebd65c7f1e0', 'command4.c': '1c2934dc2f39aec1382973ea9fd468c2a69d41c85b57f5c2ce4d0f9a88567622', 'misc.c': '23dafb30c5b0fa46847af6356cc8b0de822f9fdd325893a94bc908e80caacf7f', 'player.c': '7739f1e60ee92dd96f05b1ff4e77374f009d0dea49c1581d0b9a8f2ae8e677a0', 'creature.c': '772a1d8c11ec955c6de6e1df6aed8a6b40dc3ecae852797a3cf4bcd98c59885c', 'hollowdeep.c': 'e94c2f460097f40eaaf3a64ec647bb060c5cb2c927044cabf6102357e887a6c5', 'command2.c': '3e24addf376880b376d5277358178e2eb5832c8ef8f5a4904b7cc783ddd7ba2c', 'command8.c': '3a1f4ca901c14389b9e859989a8316e6a05e542bd859c4b4c0863d26213f16df', 'command10.c': '26dc86667988e2aaf2da75fcf35cffcaca841d5c87dce7cda6b5047b631b55c4'}
PREV = {'Makefile':'7c61bbc4e856e9248b2342180932292009d6df6733123b377f8d364edfe2f71b',
        'hd74_native.c':'50c76c32f934626fcac169cc1b88c1dd0d0b31fbe41009d73cc02caace7949e8'}

# Non-mutated inputs are also bound to the exact verified Round 74B stage.
VERIFY = {
 'command1.c': 'd4e858d8a6beddc1076483ddcd3e9059a85d1e83dc73a7bd546c40520be1e2d2',
 'global.c': 'd2b9031e0515360abce2f86ebed872fd0e21815fab9ad6db5990ee8fd7fe8a64',
 'hd74_native.h': '007d87ce46a38f4ef13f8298388a959ee2e05ea98f4b673deb08018b0750efc4',
 'hd74_progression.c': 'ba252a8bb6dbf585652d04435cffa2b911d1d49bb4a0b196e5ee0cffff70275e',
 'hd74_progression.h': '0b5a3085f34ee9b9915945f8e41d0542f808d3eec1cec66f0eaf8c8a7144c47c'
}

def repl(s,old,new,label):
    n=s.count(old)
    if n!=1: raise ValueError('%s: anchor count %s, expected 1' % (label,n))
    return s.replace(old,new)

def private_add(old, expr):
    return '#ifdef HD74_PRIVATE_NATIVE\n'+expr+'\n#else\n'+old+'\n#endif'

def main():
    if len(sys.argv)!=3: raise SystemExit('Usage: apply_xp_private.py ROUND74B_DISPOSABLE_SRC THIS_PACKAGE')
    raw=Path(sys.argv[1]); src=raw.resolve(strict=True); pkg=Path(sys.argv[2]).resolve(strict=True)
    if (src.name != 'src' or src.is_symlink() or raw.is_symlink() or
        not any(x.startswith('round74b-') for x in src.parts) or
        str(src).startswith('/srv/') or str(src).startswith('/var/www/') or
        not src.is_dir()): raise SystemExit('Refusing non-disposable source')
    for f,checksum in {**BASE_HASHES,**PREV,**VERIFY}.items():
        path=src/f
        if not path.is_file() or path.is_symlink():raise SystemExit('Missing/symlinked native source: '+f)
        current=hashlib.sha256(path.read_bytes()).hexdigest()
        if current!=checksum: raise SystemExit('Source drift: %s (%s)'%(f,current))
    for f in ('hd74_xp.h','hd74_xp.c'):
        if (src/f).exists() or not (pkg/f).is_file() or (pkg/f).is_symlink():
            raise SystemExit('Invalid destination or source file: '+f)
    original={f:(src/f).read_text(encoding='latin-1') for f in {**BASE_HASHES,**PREV}}
    out=dict(original)
    # All changes are test-gated: unchanged compilation paths remain legacy.
    f='misc.c';s=out[f]
    old='\tint level = 1;\n\t\n\twhile (exp >= needed_exp[level-1] && level < MAXALVL)'
    s=repl(s,old,'\tint level = 1;\n#ifdef HD74_PRIVATE_NATIVE\n\treturn hd74_level_from_xp(exp);\n#else\n\twhile (exp >= needed_exp[level-1] && level < MAXALVL)',f+' exp_to_lev')
    old='\treturn(MAX(1,level));\n}'
    s=repl(s,old,'\treturn(MAX(1,level));\n#endif\n}',f+' end')
    s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes');out[f]=s
    f='command7.c';s=out[f]
    old='\tif(ply_ptr->level < MAXALVL)\n\t\texpneeded = needed_exp[ply_ptr->level-1];\n\telse\n               expneeded = (long)((needed_exp[MAXALVL-1]*ply_ptr->level));   '
    new='#ifdef HD74_PRIVATE_NATIVE\n\texpneeded = hd74_xp_for_next((int)ply_ptr->level);\n\tif (expneeded < 0) {\n\t\tprint(fd, "You have reached the private level cap (60).\\n");\n\t\treturn(0);\n\t}\n#else\n'+old+'\n#endif'
    s=repl(s,old,new,f+' train threshold')
    s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' include');out[f]=s
    f='command4.c';s=out[f]
    old='\tif(ply_ptr->level < MAXALVL)\n\t\texpneeded = needed_exp[ply_ptr->level -1];\n\telse\n\t        expneeded = (long)((needed_exp[MAXALVL-1]*ply_ptr->level));   '
    new='#ifdef HD74_PRIVATE_NATIVE\n\texpneeded = hd74_xp_for_next((int)ply_ptr->level);\n\tif (expneeded < 0) expneeded = ply_ptr->experience; /* Show 0 needed at cap. */\n#else\n'+old+'\n#endif'
    s=repl(s,old,new,f+' info threshold')
    s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
    anchor='\tprint(fd, "Magic Points: %-4d/%-4d               Gold: %-7lu\\n",'
    s=repl(s,anchor,'#ifdef HD74_PRIVATE_NATIVE\n\tif (ply_ptr->level >= HD74_LEVEL_CAP) print(fd, "Round 74 private level cap reached.\\n");\n#endif\n'+anchor,f+' cap info');out[f]=s
    f='player.c';s=out[f]
    s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
    anchor='\tply_ptr->level++;\n\tply_ptr->hpmax += class_stats[ply_ptr->class].hp;'
    s=repl(s,anchor,'#ifdef HD74_PRIVATE_NATIVE\n\t/* Only trainable level-ups, not initial character creation (level 0). */\n\tif (ply_ptr->level >= HD74_LEVEL_CAP) return;\n#endif\n'+anchor,f+' up_level hard cap');out[f]=s
    f='hollowdeep.c';s=out[f]
    s=repl(s,'#include "mstruct.h"','#include "mstruct.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
    old='''    if (level < MAXALVL) {
        required = needed_exp[level - 1];
    } else {
        /* The original on-disk ABI uses signed 32-bit long values. */
        if (needed_exp[MAXALVL - 1] < 0 ||
            needed_exp[MAXALVL - 1] > 2147483647L / (long)level) {
            print(player->fd, "Training requirements exceed the original engine's supported range.\\n");
            return 0;
        }
        required = needed_exp[MAXALVL - 1] * (long)level;
    }'''
    new='''#ifdef HD74_PRIVATE_NATIVE
    required = hd74_xp_for_next((int)level);
    if (required < 0) {
        print(player->fd, "Round 74 private level cap reached; training disabled here.\\n");
        return 0;
    }
#else
'''+old+'''\n#endif'''
    s=repl(s,old,new,f+' class progress')
    out[f]=s
    f='creature.c';s=out[f]
    s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
    old='''		if (n > 1)
			if ( crt_ptr->level < (MAXALVL+2))
				crt_ptr->experience = needed_exp[crt_ptr->level-3];
			else
			    crt_ptr->experience = 
			    (long)((needed_exp[MAXALVL-1]*(crt_ptr->level-2)));   '''
    new='''#ifdef HD74_PRIVATE_NATIVE
                if (n > 1) {
                    long floor = hd74_xp_for_level((int)crt_ptr->level-1);
                    if (floor < 0) floor=0;
                    crt_ptr->experience=floor;
                }
#else
'''+old+'''\n#endif'''
    s=repl(s,old,new,f+' death penalty xp floor')
    for old,code,label in [
      ('ply_ptr->experience += expdiv;','ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,expdiv);','monster reward'),
      ('att_ptr->experience += xpv;','att_ptr->experience = hd74_xp_add_bounded(att_ptr->experience,xpv);','pvp reward')]:
        s=repl(s,old,private_add(old,code),f+' '+label)
    out[f]=s
    for f,pairs in {
        'command2.c':[('ply_ptr->experience += quest_exp[obj_ptr->questnum-1];', 'ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,quest_exp[obj_ptr->questnum-1]);'),
                      ('ply_ptr->experience += \n\t\t\t\t\tquest_exp[obj_ptr->questnum-1];','ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,quest_exp[obj_ptr->questnum-1]);')],
        'command8.c':[('ply_ptr->experience += quest_exp[obj_ptr->questnum-1];','ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,quest_exp[obj_ptr->questnum-1]);')],
        'command10.c':[('ply_ptr->experience += amte;','ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,amte);'),
                       ('ply_ptr->experience += quest_exp[trd_ptr->questnum-1];','ply_ptr->experience = hd74_xp_add_bounded(ply_ptr->experience,quest_exp[trd_ptr->questnum-1]);')]}.items():
        s=out[f];s=repl(s,'#include "mextern.h"','#include "mextern.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
        for old,new in pairs:s=repl(s,old,private_add(old,new),f+' xp grant')
        out[f]=s
    f='Makefile';s=out[f]
    s=repl(s,'OBJECTS += hd74_native.o hd74_progression.o','OBJECTS += hd74_native.o hd74_progression.o hd74_xp.o',f+' object list');out[f]=s
    f='hd74_native.c';s=out[f]
    s=repl(s,'#include "hd74_progression.h"','#include "hd74_progression.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_xp.h"\n#endif',f+' includes')
    # Original read-only command becomes an accurate private-training status.
    s=repl(s,'HOLLOWDEEP ROUND 74 DEVELOPMENT PREVIEW','HOLLOWDEEP ROUND 74 PRIVATE TRAINING',f+' header')
    s=repl(s,'Proposed XP for level %u: %lu | Missing: %ld','Private XP for level %u: %lu | Missing: %ld',f+' threshold label')
    s=repl(s,'"NOT ACTIVE: legacy train/XP, class skills, remort and rewards are unchanged.\\n"',
           '"PRIVATE TRAINING: XP/level cap active in disposable build; class skills, remort and rewards unchanged.\\n"',f+' truth in status')
    out[f]=s
    # Validate all exact anchors before any disk modifications.
    for f in out:
        if out[f]==original[f]: raise SystemExit('Missing patch: '+f)
    for f,body in out.items():
        (src/f).write_text(body,encoding='latin-1')
    for f in ('hd74_xp.c','hd74_xp.h'):shutil.copyfile(pkg/f,src/f)
    print('ROUND 74B: guarded level-60 training/score/death/XP cap hooks staged privately')
    print('REMORT/SKILL/SAVE: UNCHANGED; production deployment NONE')

if __name__=='__main__':main()
