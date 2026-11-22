#!/usr/bin/env python3
"""Round79K: isolated real-socket player Breath travel and HUD acceptance.

Builds a synthetic three-area native world, with two mapped wilderness
tiles and reciprocal room exits. Never loads or copies production world
rooms, player saves, server config, credentials or network listeners.
"""
from pathlib import Path
import os
import re
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import time

if len(sys.argv)!=2:
    raise SystemExit("Usage: check_breath_travel_socket.py PRIVATE_ELF32_SRC")
SOURCE=Path(sys.argv[1])
if (os.geteuid()!=0 or
    os.readlink("/proc/self/ns/net")==os.readlink("/proc/1/ns/net") or
    SOURCE.name!="src" or SOURCE.is_symlink() or
    SOURCE.parent.parent!=Path("/tmp") or
    not SOURCE.parent.name.startswith("hd-army-game-round79travel-")):
    raise SystemExit("Private root, network namespace and travel source required")
exe=SOURCE/"frp.new"
if exe.is_symlink() or not exe.is_file() or exe.open("rb").read(5)!=b"\x7fELF\x01":
    raise SystemExit("Missing verified private ELF32 game")

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
NECRO=REPO/"necromancer"
prior=runpy.run_path(str(NECRO/"corpse/gameplay_smoke.py"))
cache=runpy.run_path(str(NECRO/"cache/cache_gameplay.py"))
world=Path(tempfile.mkdtemp(prefix="hd79k-breath-socket-",dir="/tmp"))
print("PRIVATE SOCKET WORLD:",world,flush=True)
for folder in ("rooms","player","log","objmon","post",
               "help","bin","hollowdeep-data"):
    (world/folder).mkdir()

def once(body,old,new,label):
    if body.count(old)!=1:
        raise RuntimeError("Private native fixture anchor drift: "+label)
    return body.replace(old,new,1)

# Build from previously tested two-room native fixture. Add a connected
# wilderness segment with actual native exit records and native room files.
source=cache["fixture_source"](prior["SOURCE"])
source=once(source,
    'room site = {0}, annex = {0};',
    'room site = {0}, annex = {0}, meadow = {0}, ridge = {0};',
    "fixture room declarations")
source=once(source,
    'exit_ north = {0}, south = {0};',
    'exit_ north = {0}, south = {0}, east = {0}, west = {0}, '
    'r_north = {0}, r_south = {0};',
    "fixture exit declarations")
source=once(source,
    'xtag ntag = {0}, stag = {0};',
    'xtag ntag = {0}, stag = {0}, etag = {0}, '
    'wtag = {0}, rntag = {0}, rstag = {0};',
    "fixture exit-list declarations")

# Create all exits BEFORE the existing native room serialization.
anchor='annex.rom_num = 2; annex.hilevel = 60; annex.first_ext = &stag;'
extra=r'''
    strcpy(east.name,"east"); east.room=10001;
    etag.ext=&east; stag.next_tag=&etag;
    strcpy(west.name,"west"); west.room=2;
    strcpy(r_north.name,"north"); r_north.room=10002;
    wtag.ext=&west; rntag.ext=&r_north; wtag.next_tag=&rntag;
    strcpy(r_south.name,"south"); r_south.room=10001;
    rstag.ext=&r_south;
    strcpy(meadow.name,"Test Wilderness Meadow");
    meadow.long_desc="A private mapped meadow for testing native Breath travel.";
    meadow.rom_num=10001; meadow.hilevel=60; meadow.first_ext=&wtag;
    strcpy(ridge.name,"Test Wilderness Ridge");
    ridge.long_desc="A second private wilderness tile beyond the meadow.";
    ridge.rom_num=10002; ridge.hilevel=60; ridge.first_ext=&rstag;'''
source=once(source,anchor,anchor+"\n"+extra,
            "create reciprocal test wilderness exits")
writes=r'''
    fd=open("rooms/r10001",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
    assert(fd>=0);assert(write_rom(fd,&meadow,ALLITEMS)==0);
    assert(fsync(fd)==0);assert(close(fd)==0);
    fd=open("rooms/r10002",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
    assert(fd>=0);assert(write_rom(fd,&ridge,ALLITEMS)==0);
    assert(fsync(fd)==0);assert(close(fd)==0);
'''
source=once(source,
    '    strcpy(mage.name, "Hdnecroqa");',
    writes+'    strcpy(mage.name, "Hdnecroqa");',
    "create native wilderness room records")
source=once(source,
    '    mage.experience = 10000;',
    '    mage.experience = 10000;\n'
    '    F_SET(&mage,PPROMP);\n'
    '    F_SET(&mage,PANSIC);',
    "enable saved ANSI/HP MP Breath fixture prompt")

# Compile only a synthetic native fixture with the already established
# ELF32 serializer; the game executable itself was compiled separately.
prior["compile_fixture"].__globals__["SOURCE"]=source
seed=prior["compile_fixture"](SOURCE,world,"-m32")
subprocess.run([str(seed)],cwd=world,check=True,timeout=30)
(world/"rooms/wilderness.map").write_text(
    "HDW1\n"
    "10001\t1\t1\t.\tPrivate Test\t-\n"
    "10002\t1\t2\tF\tPrivate Test\t-\n",
    encoding="ascii")

# Populate unrelated low-numbered startup room targets with isolated
# native room fixtures, just like the existing character-creation tests.
required={i for i in range(201)}
for p in (SOURCE/"player.c",SOURCE/"command1.c"):
    body=p.read_text(encoding="latin-1")
    for m in re.finditer(r'(?:rom_num\s*=\s*|load_rom\s*\(\s*)(\d+)',body):
        required.add(int(m.group(1)))
for number in required:
    if 0<=number<10000:
        filename=world/"rooms"/("r%05d"%number)
        if not filename.exists():
            shutil.copyfile(world/"rooms/r00002",filename)

for page in (NECRO/"petruntime/gameplay/help").iterdir():
    if page.is_file():
        shutil.copyfile(page,world/"help"/page.name)

prior["prepare_chroot"](exe,world)
chroot=shutil.which("chroot",path="/usr/sbin:/usr/bin:/sbin:/bin")
assert chroot
with socket.socket() as sock:
    sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
process=None
log=world/("listener-%d.log"%port)
ansi=re.compile(r"\x1b\[[0-9;]*m")

def clean(s):
    return ansi.sub("",s)

def ask(client,query,marker):
    for attempt in range(8):
        output=prior["command"](client,query)
        delay=re.search(r"Please wait (\d+) more seconds?",output,re.I)
        if delay:
            time.sleep(int(delay[1])+1)
            continue
        if marker.lower() not in clean(output).lower():
            # Native movement commands may print only the direction.
            # Require the destination via a separate read-only LOOK.
            # The LOOK must not spend Breath.
            seen=prior["room_view"](client)
            if marker.lower() not in clean(seen).lower():
                raise AssertionError("Native command "+repr(query)+
                                     " missing "+repr(marker)+"; "+
                                     repr((output+"\n"+seen)[-900:]))
        return output
    raise RuntimeError("Native movement cooldown limit reached: "+query)

try:
    with log.open("wb") as out:
        process=subprocess.Popen([
            chroot,"--userspec=65534:65534","--groups=65534",
            str(world),"/bin/hollowdeep",str(port)
        ],cwd=world,
            env={"PATH":"/usr/bin:/bin","HOLLOWDEEP_BIND":"127.0.0.1"},
            stdout=out,stderr=subprocess.STDOUT)
    with prior["connect_game"](port,process) as player:
        prior["login"](player,"Hdnecroqa")
        skills=ask(player,"skills","Breath 100/100")
        assert "\x1b[" in skills, "Saved ANSI should be enabled"
        print("PASS: native character HUD shows persisted initial 100/100 Breath",
              flush=True)

        ask(player,"north","Necromancer Trial Annex")
        skills=ask(player,"skills","Breath 100/100")
        ask(player,"east","Test Wilderness Meadow")
        ask(player,"skills","Breath 98/100")
        ask(player,"north","Test Wilderness Ridge")
        ask(player,"skills","Breath 96/100")
        ask(player,"south","Test Wilderness Meadow")
        ask(player,"skills","Breath 94/100")
        ask(player,"go west","Necromancer Trial Annex")
        ask(player,"skills","Breath 94/100")
        print("PASS: real directional + named exits charge only wilderness entry",
              flush=True)

        denied=prior["command"](player,"go north")
        assert "don't see that exit" in clean(denied).lower() or \
               "can't go" in clean(denied).lower()
        ask(player,"skills","Breath 94/100")
        print("PASS: failed exit cannot charge Breath",flush=True)

        ask(player,"save","Player saved.")
        prior["quit_with_cooldown"](player,process)

    with prior["connect_game"](port,process) as returning:
        prior["login"](returning,"Hdnecroqa")
        ask(returning,"skills","Breath 94/100")
        print("PASS: native save/logout/reconnect preserves spent Breath",
              flush=True)
        prior["quit_with_cooldown"](returning,process)
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

print("ROUND 79K: PRIVATE SOCKET BREATH TRAVEL + HUD PASS",flush=True)
print("MOUNT OWNERSHIP / +15 RESTING: NOT YET CONNECTED",flush=True)
print("PRODUCTION DEPLOYMENT: NONE",flush=True)
