#!/usr/bin/env python3
"""Apply FIRST-LIFE training costs to the exact, already-patched Round74B private native source.

No production, no restarts. Without a trusted persisted remort lookup, unknown
life status receives STANDARD prices. HD74_LIFE_TEST_BRIDGE is permitted only
for disposable tests and is not a source of in-game authority.
"""
from pathlib import Path
import hashlib
import sys

EXPECTED = {
    'command7.c':'147f82eb7e91ab4d86e2891eaa6af2879d717cf67aa19130cee258adf4f6d171',
    'command4.c':'53d37609e9013138c183ccc5150348371c456b861af64b5c25654a2147b41b22',
    'hollowdeep.c':'57518a1c2f1e22cd544a7fa88654e9dfdb5eaa825758d20b60b3e9ded8f757d8',
    'hd74_native.c':'cfe7661796bdf5cc69bca0c712a9b4969f727b2a1754b7fa5b275fcc4a615f41',
    'hd74_xp.c':'07c97ebfdc10dd0c7a9ee072a571aee6ea1bbc7ce322baeab74dbbc1cb2ac379',
    'hd74_xp.h':'08cf3de4067c3b171e3a525f4822fd4c54a32f63080852cb8309f01f129e4001',
}

def once(source, old, new, file_name):
    if source.count(old) != 1:
        raise ValueError('Unsafe or missing source anchor: '+file_name+' '+repr(old[:55]))
    return source.replace(old,new,1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: apply_first_life_private.py /root/hollowdeep-dev/round74b-XXXXXXXX/src')
    raw=Path(sys.argv[1]); src=raw.resolve(strict=True)
    if (src.is_symlink() or raw.is_symlink() or src.name != 'src' or
        not any(part.startswith('round74b-') for part in src.parts) or
        str(src).startswith(('/srv/','/var/www/'))):
        raise SystemExit('Refusing non-disposable source: '+str(src))
    original={}
    for name,expected in EXPECTED.items():
        p=src/name
        if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise SystemExit('Source missing/symlinked/drifted: '+name)
        original[name]=p.read_text(encoding='latin-1')
    out=dict(original)
    f='hd74_xp.h';s=out[f]
    old='#endif\n'
    new='''/* Life status MUST come from an atomic, trusted character save record.
 * -1 means "not verified"; unknown receives normal prices (never free).
 * Zero remorts: first life. One or more: regular reborn lives.
 */
int hd74_verified_remorts(const char *native_player_name);
long hd74_xp_for_life_next(int current_level, int verified_remorts);
long hd74_gold_for_life_next(int current_level, int verified_remorts);
int hd74_training_cost_for_remorts(int current_level, int verified_remorts,
                                  long *xp_required, long *gold_required);
int hd74_level_from_xp_for_life(long xp, int verified_remorts);
#endif
'''
    out[f]=once(s,old,new,f)

    f='hd74_xp.c';s=out[f]
    extension='''
/* This function is deliberately unhooked until a native, atomic progression
 * save/read supplies verified life data. Do not infer remorts from level or
 * a player-supplied command argument. Only disposable tests define the bridge. */
int hd74_verified_remorts(const char *native_player_name)
{
    if (!native_player_name || !native_player_name[0]) return -1;
#ifdef HD74_LIFE_TEST_BRIDGE
    { extern int hd74_test_verified_remorts(const char *native_player_name);
      return hd74_test_verified_remorts(native_player_name); }
#else
    return -1; /* Unknown: never apply discount from unverified data. */
#endif
}

long hd74_xp_for_life_next(int current_level, int verified_remorts)
{
    long full=hd74_xp_for_next(current_level);
    if (full<0 || verified_remorts < -1) return -1;
    return verified_remorts==0 ? full/2L : full;
}
long hd74_gold_for_life_next(int current_level, int verified_remorts)
{
    long full=hd74_xp_for_next(current_level);
    if (full<0 || verified_remorts < -1) return -1;
    /* Gold was already HALF the standard cumulative XP threshold.
       First life pays HALF of that normal gold fee (floor for odd gold). */
    return verified_remorts==0 ? (full/2L)/2L : full/2L;
}
int hd74_training_cost_for_remorts(int current_level, int verified_remorts,
                                  long *xp_required, long *gold_required)
{
    long xp, gold;
    if (!xp_required || !gold_required) return -1;
    xp=hd74_xp_for_life_next(current_level,verified_remorts);
    gold=hd74_gold_for_life_next(current_level,verified_remorts);
    if (xp<0 || gold<0) return -1;
    *xp_required=xp; *gold_required=gold;
    return 0;
}
int hd74_level_from_xp_for_life(long xp, int verified_remorts)
{
    int level;
    if (verified_remorts < -1) return -1;
    if (xp<=0L) return 1;
    if (xp>HD74_XP_MAX) xp=HD74_XP_MAX;
    for (level=2;level<=HD74_LEVEL_CAP;++level) {
        long threshold=hd74_xp_for_life_next(level-1,verified_remorts);
        if (threshold<0 || xp<threshold) break;
    }
    return level-1;
}
'''
    out[f]=s+extension

    f='command7.c';s=out[f]
    old='''\texpneeded = hd74_xp_for_next((int)ply_ptr->level);
\tif (expneeded < 0) {'''
    new='''\tif (hd74_training_cost_for_remorts((int)ply_ptr->level,
\t        hd74_verified_remorts(ply_ptr->name),
\t        &expneeded,&goldneeded) != 0) {'''
    s=once(s,old,new,f)
    old='''\tgoldneeded = expneeded / 2L;

\tif(expneeded > ply_ptr->experience) {'''
    new='''#ifndef HD74_PRIVATE_NATIVE
\tgoldneeded = expneeded / 2L;
#endif

\tif(expneeded > ply_ptr->experience) {'''
    out[f]=once(s,old,new,f)

    f='command4.c';s=out[f]
    old='\texpneeded = hd74_xp_for_next((int)ply_ptr->level);'
    new='\texpneeded = hd74_xp_for_life_next((int)ply_ptr->level,\n\t                                     hd74_verified_remorts(ply_ptr->name));'
    out[f]=once(s,old,new,f)

    f='hollowdeep.c';s=out[f]
    old='    required = hd74_xp_for_next((int)level);'
    new='    required = hd74_xp_for_life_next((int)level, hd74_verified_remorts(player->name));'
    s=once(s,old,new,f)
    old='    price = required / 2L;'
    new='''#ifdef HD74_PRIVATE_NATIVE
    price = hd74_gold_for_life_next((int)level, hd74_verified_remorts(player->name));
#else
    price = required / 2L;
#endif'''
    out[f]=once(s,old,new,f)

    f='hd74_native.c';s=out[f]
    old='''        remaining=(player->experience<(long)next)?(long)next-player->experience:0;'''
    new='''#ifdef HD74_PRIVATE_NATIVE
        { long adjusted=hd74_xp_for_life_next((int)level,
                                      hd74_verified_remorts(player->name));
          if (adjusted>=0) next=(uint32_t)adjusted; }
#endif
        remaining=(player->experience<(long)next)?(long)next-player->experience:0;'''
    s=once(s,old,new,f)
    old='''    print(player->fd,"Proposed creation: up to 65 total stat points, 3..18 per stat.\\n");'''
    new='''#ifdef HD74_PRIVATE_NATIVE
    { int remorts=hd74_verified_remorts(player->name);
      if (remorts==0) print(player->fd,"First life: 50%% XP threshold and 50%% regular training gold fee.\\n");
      else if (remorts>0) print(player->fd,"Reborn life: standard XP and training gold.\\n");
      else print(player->fd,"Life status not yet verified in player save: standard training prices.\\n"); }
#endif
    print(player->fd,"Proposed creation: up to 65 total stat points, 3..18 per stat.\\n");'''
    out[f]=once(s,old,new,f)

    # No writes on any unsafe anchors / failed checks.
    if any(out[k]==v for k,v in original.items()):
        raise SystemExit('No changes detected for one or more target files')
    for name,text in out.items(): (src/name).write_text(text,encoding='latin-1')
    print('ROUND 74B: first-life 50%% XP/50%% gold private training policy staged')
    print('ROUND 74B: unknown remort status defaults to standard costs (safe)')
    print('LIVE PLAYER-SAVE LIFE LOOKUP: NOT INTEGRATED; PRODUCTION: UNCHANGED')

if __name__=='__main__': main()
