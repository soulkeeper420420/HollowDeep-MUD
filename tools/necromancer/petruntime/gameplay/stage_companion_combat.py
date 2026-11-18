"""Enable companion assistance on ordinary native combat rounds."""
import re

def stage(source):
    p=source/'command5.c'
    s=p.read_text(encoding='latin-1')

    old=r'''#ifdef HD_NECROMANCER_PLAYTEST
    /* Never use a freed target after the native killing blow. */
    if (!attack_crt(ply_ptr, crt_ptr))
        hd_necro_skeleton_assist(ply_ptr, crt_ptr);
#else
    attack_crt(ply_ptr, crt_ptr);
#endif'''

    assert s.count(old)==1
    s=s.replace(old,"    attack_crt(ply_ptr, crt_ptr);",1)

    anchor='#include "hd_necro_skeleton.h"'
    assert s.count(anchor)==1

    s=s.replace(anchor,anchor+
        '\nextern int hd_army_assist_result(creature *, creature *);',1)

    a=s.index('int attack_crt(ply_ptr, crt_ptr)')
    b=s.index('\n}\n',a)
    body=s[a:b]

    body,n=re.subn(
        r'else\s*\n\s*check_for_flee\(crt_ptr\);',
        '''else {
            if (ply_ptr->type == PLAYER &&
                hd_army_assist_result(ply_ptr,crt_ptr))
                return(1);
            check_for_flee(crt_ptr);
        }''',body,count=1)

    assert n==1

    anchor='    }\n\n    return(0);'
    assert body.endswith(anchor)

    body=body[:-len(anchor)]+'''        if (ply_ptr->type == PLAYER &&
            hd_army_assist_result(ply_ptr,crt_ptr))
            return(1);
    }

    return(0);'''

    p.write_text(s[:a]+body+s[b:],encoding='latin-1')
