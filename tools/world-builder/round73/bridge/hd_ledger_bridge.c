#define _GNU_SOURCE
/* Round 73I: bounded native-to-trusted-ledger transport, TEST-GATED only.
 * The caller must already have checked the precise monster pointer, owner,
 * and actual held map. No request body may originate from player text.
 */
#include "hd_ledger_bridge.h"
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/time.h>
#include <unistd.h>

static int token(const char *s, size_t max, unsigned min) {
    unsigned i;
    if(!s) return 0;
    for(i=0; i<max && s[i]; ++i) {
        unsigned char c=(unsigned char)s[i];
        if(!((c>='0'&&c<='9')||(c>='A'&&c<='Z')||
              (c>='a'&&c<='z')||c=='.'||c==':'||c=='_'||c=='-')) return 0;
    }
    return i>=min && i<max;
}
static int hex32(const char *s) {
    unsigned i;
    if(!s || s[32]) return 0;
    for(i=0;i<32;++i)
        if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f'))) return 0;
    return 1;
}
static int name_ok(const char *s) {
    unsigned i;
    if(!s)return 0;
    for(i=0;i<80 && s[i];++i) {
        unsigned char c=(unsigned char)s[i];
        if(c<32 || c>126 || c=='|' || c=='\r' || c=='\n')return 0;
    }
    return i>0 && i<80 && s[0]!=' ' && s[i-1]!=' ';
}
static int append(char *buf, size_t cap, size_t *used, const char *item) {
    int n;
    if(*used>=cap) return -1;
    n=snprintf(buf+*used,cap-*used,"|%s",item);
    if(n<0 || (size_t)n>=cap-*used) return -1;
    *used+=(size_t)n;
    return 0;
}
static int dispatch(const char *path,uid_t server_uid,const char *body) {
    int fd=-1, ret=HD_LEDGER_DENIED, n, off=0;
    struct sockaddr_un addr;
    struct ucred cred;
    socklen_t len=sizeof cred;
    struct timeval tv;
    char resp[32];
    size_t total=strlen(body),pos=0;
    if(!path||!body||!path[0]||strlen(path)>=sizeof addr.sun_path||total==0||total>1024) return ret;
    memset(&addr,0,sizeof addr);
    addr.sun_family=AF_UNIX;
    memcpy(addr.sun_path,path,strlen(path)+1);
    fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
    if(fd<0)return ret;
    tv.tv_sec=2;tv.tv_usec=0;
    if(setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof tv) ||
       setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof tv) ||
       connect(fd,(struct sockaddr *)&addr,(socklen_t)(offsetof(struct sockaddr_un,sun_path)+strlen(path)+1)) ||
       getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&len) ||
       len!=sizeof cred || cred.uid!=server_uid) goto done;
    while(pos<total) {
        ssize_t w=send(fd,body+pos,total-pos,MSG_NOSIGNAL);
        if(w<0&&errno==EINTR)continue;
        if(w<=0)goto done;
        pos+=(size_t)w;
    }
    if(shutdown(fd,SHUT_WR))goto done;
    while(off<(int)sizeof(resp)-1) {
        n=(int)recv(fd,resp+off,1,0);
        if(n<0 && errno==EINTR)continue;
        if(n<=0)goto done;
        off+=n;
        if(resp[off-1]=='\n')break;
    }
    resp[off]='\0';
    if(!strcmp(resp,"OK\n"))ret=HD_LEDGER_OK;
    else if(!strcmp(resp,"READY\n"))ret=HD_LEDGER_READY;
    else if(!strcmp(resp,"PENDING\n"))ret=HD_LEDGER_PENDING;
    /* DELIVERED is deliberately not a grant/replay permission. */
done:
    if(fd>=0)close(fd);
    return ret;
}
int hd_ledger_begin(const char *sock, uid_t uid, const hd_guard_proof *p) {
    char req[1025];
    unsigned i;
    size_t used;
    int n;
    if(!p||!hex32(p->encounter_id)||!token(p->map,sizeof p->map,3)||
       !token(p->owner,sizeof p->owner,3)||p->room<10000U||p->room>=16000U||
       p->count==0||p->count>HD_GPROOF_MAX)return HD_LEDGER_DENIED;
    n=snprintf(req,sizeof req,"BEGIN|%s|%s|%s|%u|%u",p->encounter_id,p->map,p->owner,
               (unsigned)p->room,(unsigned)p->count);
    if(n<0||(size_t)n>=sizeof req)return HD_LEDGER_DENIED;
    used=(size_t)n;
    for(i=0;i<p->count;++i) {
        if(!hex32(p->guardian_ids[i])||!name_ok(p->names[i])||
           append(req,sizeof req,&used,p->guardian_ids[i])||
           append(req,sizeof req,&used,p->names[i]))return HD_LEDGER_DENIED;
    }
    if(used>=sizeof(req)-1)return HD_LEDGER_DENIED;
    req[used++]='\n';req[used]='\0';
    return dispatch(sock,uid,req)==HD_LEDGER_OK ? HD_LEDGER_OK : HD_LEDGER_DENIED;
}
int hd_ledger_kill(const char *sock, uid_t uid, const hd_guard_proof *p,unsigned index) {
    char req[256];
    int n;
    if(!p||index>=p->count||p->count>HD_GPROOF_MAX||!hex32(p->encounter_id)||
       !hex32(p->guardian_ids[index])||!hex32(p->event_ids[index])||
       !token(p->owner,sizeof p->owner,3)||p->dead[index]!=1U)return HD_LEDGER_DENIED;
    n=snprintf(req,sizeof req,"KILL|%s|%s|%s|%s\n",p->encounter_id,
               p->guardian_ids[index],p->event_ids[index],p->owner);
    if(n<0||(size_t)n>=sizeof req)return HD_LEDGER_DENIED;
    return dispatch(sock,uid,req);
}
int hd_ledger_claim(const char *sock,uid_t uid,const hd_guard_proof *p) {
    char req[256];
    int n;
    if(!p||!hex32(p->encounter_id)||!token(p->owner,sizeof p->owner,3)||
       !token(p->map,sizeof p->map,3))return HD_LEDGER_DENIED;
    n=snprintf(req,sizeof req,"CLAIM|%s|%s|%s\n",p->encounter_id,p->owner,p->map);
    if(n<0||(size_t)n>=sizeof req)return HD_LEDGER_DENIED;
    return dispatch(sock,uid,req)==HD_LEDGER_PENDING?HD_LEDGER_PENDING:HD_LEDGER_DENIED;
}
