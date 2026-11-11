#!/usr/bin/env python3
"""Round11E: fault-inject exact private HD11 atomic save helper, never real MUD.

The exact hd11_name_valid + hd11_atomic_player_write C source is extracted
from the already-compiled *private* Round11D staged files2.c. It is built as
a tiny native 32-bit process and tested in independently-created, empty
throwaway directories via a test-only LD_PRELOAD library.
No game, player record or production path is opened.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

STAGE=Path("/root/hollowdeep-dev/guild-social-batch1/round11-atomic-pGqKMYDt")
ROOT=Path("/root/hollowdeep-dev/guild-social-batch1")
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
LIVE=Path("/srv/hollowdeep/world/src_3.00")

def source_digest():
    # Same checksum algorithm as previous Round 10/11 integrity checks.
    cmd = ("find . -type f -print0 | sort -z | "
           "xargs -0 sha256sum | sha256sum | awk '{print $1}'")
    return subprocess.check_output(["bash","-c",cmd],cwd=LIVE,text=True).strip()

def require(condition, message):
    if not condition:
        raise RuntimeError("STOP: " + message)

def command(args, *, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=30, check=False)

require(os.geteuid() == 0, "Run via sudo")
require(source_digest() == EXPECTED, "Live source checksum differs")
require(STAGE.is_dir() and (STAGE/"src/files2.c").is_file(),
        "Expected already-compiled private Round11D source missing")
require((STAGE/"src/frp.new").is_file(), "Private compiler result missing")
require(not (STAGE/"src/files2.c").is_symlink(),
        "Private source must not be a symlink")
require(not (STAGE/"src/frp.new").is_symlink(),
        "Private executable must not be a symlink")
source=(STAGE/"src/files2.c").read_text()
begin_marker="static int hd11_name_valid(const char *name)"
end_marker="/*\n * Retain the native K&R signature"
require(source.count(begin_marker)==1 and source.count(end_marker)==1,
        "Native atomic helper extraction anchors unexpected")
begin=source.index(begin_marker)
end=source.index(end_marker, begin)
helper=source[begin:end]
for symbol in ("hd11_atomic_player_write","mkstemp(","fsync(fd)",
               "rename(temporary, file)","fsync(directory_fd)"):
    require(symbol in helper, "Native helper lacks " + symbol)
require(helper.count("static int hd11_atomic_player_write")==1,
        "Native write helper not unique")

# Only the two small atomic commit functions are extracted. The rest of the
# engine, native player loader, and any game/character files are not involved.
headers = r"""
#define _GNU_SOURCE
#define PLAYERPATH "player"
#include <errno.h>
#include <ctype.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
"""
entry = r"""
int main(int argc, char **argv) {
    int ret;
    if(argc != 3) return(90);
    ret=hd11_atomic_player_write(argv[1],argv[2],strlen(argv[2]));
    return(ret == 0 ? 0 : 3);
}
"""

injector=r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
static int write_once=0, fsync_count=0;
static int fault(const char *name) {
    const char *value=getenv("HD11_FAULT");
    return(value && strcmp(value,name)==0);
}
ssize_t write(int fd, const void *buf, size_t count) {
    ssize_t (*real_write)(int,const void *,size_t)=dlsym(RTLD_NEXT,"write");
    if(fault("write_enospc")) {errno=ENOSPC; return(-1);}
    if(fault("write_eio")) {errno=EIO; return(-1);}
    if(fault("write_eintr_once") && !write_once++) {errno=EINTR;return(-1);}
    if(fault("write_short") && count > 1) count=1;
    if(fault("crash_during_write")) {kill(getpid(),SIGKILL);_exit(99);}
    return real_write(fd,buf,count);
}
int fsync(int fd) {
    int (*real_fsync)(int)=dlsym(RTLD_NEXT,"fsync");
    ++fsync_count;
    if(fault("fsync_eio_first") && fsync_count==1) {
        errno=EIO;return(-1);
    }
    if(fault("fsync_eio_directory") && fsync_count==2) {
        errno=EIO;return(-1);
    }
    if(fault("crash_after_rename") && fsync_count==2) {
        kill(getpid(),SIGKILL);_exit(99);
    }
    return real_fsync(fd);
}
int rename(const char *old, const char *newname) {
    int (*real_rename)(const char *,const char *)=dlsym(RTLD_NEXT,"rename");
    if(fault("rename_eio")) {errno=EIO;return(-1);}
    if(fault("crash_before_rename")) {kill(getpid(),SIGKILL);_exit(99);}
    return real_rename(old,newname);
}
"""

WORK=Path(tempfile.mkdtemp(prefix="round11-fault-", dir=ROOT))
os.chmod(WORK,0o700)
print("=== HOLLOWDEEP ROUND 11E SAVE ATOMICITY FAULT HARNESS ===",flush=True)
print("Live source: VERIFIED UNCHANGED",flush=True)
print("Private atomic-save helper: EXACT EXTRACT, NO GAME EDITS",flush=True)
print("Disposable workspace:",WORK,flush=True)

(WORK/"atomic.c").write_text(headers+"\n"+helper+"\n"+entry)
(WORK/"injector.c").write_text(injector)
cc=command(["gcc","-m32","-std=gnu89","-O1",
            "-fstack-protector-strong","-D_FORTIFY_SOURCE=3",
            "-Wall","-Wextra","atomic.c","-o","atomic-test"],cwd=WORK)
require(cc.returncode==0, "Native 32-bit helper compiler failed:\n"+cc.stderr[-1500:])
lib=command(["gcc","-m32","-std=gnu89","-O1","-shared","-fPIC",
             "-Wall","-Wextra","injector.c","-ldl","-o","libfault.so"],cwd=WORK)
require(lib.returncode==0, "32-bit fault library compiler failed:\n"+lib.stderr[-1500:])
print("32-bit native atomic saver + syscall fault library: COMPILED",flush=True)

OLD=b"LAST_KNOWN_GOOD"
NEW=b"COMPLETED_NEW_SAVE"
failures=0
passes=0

def verify(label, ok, reason):
    global passes, failures
    if ok:
        passes+=1
        print("PASS:",label,flush=True)
    else:
        failures+=1
        print("FAIL:",label,"reason:",reason,flush=True)

def run_case(label, mode, expected_status, expected_content,
             expect_temp=False, name="Hdfaultcase", old=OLD):
    cwd=WORK/"cases"/label
    (cwd/"player").mkdir(parents=True,mode=0o700)
    player=cwd/"player"/name
    if old is not None:
        player.write_bytes(old)
        os.chmod(player,0o600)
    before=player.read_bytes() if player.exists() else None
    env=os.environ.copy()
    env.pop("LD_PRELOAD",None)
    env.pop("HD11_FAULT",None)
    if mode:
        env["LD_PRELOAD"]=str(WORK/"libfault.so")
        env["HD11_FAULT"]=mode
    try:
        done=command([str(WORK/"atomic-test"),name,NEW.decode()],
                     cwd=cwd,env=env)
        code=done.returncode
        contents=player.read_bytes() if player.is_file() else None
        leftover=list((cwd/"player").glob(".hd11-*"))
        correct=(code==expected_status and contents==expected_content
                 and bool(leftover)==expect_temp)
        reason=("status={} expected={}; data={} expected={}; tmp={}"
                .format(code,expected_status,contents,expected_content,
                        len(leftover)))
        verify(label,correct,reason)
    except Exception as exc:
        verify(label,False,str(exc))

print("=== 1. NORMAL COMPLETION AND RETRIES ===",flush=True)
run_case("clean_replacement",None,0,NEW)
run_case("short_write_retry","write_short",0,NEW)
run_case("eintr_retry","write_eintr_once",0,NEW)
run_case("new_account_save",None,0,NEW,old=None)

print("=== 2. FAILED WRITES: OLD PRIMARY MUST SURVIVE ===",flush=True)
run_case("enospc_write","write_enospc",3,OLD)
run_case("eio_write","write_eio",3,OLD)
run_case("failed_file_fsync","fsync_eio_first",3,OLD)
run_case("failed_rename","rename_eio",3,OLD)

print("=== 3. CRASHES: OLD OR COMMITTED NEW PRIMARY ===",flush=True)
run_case("killed_during_write","crash_during_write",-9,OLD,expect_temp=True)
run_case("killed_before_rename","crash_before_rename",-9,OLD,expect_temp=True)
run_case("killed_after_rename","crash_after_rename",-9,NEW)

print("=== 4. DIR SYNC FAILURE: NEW COMPLETE PRIMARY, ERROR REPORTED ===",flush=True)
run_case("failed_directory_fsync","fsync_eio_directory",3,NEW)

print("=== 5. REFUSE SYMLINK AND INVALID ACCOUNT ===",flush=True)
unsafe=WORK/"cases"/"symlink_target"
(unsafe/"player").mkdir(parents=True,mode=0o700)
target=unsafe/"untouched.txt"
target.write_bytes(OLD)
(unsafe/"player"/"Hdfaultcase").symlink_to(target)
env=os.environ.copy();env.pop("LD_PRELOAD",None);env.pop("HD11_FAULT",None)
out=command([str(WORK/"atomic-test"),"Hdfaultcase",NEW.decode()],cwd=unsafe,env=env)
verify("existing_symlink_refused",
       out.returncode==3 and target.read_bytes()==OLD
       and (unsafe/"player"/"Hdfaultcase").is_symlink(),
       "result={}".format(out.returncode))

bad=WORK/"cases"/"bad_name"
(bad/"player").mkdir(parents=True,mode=0o700)
out=command([str(WORK/"atomic-test"),"../bad",NEW.decode()],cwd=bad,env=env)
verify("traversal_name_refused",out.returncode==3 and
       list((bad/"player").iterdir())==[],
       "result={}".format(out.returncode))

print("=== 6. PRODUCTION SOURCE INTEGRITY RECHECK ===",flush=True)
require(source_digest()==EXPECTED, "Live source changed during fault tests")
print("Production source hash: UNCHANGED",flush=True)
print("Production engine/rooms/characters: NOT ACCESSED",flush=True)
print("Private guild binary and characters: NOT MODIFIED",flush=True)
print("Synthetic temp files intentionally remain in crash-only cases",flush=True)
print("=== ROUND 11E SUMMARY ===",flush=True)
print("Passed:",passes,flush=True)
print("Failed:",failures,flush=True)
print("Report workspace:",WORK,flush=True)
print("Release safety: PENDING FULL-NATIVE LOAD + EQUIPMENT + LEDGER TESTS",flush=True)
if failures:
    sys.exit(2)
