#!/usr/bin/env python3
"""Round79K: stage real Breath gameplay integration in disposable ELF32 source.

The private patch:
  * changes the native movement handlers only AFTER permission, room-level,
    occupancy and other exit validation, BEFORE room mutation/broadcasts;
  * classifies wilderness by exact validated wilderness.map tile membership;
  * checkpoints new player room and Breath together before moving live state;
  * reads actual durable Breath for the existing colored/plain HUD;
  * recovers 5 Breath only after a verified >=45s elapsed native update
    (rest-specific 15-rate is intentionally pending the native rest audit).
Nothing modifies production world, code, player files or services.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
FROM="hd-army-game-round79move-"
TO="hd-army-game-round79travel-"
NEW=("hd79_breath_travel_runtime.c","hd79_breath_travel_runtime.h")
REQUIRED=("frp.new","Makefile","wilderness.c","command2.c","command6.c",
          "player.c","hd_breath_store.inc","hd_breath_move_checkpoint.inc",
          "hd_status_hud.c")

def validate(source,prefix,exists):
    source=Path(source)
    if (source.name!="src" or source.parent.parent!=Path("/tmp") or
        not source.parent.name.startswith(prefix) or
        source.is_symlink() or source.parent.is_symlink()):
        raise ValueError("Only disposable /tmp/"+prefix+"*/src accepted")
    if not exists:
        if source.exists() or not source.parent.is_dir():
            raise ValueError("Destination must be an unused private /tmp path")
        return source
    if not source.is_dir() or source.resolve(strict=True)!=source.absolute():
        raise ValueError("Native source is not a real private directory")
    for name in REQUIRED:
        p=source/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Missing private native baseline: "+name)
    with (source/"frp.new").open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private engine must be ELF32")
    for root,dirs,files in os.walk(source,followlinks=False):
        for name in dirs+files:
            if (Path(root)/name).is_symlink():
                raise ValueError("Symlinks denied in native private tree")
    if any((source/name).exists() for name in NEW):
        raise ValueError("Breath travel already staged in this source")
    return source

def insert_once(body,anchor,updated,label):
    if body.count(anchor)!=1:
        raise ValueError("Exact native source anchor drift: "+label)
    return body.replace(anchor,updated,1)

TILE=r'''#ifdef HD79_BREATH_TRAVEL_PLAYTEST
/* Read and validate an actual native wilderness.map tile. This must
 * remain independent of showmap on/off and old room-ID-only heuristics.
 * Invalid/missing wilderness data denies travel into reserved room IDs.
 */
int hd79_wilderness_tile(int id)
{
    FILE *file;
    struct tile tile;
    char version[24];
    int rows=0,found=0,result;
    if (id<10000) return 0;
    if (id>=RMAX) return -1;
    file=fopen(ROOMPATH "/wilderness.map","r");
    if (!file) return -1;
    if (!fgets(version,sizeof version,file) ||
        strcmp(version,"HDW1\n")) {
        fclose(file);
        return -1;
    }
    while ((result=read_tile(file,&tile))>0) {
        if (++rows>6000) { fclose(file); return -1; }
        if (tile.id==id) {
            if (found) { fclose(file); return -1; }
            found=1;
        }
    }
    if (result<0 || ferror(file)) {
        fclose(file);
        return -1;
    }
    fclose(file);
    return found ? 1:-1;
}
#endif /* HD79_BREATH_TRAVEL_PLAYTEST */

'''

RUNTIME_DECL=r'''#ifdef HD79_BREATH_TRAVEL_PLAYTEST
extern int hd79_breath_precommit(creature *,room *);
#endif
'''

MOVEMENT_GUARD=r'''#ifdef HD79_BREATH_TRAVEL_PLAYTEST
        /* Source exit and destination restrictions have all passed.
         * Save BOTH destination room and Breath before live mutation,
         * follower transfer or trap side effects.
         */
        if (hd79_breath_precommit(ply_ptr,rom_ptr)<0)
            return(0);
#endif
'''

def patch(source):
    files={name:(source/name).read_text(encoding="latin-1")
           for name in ("Makefile","wilderness.c","command2.c",
                        "command6.c","player.c")}
    make=files["Makefile"]
    feature=("ifeq ($(BREATH_MOVE_CHECKPOINT_TEST),1)\n"
             "CFLAGS += -DHD79_BREATH_MOVE_CHECKPOINT_TEST\n"
             "endif\n")
    files["Makefile"]=insert_once(
        make,feature,feature+
        "ifeq ($(BREATH_TRAVEL_PLAYTEST),1)\n"
        "CFLAGS += -DHD79_BREATH_TRAVEL_PLAYTEST\n"
        "OBJECTS += hd79_breath_travel_runtime.o\n"
        "endif\n",
        "native feature-gated Makefile")

    wilderness=files["wilderness.c"]
    anchor="static int visible(creature *player, int id)"
    files["wilderness.c"]=insert_once(
        wilderness,anchor,TILE+anchor,
        "exact native tile parser and map-position helper")

    # Both native entry points execute permission/level/room-full checks
    # first. This insertion is before broadcasts or add/del_crt_rom.
    markers={
        "command2.c":'if(ply_ptr->class == DM && !F_ISSET(ply_ptr, PDMINV)){',
        "command6.c":'if(strcmp(ext_ptr->name, "up")',
    }
    for name,anchor in markers.items():
        body=files[name]
        if body.count(anchor)!=1:
            raise ValueError("Native move/go post-validation anchor drift: "+name)
        start=body.index(anchor)
        # Match whitespace on that same native line; insert before it.
        line_begin=body.rfind("\n",0,start)+1
        old_line=body[line_begin:body.find("\n",start)]
        if not old_line.lstrip().startswith(anchor):
            raise ValueError("Native move/go anchor not at line start: "+name)
        body=body[:line_begin]+MOVEMENT_GUARD+body[line_begin:]
        # K&R native functions can declare prototypes at source scope,
        # but a prototype in this function is also valid GNU89.
        sign='int move(ply_ptr, cmnd)' if name=="command2.c" else 'int go(ply_ptr, cmnd)'
        body=insert_once(body,sign,RUNTIME_DECL+sign,
                         "native "+name+" movement signature")
        files[name]=body

    player=files["player.c"]
    hudheader='#include "hd_status_hud.h"'
    player=insert_once(player,hudheader,hudheader+
        '\n#ifdef HD79_BREATH_TRAVEL_PLAYTEST\n'
        '#include "hd79_breath_travel_runtime.h"\n'
        '#endif',"native HUD include")
    breath_anchor='    values.breath_available = 0;'
    player=insert_once(player,breath_anchor,breath_anchor+
        '''
#ifdef HD79_BREATH_TRAVEL_PLAYTEST
    {
        int stamina=0;
        if (!hd79_breath_status(ply_ptr,&stamina)) {
            values.breath_available=1;
            values.breath_current=stamina;
            values.breath_max=HD_BREATH_MAX;
        }
    }
#endif''',"true persisted Breath HUD")
    # update_ply has a verified native t=time(0) source anchor.
    tick='  t = time(0);\n  ply_ptr->lasttime[LT_HOURS].interval +='
    player=insert_once(player,tick,
        '  t = time(0);\n'
        '#ifdef HD79_BREATH_TRAVEL_PLAYTEST\n'
        '  /* Single native player-update callback; durable 45-second gate. */\n'
        '  hd79_breath_pulse(ply_ptr,t);\n'
        '#endif\n'
        '  ply_ptr->lasttime[LT_HOURS].interval +=',
        "verified update_ply native tick")
    files["player.c"]=player

    # No source mutation outside the targeted file list.
    for name,body in files.items():
        if "HD79_BREATH_TRAVEL_PLAYTEST" not in body:
            raise ValueError("Missing new native feature gate: "+name)
    return files

def stage(source,target):
    source=validate(source,FROM,True)
    target=validate(target,TO,False)
    patches=patch(source)
    original={name:(source/name).read_bytes() for name in patches}
    shutil.copytree(source,target,symlinks=False)
    try:
        for name,body in patches.items():
            (target/name).write_text(body,encoding="latin-1")
        for name in NEW:
            shutil.copyfile(HERE/name,target/name)
        if any((source/name).read_bytes()!=old
               for name,old in original.items()):
            raise ValueError("Private native source changed during staging")
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("target",type=Path)
    options=parser.parse_args()
    try:
        dest=stage(options.source,options.target)
    except (ValueError,OSError) as err:
        print("ROUND 79K: PRIVATE TRAVEL REFUSED:",err,file=sys.stderr)
        return 1
    print("ROUND 79K: NATIVE PRIVATE TRAVEL HOOKS STAGED:",dest)
    print("STATUS: PRIVATE BUILD AND SOCKET REGRESSIONS STILL REQUIRED")
    print("RESTING +15 AND MOUNTS: NOT YET WIRED")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
