#!/usr/bin/env python3
"""Round79P: stage explicit native REST+15 in isolated accepted ELF32 source.

Source: accepted Round79K travel build from /tmp.
Target: new unused /tmp/hd-army-game-round79rest-*/src.
Never edit the known-good prior source or live production.

Exactly verified process_cmd() and native social command table, with
cleanup inserted in the one free_crt() and die() function definition.
No creature/player binary structure, save-format or room edits.
"""
from pathlib import Path
import argparse
import os
import re
import shutil
import sys

from native_move_go_precise import end_function

HERE=Path(__file__).resolve().parent
IN_PREFIX="hd-army-game-round79travel-"
OUT_PREFIX="hd-army-game-round79rest-"
NEW=("hd79_rest_session.h","hd79_rest_session.c",
     "hd79_rest_game.h","hd79_rest_game.c")
REQUIRED=("frp.new","Makefile","command1.c","global.c",
          "player.c","creature.c","hd79_breath_travel_runtime.c",
          "hd79_breath_travel_runtime.h",
          "hd_breath_store.inc","hd_breath_move_checkpoint.inc")

def private(src,prefix,existing):
    src=Path(src)
    if (src.name!="src" or src.parent.parent!=Path("/tmp") or
        not src.parent.name.startswith(prefix) or
        src.is_symlink() or src.parent.is_symlink()):
        raise ValueError("Only disposable /tmp/"+prefix+"*/src accepted")
    if not existing:
        if src.exists() or not src.parent.is_dir() or src.parent.is_symlink():
            raise ValueError("Destination must be unused private source")
        return src
    if not src.is_dir() or src.resolve(strict=True)!=src.absolute():
        raise ValueError("Private native tree is unsafe")
    for name in REQUIRED:
        p=src/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Missing isolated native prerequisite: "+name)
    with (src/"frp.new").open("rb") as stream:
        if stream.read(5)!=b"\x7fELF\x01":
            raise ValueError("Original candidate is not ELF32")
    for root,dirs,files in os.walk(src,followlinks=False):
        if any((Path(root)/name).is_symlink() for name in dirs+files):
            raise ValueError("Symlinks denied in native tree")
    if any((src/name).exists() for name in NEW):
        raise ValueError("Rest source already staged in source directory")
    return src

def replace_once(body,old,new,label):
    if body.count(old)!=1:
        raise ValueError("Exact native source anchor drift: "+label)
    return body.replace(old,new,1)

def native_cleanup_definition(src,symbol):
    pattern=re.compile(r'(?m)^[ \t]*(?:void[ \t]+|int[ \t]+)?'+
                       re.escape(symbol)+
                       r'[ \t]*\([ \t]*([A-Za-z_]\w*)[ \t]*'
                       r'(?:,[ \t]*[A-Za-z_]\w*[ \t]*)*\)[ \t]*$')
    definitions=[]
    for path in sorted(src.glob("*.c")):
        lines=path.read_text(encoding="latin-1").splitlines(keepends=True)
        plain=[line.rstrip("\r\n") for line in lines]
        for index,line in enumerate(plain):
            found=pattern.match(line)
            if not found:
                continue
            end=end_function(plain,index)
            if end is None or end<=index:
                continue
            # Reject prototypes and recognize actual K&R declarations.
            opening=next((i for i in range(index+1,min(end+1,index+40))
                          if plain[i].strip()=="{"),None)
            if opening is None:
                continue
            definitions.append((path,opening,found.group(1)))
    if len(definitions)!=1:
        raise ValueError("Exact native "+symbol+"() lifecycle definition count "+
                         str(len(definitions))+"; refusing to guess")
    return definitions[0]

def inject_after_brace(body,opening,param,symbol):
    lines=body.splitlines(keepends=True)
    if opening>=len(lines) or lines[opening].strip()!="{":
        raise ValueError("Native "+symbol+"() opening brace changed")
    hook=(
        "#ifdef HD79_REST_PLAYTEST\n"
        "  { extern void hd79_rest_forget(); hd79_rest_forget("+param+"); }\n"
        "#endif\n"
    )
    lines.insert(opening+1,hook)
    return "".join(lines)

def patch(src):
    edited={}
    make=(src/"Makefile").read_text(encoding="latin-1")
    feature=("ifeq ($(BREATH_TRAVEL_PLAYTEST),1)\n"
             "CFLAGS += -DHD79_BREATH_TRAVEL_PLAYTEST\n"
             "OBJECTS += hd79_breath_travel_runtime.o\n"
             "endif\n")
    flags=("ifeq ($(REST_BREATH_PLAYTEST),1)\n"
           "ifneq ($(BREATH_TRAVEL_PLAYTEST),1)\n"
           "$(error REST_BREATH_PLAYTEST requires BREATH_TRAVEL_PLAYTEST)\n"
           "endif\n"
           "CFLAGS += -DHD79_REST_PLAYTEST\n"
           "OBJECTS += hd79_rest_session.o hd79_rest_game.o\n"
           "endif\n")
    edited["Makefile"]=replace_once(make,feature,feature+flags,
                                  "feature-gated ELF32 Makefile")

    command=(src/"command1.c").read_text(encoding="latin-1")
    native_end="return((*cmdlist[cmdno].cmdfn)(Ply[fd].ply, cmnd));"
    prep=(
        "#ifdef HD79_REST_PLAYTEST\n"
        "        /* Rest is cleared only after alias and authorization checks,\n"
        "         * but before special or ordinary native command execution.\n"
        "         */\n"
        "        hd79_rest_before_command(Ply[fd].ply,cmdlist[cmdno].cmdstr);\n"
        "#endif\n"
    )
    special="        if(cmdlist[cmdno].cmdno < 0)"
    command=replace_once(command,special,prep+special,
                         "process_cmd before special dispatch")
    command=replace_once(
        command,native_end,native_end,
        "one real process_cmd native callback")
    decl="int process_cmd(fd, cmnd)"
    command=replace_once(
        command,decl,
        "#ifdef HD79_REST_PLAYTEST\n"
        "extern void hd79_rest_before_command(creature *,const char *);\n"
        "#endif\n"+decl,
        "one native process_cmd definition")
    edited["command1.c"]=command

    global_c=(src/"global.c").read_text(encoding="latin-1")
    sleep='  { "sleep", 100, action },'
    addition=(
        "#ifdef HD79_REST_PLAYTEST\n"
        '  { "rest", 100, hd79_rest_command },\n'
        "#endif\n"
    )
    global_c=replace_once(global_c,sleep,addition+sleep,
                          "dedicated rest command beside old sleep emote")
    global_c=(
        "#ifdef HD79_REST_PLAYTEST\n"
        "extern int hd79_rest_command();\n"
        "#endif\n"+global_c
    )
    edited["global.c"]=global_c

    runtime=(src/"hd79_breath_travel_runtime.c").read_text(
        encoding="latin-1")
    hdr='#include "hd79_breath_travel_runtime.h"'
    runtime=replace_once(runtime,hdr,
        hdr+'\n#ifdef HD79_REST_PLAYTEST\n'
        '#include "hd79_rest_game.h"\n#endif',
        "native rest runtime header")
    original="    int rc;\n    if (!player || player->type!=PLAYER ||"
    changed=(
        "    int rc;\n"
        "#ifdef HD79_REST_PLAYTEST\n"
        "    int resting=0;\n"
        "#endif\n"
        "    if (!player || player->type!=PLAYER ||"
    )
    runtime=replace_once(runtime,original,changed,
                         "native Breath recovery function declarations")
    old_step=(
        "    rc=hd_breath_store_step(player->name,&before,HD_BREATH_OP_RECOVER,\n"
        "                            0,0,now,&after);"
    )
    new_step=(
        "#ifdef HD79_REST_PLAYTEST\n"
        "    resting=hd79_rest_bonus_eligible(player,now,before.last_recover);\n"
        "#endif\n"
        "    rc=hd_breath_store_step(player->name,&before,HD_BREATH_OP_RECOVER,\n"
        "#ifdef HD79_REST_PLAYTEST\n"
        "                            0,resting,now,&after);\n"
        "#else\n"
        "                            0,0,now,&after);\n"
        "#endif"
    )
    runtime=replace_once(runtime,old_step,new_step,
                         "existing atomic +5 Breath recovery")
    edited["hd79_breath_travel_runtime.c"]=runtime

    # Both cleanup functions may live in the same native C unit.
    # Insert from last line toward first so original K&R line
    # positions remain exact and no source offset needs guessing.
    cleanup={}
    for symbol in ("free_crt","die"):
        path,opening,param=native_cleanup_definition(src,symbol)
        cleanup.setdefault(path.name,[]).append((opening,param,symbol))
    for name,hooks in cleanup.items():
        body=(src/name).read_text(encoding="latin-1")
        for opening,param,symbol in sorted(hooks,reverse=True):
            body=inject_after_brace(body,opening,param,symbol)
        edited[name]=body

    return edited

def stage(source,target):
    source=private(source,IN_PREFIX,True)
    target=private(target,OUT_PREFIX,False)
    edits=patch(source)
    fingerprints={name:(source/name).read_bytes() for name in edits}
    shutil.copytree(source,target,symlinks=False)
    try:
        for name,text in edits.items():
            (target/name).write_text(text,encoding="latin-1")
        for name in NEW:
            shutil.copyfile(HERE/name,target/name)
        for name,original in fingerprints.items():
            if (source/name).read_bytes()!=original:
                raise ValueError("Accepted native source changed while staging")
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("accepted_round79k_source",type=Path)
    p.add_argument("new_private_round79p_source",type=Path)
    args=p.parse_args()
    try:
        output=stage(args.accepted_round79k_source,
                     args.new_private_round79p_source)
    except (OSError,ValueError) as error:
        print("ROUND79P: PRIVATE SOURCE STAGING REFUSED:",error,
              file=sys.stderr)
        return 1
    print("ROUND79P: NATIVE EXPLICIT REST +15 HOOKS STAGED:",output)
    print("BUILD AND SOCKET TESTS: REQUIRED BEFORE PLAYABLE")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
