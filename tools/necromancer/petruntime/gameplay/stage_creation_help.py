"""Private new-character attribute and help integration."""
from pathlib import Path
import re
import shutil

HERE=Path(__file__).resolve().parent

def stage(source):
    p=source/'command1.c'
    s=p.read_text(encoding='latin-1')

    identity="Ply[fd].extr->tempstr[1][0] == 'n'"

    assert identity in s
    assert 'hd_store_create_necromancer(' in s

    anchor='#include "mextern.h"'
    assert s.count(anchor)==1

    s=s.replace(anchor,anchor+r'''

#ifdef HD_NECROMANCER_PLAYTEST
#include "hd_necro_creation.h"

static int hd_necro_random_stat(int low,int high)
{
    return mrand(low,high);
}
#endif
''',1)

    pattern=r'^[ \t]*switch\s*\(\s*Ply\[fd\]\.ply->race\s*\)\s*\{'

    matches=list(re.finditer(pattern,s,re.M))

    assert len(matches)==1, 'Unexpected racial adjustment layout'

    pos=matches[0].start()

    s=s[:pos]+'''#ifdef HD_NECROMANCER_PLAYTEST
        hd_necro_creation_stats(Ply[fd].ply,
            Ply[fd].extr->tempstr[1][0] == 'n',
            hd_necro_random_stat);
#endif
'''+s[pos:]

    p.write_text(s,encoding='latin-1')

    shutil.copyfile(
        HERE.parent/'creation/hd_necro_creation.h',
        source/'hd_necro_creation.h')

    print('PASS: Necromancer-only rolls precede race modifiers',
          flush=True)

    p=source/'hollowdeep_help.c'
    s=p.read_text(encoding='latin-1')

    pattern=r'"raise skeleton \[%s\][^"\n]*"'

    s,n=re.subn(pattern,
        lambda m: r'"raise corpse [%s] - 8 mana, 120-second cooldown\n"',
        s)

    assert n==1, 'Legacy Necromancer skill entry not found'

    pattern=r'^[ \t]*print\(player->fd, "%d skills listed\.[^\n]*$'

    matches=list(re.finditer(pattern,s,re.M))
    assert len(matches)==1

    pos=matches[0].start()

    s=s[:pos]+r'''
    if (player->type == PLAYER || all) {
        print(player->fd,
              "conjure [all classes] - one companion, 300-second cooldown\n");
        shown++;
    }
'''+s[pos:]

    anchor='    if (count == 2 && !strcmp(token[1], "conjure"))'

    assert s.count(anchor)==1

    routes='''    if (count == 3 && !strcmp(token[1], "pet") && !strcmp(token[2], "experience")) return show_page(player, "pet-experience");
    if (count == 2 && !strcmp(token[1], "pet")) return show_page(player, "help.154");
    if (count == 2 && !strcmp(token[1], "drain-mana")) return show_page(player, "drain-mana");
'''

    s=s.replace(anchor,routes+anchor,1)

    s=s.replace('Class guide: help necromancer | help raise skeleton',
                'Class guide: help necromancer | help raise corpse | help conjure')

    p.write_text(s,encoding='latin-1')
    print('PASS: Updated native skill catalog and help routes',
          flush=True)
