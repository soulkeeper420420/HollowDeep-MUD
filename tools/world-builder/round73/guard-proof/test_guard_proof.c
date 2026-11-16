#define _GNU_SOURCE
#include "hd_guard_proof.h"
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static const char *ROOT="guard-proof";
static char guardian_names[HD_GPROOF_MAX][80] = {
    "Treasure Guardian One", "Treasure Guardian Two"
};
static void matching(const hd_guard_proof *a,const hd_guard_proof *b) {
    assert(!strcmp(a->encounter_id,b->encounter_id));
    assert(!strcmp(a->guardian_ids[0],b->guardian_ids[0]));
}
int main(void) {
    char temp[]="/tmp/hollowdeep-73h-proof-XXXXXX";
    hd_guard_proof first, second, again, bad;
    char leaf[80];
    pid_t pid;
    int fd, status;
    unsigned char c;
    assert(mkdtemp(temp) && chdir(temp)==0);
    assert(mkdir(ROOT,0700)==0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&first)==0);
    assert(!hd_guard_proof_ready(&first));
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&second)==0);
    matching(&first,&second);
    assert(hd_guard_proof_begin(ROOT,10002,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&bad)<0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Anotherqa",
                                (const char (*)[80])guardian_names,2,&bad)<0);
    assert(hd_guard_proof_mark(ROOT,&first,2)<0);
    assert(setenv("HD_GPROOF_FAIL","before_rename",1)==0);
    assert(hd_guard_proof_mark(ROOT,&first,0)==HD_GPROOF_ERROR);
    assert(unsetenv("HD_GPROOF_FAIL")==0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&second)==0);
    assert(!second.dead[0]);
    assert(hd_guard_proof_mark(ROOT,&first,0)==0);
    assert(first.dead[0] && !first.dead[1] && first.event_ids[0][0]);
    assert(hd_guard_proof_mark(ROOT,&first,0)==HD_GPROOF_ALREADY);
    /* Failed directory sync is genuinely uncertain, never a durable claim
     * until the caller has independently recovered the record. */
    assert(setenv("HD_GPROOF_FAIL","after_rename",1)==0);
    assert(hd_guard_proof_mark(ROOT,&first,1)==HD_GPROOF_UNCERTAIN);
    assert(unsetenv("HD_GPROOF_FAIL")==0);
    assert(!first.dead[1]); /* caller cannot unlock on uncertain result */
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&second)==0);
    assert(second.dead[1] && hd_guard_proof_ready(&second));
    pid=fork();assert(pid>=0);
    if(pid==0) {
        /* Fresh process has no pointer/chest memory but reads durable IDs. */
        hd_guard_proof recovered;
        if(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&recovered)!=0)
            _exit(1);
        if(!recovered.dead[0] || !recovered.dead[1] ||
           strcmp(recovered.event_ids[0],first.event_ids[0])) _exit(2);
        if(hd_guard_proof_mark(ROOT,&recovered,1)!=HD_GPROOF_ALREADY) _exit(3);
        _exit(0);
    }
    assert(waitpid(pid,&status,0)==pid && WIFEXITED(status) && WEXITSTATUS(status)==0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&again)==0);
    assert(hd_guard_proof_ready(&again));
    matching(&first,&again);
    /* A spoofed stale challenge ID cannot add a kill. */
    bad=first;bad.encounter_id[0]=(bad.encounter_id[0]=='a')?'b':'a';
    assert(hd_guard_proof_mark(ROOT,&bad,1)<0);
    /* Writable same-user sidecars are NOT cryptographic auth; CRC only
     * detects malformed bytes. Stronger authority remains required. */
    snprintf(leaf,sizeof leaf,"%s/g-%s.proof",ROOT,"map.0001");
    fd=open(leaf,O_RDWR);assert(fd>=0);
    assert(lseek(fd,30,SEEK_SET)==30 && read(fd,&c,1)==1);
    c ^= 0x80; assert(lseek(fd,30,SEEK_SET)==30 && write(fd,&c,1)==1);
    assert(close(fd)==0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&bad)<0);
    assert(unlink(leaf)==0);
    assert(symlink("/etc/passwd",leaf)==0);
    assert(hd_guard_proof_begin(ROOT,10001,"map.0001","Nativeqa",
                                (const char (*)[80])guardian_names,2,&bad)<0);
    assert(unlink(leaf)==0);
    /* New map must be newly minted; no stale guardian ids. */
    assert(hd_guard_proof_begin(ROOT,10001,"map.0002","Nativeqa",
                                (const char (*)[80])guardian_names,2,&bad)==0);
    assert(strcmp(first.encounter_id,bad.encounter_id));
    puts("ROUND 73H: durable unique guardian IDs, death proof, restart, spoof/corruption/symlink denial PASS");
    return 0;
}
