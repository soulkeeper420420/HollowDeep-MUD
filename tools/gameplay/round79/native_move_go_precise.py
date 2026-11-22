#!/usr/bin/env python3
"""Round 79J: PRIVATE compact native move()/go() definition report.

Output each exact C function (up to a bound), not arbitrary adjacent command
code. This fixes the previous report's 1200-line output-cap problem.
Only verified /tmp private native ELF32 source is accepted. Read-only.
"""
from pathlib import Path
import argparse
import re
import sys

PREFIX=("hd-army-game-round79store-","hd-army-game-round79move-")
TARGET=re.compile(r'^\s*int\s+(move|go)\s*\(',re.M)
INTEREST=re.compile(
    r'rom_num|first_ext|add_ply_rom|del_ply_rom|load_rom|'
    r'find_ext|find_rom|XLOCK|XSECRT|XINVIS|RMAX|parent_rom|'
    r'please_wait|return\s*\(|exit_ptr|ext_ptr|look\(|'
    r'fail|deny|PFLYSP|PBRWAT',re.I
)

def check(root):
    root=Path(root)
    if (root.name!="src" or root.is_symlink() or
        root.parent.is_symlink() or root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(PREFIX) or
        root.resolve(strict=True)!=root.absolute()):
        raise ValueError("Expected verified private Round79H/J ELF32 tree")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private ELF32 candidate missing")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private source is not ELF32")
    for file in root.glob("*.c"):
        if file.is_symlink() or not file.is_file():
            raise ValueError("Private native code symlink denied")
    return root

def end_function(lines,start):
    """Return first balanced closing brace after a K&R function header.

    Strip comments/literals while scanning so a brace within an MUD
    room string or source comment cannot truncate the function.
    """
    fragment="\n".join(lines[start:])
    pending=True
    state="code"
    depth=0
    i=0
    line=start
    while i<len(fragment):
        ch=fragment[i]
        nxt=fragment[i+1] if i+1<len(fragment) else ""
        if ch=="\n":
            line+=1
            if state=="line_comment":
                state="code"
            i+=1
            continue
        if state=="code":
            if ch=="/" and nxt=="/":
                state="line_comment"; i+=2; continue
            if ch=="/" and nxt=="*":
                state="block_comment";i+=2;continue
            if ch=='"':
                state="string";i+=1;continue
            if ch=="'":
                state="char";i+=1;continue
            # K&R function parameter declarations end in semicolons
            # after the signature; only a same-line semicolon is a
            # prototype rather than a native function definition.
            if ch==";" and pending and line==start:
                return None
            if ch=="{":
                pending=False;depth+=1
            elif ch=="}" and not pending:
                depth-=1
                if depth==0:
                    return line
        elif state=="block_comment" and ch=="*" and nxt=="/":
            state="code";i+=2;continue
        elif state in ("string","char"):
            if ch=="\\":
                i+=2;continue
            if (state=="string" and ch=='"') or (state=="char" and ch=="'"):
                state="code"
        i+=1
    return None

def extract(root):
    output=[]
    for filename in sorted(root.glob("*.c")):
        lines=filename.read_text(encoding="latin-1").splitlines()
        for i,line in enumerate(lines):
            m=TARGET.match(line)
            if not m:
                continue
            end=end_function(lines,i)
            if end is not None and end>i and end-i<950:
                output.append((m.group(1),filename.name,i,end,lines))
    for name in ("move","go"):
        matches=[x for x in output if x[0]==name]
        print("=== NATIVE %s() verified definitions: %d ==="%(name,len(matches)))
        if len(matches)!=1:
            raise ValueError("Expected exactly one real native "+name+"() body")
        _,filename,start,end,lines=matches[0]
        print("SOURCE: %s:%d-%d"%(filename,start+1,end+1))
        # Include start, actual brace/body context, destination and room
        # mutation edges, final returns. Stay under ~280 lines per function.
        selected=set(range(start,min(end+1,start+110)))
        selected.update(range(max(start,end-30),end+1))
        indices=[i for i in range(start,end+1) if INTEREST.search(lines[i])]
        for ix in indices[:85]:
            selected.update(range(max(start,ix-1),min(end+1,ix+3)))
        previous=-2
        for ix in sorted(selected)[:285]:
            if ix!=previous+1:
                print("...")
            print("%s:%04d: %s"%(filename,ix+1,lines[ix][:205]))
            previous=ix
    print("ROUND 79J: EXACT NATIVE GO/MOVE FUNCTION SOURCE PASS")
    print("NATIVE GAMEPLAY MOVEMENT HOOK: NOT YET INSTALLED")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args()
    try:
        extract(check(args.source))
    except (OSError,ValueError) as error:
        print("ROUND 79J MOVE SOURCE REFUSED:",error,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
