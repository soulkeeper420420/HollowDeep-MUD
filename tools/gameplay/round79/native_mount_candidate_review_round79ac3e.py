#!/usr/bin/env python3
"""Round79AC3E: READ-ONLY native candidate attribute review; never whitelist."""
import argparse
import os
from pathlib import Path
import re
import stat
import struct
import sys
import native_template_inventory_round79ac3d as inventory

FIELDS=("size","mpmax","mpcur","ndice","sdice","pdice",
        "flags","flags_len","spells","spells_len","carry","carry_len")
SIGNATURE=re.compile(r"HD79_AC3E(?: \d+){12}")
# These are defensive byte-array ceilings, not presumed native field sizes.
# Exact array lengths come from sizeof() in the private compiled ELF32 probe.
MAX_TRAIT_BYTES=256
EXCLUDES=("sea horse","statue","cultist","puppet","guardian","ghost",
          "phantom","hatchling","faerie","carp","fenris","adamantine",
          "platinum","baby")

def decode_traits(source):
    if not SIGNATURE.fullmatch(source.strip()):
        raise ValueError("Unverified native ELF32 trait metadata")
    fields=dict(zip(FIELDS,map(int,source.strip().split()[1:])))
    if fields["size"]!=inventory.RECORD:
        raise ValueError("Native creature trait record size mismatch")
    for field in ("flags","spells","carry"):
        count=fields[field+"_len"]
        if count<1 or count>MAX_TRAIT_BYTES or (field=="carry" and count%2):
            raise ValueError("Unsupported native trait array size: "+field+
                             "="+str(count))
    # Never assume a specific number of spell/flag/carry bytes. Verify
    # the *compiled* sizeof() values are bounded, disjoint, and within
    # the actual native creature record before reading raw template data.
    shapes=(("mpmax",2),("mpcur",2),("ndice",2),("sdice",2),
            ("pdice",2)) + tuple((field,fields[field+"_len"])
                                for field in ("flags","spells","carry"))
    ranges=[]
    for name,size in shapes:
        offset=fields[name]
        if offset<80 or offset+size>fields["size"]:
            raise ValueError("Native trait offset out of bounds: "+name)
        for earlier,size2 in ranges:
            if offset<earlier+size2 and earlier<offset+size:
                raise ValueError("Overlapping native fields")
        ranges.append((offset,size))
    return fields

def native_record(directory,index,limit):
    if (not isinstance(index,int) or not isinstance(limit,int) or
        not (0<=index<limit) or limit<100 or limit>3000 or limit%100):
        raise ValueError("Template index outside compiled CMAX")
    directory=inventory.verified_dir(directory)
    source=directory/("m%02d"%(index//inventory.GROUP))
    descriptor=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        info=os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or
            info.st_size>inventory.RECORD*inventory.GROUP or
            info.st_size%inventory.RECORD):
            raise ValueError("Native monster file size changed")
        record=os.pread(descriptor,inventory.RECORD,
                        (index%inventory.GROUP)*inventory.RECORD)
        if len(record)!=inventory.RECORD:
            raise ValueError("Native monster record missing")
        return record
    finally:
        os.close(descriptor)

def review_entry(candidate,record,abi,fields):
    index,species,name,level,hpcur,hpmax=candidate
    if (len(record)!=inventory.RECORD or
        record[:80].split(b"\x00",1)[0]!=name.encode("ascii") or
        record[abi[0]]!=1 or record[abi[1]]!=level or
        struct.unpack_from("<h",record,abi[2])[0]!=hpmax or
        struct.unpack_from("<h",record,abi[3])[0]!=hpcur):
        raise ValueError("Candidate changed between native scans")
    mpmax=struct.unpack_from("<h",record,fields["mpmax"])[0]
    mpcur=struct.unpack_from("<h",record,fields["mpcur"])[0]
    if not 0<=mpcur<=mpmax:
        raise ValueError("Invalid native mana resource")
    dice=[struct.unpack_from("<h",record,fields[x])[0]
          for x in ("ndice","sdice","pdice")]
    counts={tag:sum(1 for v in record[fields[tag]:fields[tag]+fields[tag+"_len"]]
                   if v) for tag in ("flags","spells","carry")}
    excluded=next((phrase for phrase in EXCLUDES if phrase in name.lower()),None)
    status=("EXCLUDE_NAME" if excluded else
            "MANUAL_MAGIC_REVIEW" if counts["spells"] else "MANUAL_REVIEW")
    return (index,species,name,level,hpcur,hpmax,mpcur,mpmax,
            *dice,counts["flags"],counts["spells"],counts["carry"],status,
            excluded or "None")

def report(rows):
    lines=["=== ROUND79AC3E: PRIVATE NATIVE MOUNT TEMPLATE RISK AUDIT ===",
           "Native candidates assessed: "+str(len(rows)),
           "Excluded by conservative name screen: "+
             str(sum(x[-2]=="EXCLUDE_NAME" for x in rows))]
    for x in rows[:120]:
        lines.append("RISK id=%d type=%s name=%r lvl=%d hp=%d/%d mp=%d/%d "
          "dice=%d/%d/%d flags=%d spells=%d carry=%d status=%s reason=%s"%x)
    lines.extend(("PASS: READ-ONLY native trait review complete",
        "NO TEMPLATE APPROVED OR TRUSTED CATALOG CONFIGURED",
        "NO PLAYER MOUNT SPAWN/BOARD/STABLE/RETRIEVE/RESTORE/TRAVEL",
        "PRODUCTION DEPLOYMENT: NONE"))
    return "\n".join(lines)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-root",required=True,type=Path)
    parser.add_argument("--abi",required=True,type=Path)
    parser.add_argument("--traits",required=True,type=Path)
    args=parser.parse_args()
    try:
        abi=inventory.parse_abi(args.abi.read_text(encoding="ascii"))
        fields=decode_traits(args.traits.read_text(encoding="ascii"))
        directory=inventory.discover(args.world_root)
        _,_,candidates=inventory.inspect(directory,abi)
        checked=set()
        rows=[]
        for candidate in candidates:
            index=candidate[0]
            if index in checked:
                raise ValueError("Duplicate native candidate ID")
            checked.add(index)
            row=native_record(directory,index,abi[4])
            rows.append(review_entry(candidate,row,abi,fields))
        print(report(rows))
    except (OSError,UnicodeError,ValueError,struct.error) as exc:
        print("ROUND79AC3E: READ-ONLY AUDIT REFUSED:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
