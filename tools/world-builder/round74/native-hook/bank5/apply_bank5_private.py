#!/usr/bin/env python3
"""Stage a five-level XP bank. Train remains one level per invocation.

Private Round 74B source only, after 65-point + XP60 + first-life patches.
Fail closed on source drift; zero writes until all anchors validated.
"""
from pathlib import Path
import hashlib
import sys

EXPECTED={
    'hd74_xp.c':'4bb6c12010de1866a29619181ffad0fa16a953b84a3392c762d4b2a3d1cb3252',
    'hd74_xp.h':'f75a90843459d054df98057187930bab41ce07c65dd1ff6b971384dc417c374d',
    'creature.c':'9a187ae377b3f83a9bac69a64f3ab4f995f1c875d99bf5d9ca35ecace81ed84f',
    'command2.c':'5de02bddeda033076ee361fa8563e437c069b42a7687d5f5f73810bfe7d66237',
    'command8.c':'340597e0b06318f73a4b107450f7aca9ddc7f32739495dfd0117f6446ca09379',
    'command10.c':'c3a0cc43bbc542db4df4503a84aedf972ad77ecf17bce1443c0f6f4940a95516',
    'command7.c':'f807c2b42b30d5a6bd839ab481e36478f2bd87ac4e09a11c9675659a6d0dda52',
}

def once(source, old, new, label):
    if source.count(old)!=1:
        raise ValueError('source mismatch for '+label+' (found '+str(source.count(old))+')')
    return source.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('Usage: apply_bank5_private.py /root/hollowdeep-dev/round74b-XXXXXXXX/src')
    raw=Path(sys.argv[1]); src=raw.resolve(strict=True)
    if (raw.is_symlink() or src.is_symlink() or src.name!='src' or
        not any(x.startswith('round74b-') for x in src.parts) or
        str(src).startswith(('/srv/','/var/www/'))):
        raise SystemExit('Refusing non-disposable source: '+str(src))
    original={}
    for name,digest in EXPECTED.items():
        f=src/name
        if not f.is_file() or f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:
            raise SystemExit('Source missing, symlinked or drifted: '+name)
        original[name]=f.read_text(encoding='latin-1')
    out=dict(original)
    f='hd74_xp.h'
    out[f]=once(out[f], '#endif\n',
                  '''/* Keep up to five NEXT levels of total XP banked. Each `train` command
 * still grants exactly ONE level and charges that level's gold fee.
 * Unknown life data uses the full-cost XP curve (never a free discount).
 */
#define HD74_BANKED_LEVELS 5
long hd74_xp_bank_limit(int current_level, int verified_remorts);
long hd74_xp_add_banked(long current, long delta, int current_level,
                        int verified_remorts);
int hd74_bankable_levels(int current_level, long xp, int verified_remorts);
#endif
''',f)
    f='hd74_xp.c'
    out[f]+='''
/* The first five *future* level thresholds may be earned before training.
 * XP is cumulative: training never subtracts XP. A legacy character whose
 * saved experience is already above the cap is not silently reduced. */
long hd74_xp_bank_limit(int current_level, int verified_remorts)
{
    int highest;
    if (current_level < 1 || current_level > HD74_LEVEL_CAP ||
        verified_remorts < -1) return -1;
    highest=current_level+HD74_BANKED_LEVELS;
    if (highest>HD74_LEVEL_CAP) highest=HD74_LEVEL_CAP;
    return hd74_xp_for_life_next(highest-1,verified_remorts);
}
long hd74_xp_add_banked(long current, long delta, int current_level,
                        int verified_remorts)
{
    long limit, updated;
    if (current < 0) current=0;
    if (current>HD74_XP_MAX) current=HD74_XP_MAX;
    if (delta<=0) return current;
    if (current_level==HD74_LEVEL_CAP) return current;
    limit=hd74_xp_bank_limit(current_level,verified_remorts);
    if (limit<0 || current>=limit) return current;
    updated=hd74_xp_add_bounded(current,delta);
    return updated>limit ? limit : updated;
}
int hd74_bankable_levels(int current_level, long xp, int verified_remorts)
{
    int gained=0, next;
    if (current_level<1 || current_level>HD74_LEVEL_CAP ||
        verified_remorts < -1) return -1;
    for(next=current_level+1;
        next<=HD74_LEVEL_CAP && gained<HD74_BANKED_LEVELS; ++next) {
        long threshold=hd74_xp_for_life_next(next-1,verified_remorts);
        if(threshold<0 || xp<threshold) break;
        ++gained;
    }
    return gained;
}
'''
    sites=[
        ('creature.c','ply_ptr','hd74_xp_add_bounded(ply_ptr->experience,expdiv)',1),
        ('creature.c','att_ptr','hd74_xp_add_bounded(att_ptr->experience,xpv)',1),
        ('command2.c','ply_ptr','hd74_xp_add_bounded(ply_ptr->experience,quest_exp[obj_ptr->questnum-1])',2),
        ('command8.c','ply_ptr','hd74_xp_add_bounded(ply_ptr->experience,quest_exp[obj_ptr->questnum-1])',1),
        ('command10.c','ply_ptr','hd74_xp_add_bounded(ply_ptr->experience,amte)',1),
        ('command10.c','ply_ptr','hd74_xp_add_bounded(ply_ptr->experience,quest_exp[trd_ptr->questnum-1])',1),
    ]
    for file,actor,old,expected_count in sites:
        new=old.replace('hd74_xp_add_bounded(', 'hd74_xp_add_banked(')[:-1]+(
          ',(int)%s->level,hd74_verified_remorts(%s->name))'%(actor,actor))
        if out[file].count(old)!=expected_count:
            raise ValueError('unsafe XP grant anchors in '+file)
        out[file]=out[file].replace(old,new)
    # Train is not patched. A private build contains exactly one up_level call,
    # and the test runs five separate calls against actual native train().
    if out['command7.c'].count('up_level(ply_ptr);')!=1:
        raise SystemExit('Actual train is not one-level-per-command')
    # Check all intended edits before modifying anything.
    for name in EXPECTED:
        if name!='command7.c' and out[name]==original[name]:
            raise SystemExit('No change in '+name)
    for name in out:
        if name=='command7.c':continue
        (src/name).write_text(out[name],encoding='latin-1')
    print('ROUND 74B: XP bank capped at five future level thresholds (private)')
    print('ROUND 74B: actual train remains one level per command')
    print('REMORT SAVE BRIDGE: PENDING; PRODUCTION DEPLOYMENT: NONE')

if __name__=='__main__': main()
