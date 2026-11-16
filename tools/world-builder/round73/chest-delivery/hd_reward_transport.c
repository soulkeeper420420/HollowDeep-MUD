#define _GNU_SOURCE
/* Isolated 73J client: verified OS socket peer, bounded fixed wire grammar.
 * This is NOT safe as a player command or a production privilege boundary.
 */
#include "hd_reward_transport.h"
#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>

#define HD_WIRE_CAP 4096U
static int id32(const char *s) {
    unsigned i;
    if(!s || strlen(s)!=32U) return 0;
    for(i=0;i<32;++i) if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f'))) return 0;
    return 1;
}
static int id64(const char *s) {
    unsigned i;
    if(!s || strlen(s)!=64U) return 0;
    for(i=0;i<64;++i) if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f'))) return 0;
    return 1;
}
static int token(const char *s, unsigned n) {
    unsigned i;
    if(!s) return 0;
    for(i=0;i<n && s[i];++i) {
        char c=s[i];
        if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||(c>='A'&&c<='Z')||
             c=='.'||c==':'||c=='_'||c=='-'))return 0;
    }
    return i>=3U && i<n;
}
static int decimal(const char *s,long max,long *out) {
    long n=0;
    if(!s || !s[0])return 0;
    for(;*s;++s) {
        if(*s<'0'||*s>'9'||n>(max-(*s-'0'))/10L)return 0;
        n=n*10L+(*s-'0');
    }
    *out=n;return 1;
}
static int exchange(const char *path,uid_t expected,
                    const char *request,char *reply,size_t cap) {
    int fd=-1,rc=-1;
    size_t pos=0, n, bytes;
    struct sockaddr_un addr;
    struct ucred peer;
    struct timeval tv;
    socklen_t len=sizeof peer;
    if(!path||!request||!reply||cap<2U ||
       strlen(path)>=sizeof(addr.sun_path))return -1;
    bytes=strlen(request);
    if(bytes<2U || bytes>1024U || request[bytes-1]!='\n')return -1;
    memset(&addr,0,sizeof addr);
    addr.sun_family=AF_UNIX;
    memcpy(addr.sun_path,path,strlen(path)+1U);
    fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
    if(fd<0)return -1;
    tv.tv_sec=2;tv.tv_usec=0;
    if(setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof tv)||
       setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof tv)||
       connect(fd,(struct sockaddr *)&addr,(socklen_t)(offsetof(struct sockaddr_un,sun_path)+strlen(path)+1U))||
       getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&peer,&len)||
       len!=sizeof peer||peer.uid!=expected)goto done;
    pos=0;
    while(pos<bytes) {
        ssize_t w=send(fd,request+pos,bytes-pos,MSG_NOSIGNAL);
        if(w<0&&errno==EINTR)continue;
        if(w<=0)goto done;
        pos+=(size_t)w;
    }
    if(shutdown(fd,SHUT_WR))goto done;
    pos=0;
    while(pos+1U<cap) {
        ssize_t r=recv(fd,reply+pos,1,0);
        if(r<0&&errno==EINTR)continue;
        if(r<=0)goto done;
        ++pos;
        if(reply[pos-1U]=='\n')break;
    }
    if(!pos || reply[pos-1U]!='\n')goto done;
    reply[pos-1U]='\0';
    rc=0;
done:
    close(fd);
    return rc;
}
static int split(char *s,char **parts,int max) {
    int n=0;
    char *start=s,*p=s;
    while(*p) {
        if(*p=='\r'||*p=='\n')return -1;
        if(*p=='|') {
            if(n>=max||p==start)return -1;
            *p='\0';parts[n++]=start;start=p+1;
        }
        ++p;
    }
    if(!*start||n>=max)return -1;
    parts[n++]=start;
    return n;
}
int hd_reward_fetch(const char *sock,uid_t uid,const hd_guard_proof *p,
                    hd_native_reward *out) {
    char request[256], reply[HD_WIRE_CAP+1U],*parts[5+HD_REWARD_LIMIT];
    hd_native_reward m;
    long gold,count,tid,power;
    int n,k,i;
    if(!p||!out)return HD_TRANSPORT_DENIED;
    memset(out,0,sizeof *out);memset(&m,0,sizeof m);
    if(!id32(p->encounter_id)||!token(p->owner,80)||!token(p->map,33))return HD_TRANSPORT_DENIED;
    n=snprintf(request,sizeof request,"GRANT|%s|%s|%s\n",p->encounter_id,p->owner,p->map);
    if(n<0||(size_t)n>=sizeof request ||exchange(sock,uid,request,reply,sizeof reply))return HD_TRANSPORT_DENIED;
    if(!strcmp(reply,"ALREADY"))return HD_TRANSPORT_ALREADY;
    k=split(reply,parts,5+HD_REWARD_LIMIT);
    if(k<5||strcmp(parts[0],"MANIFEST")||!id32(parts[1])||!id64(parts[2])||
       !decimal(parts[3],1000000L,&gold)||!decimal(parts[4],HD_REWARD_LIMIT,&count)||
       k!=5+(int)count ||(count==0&&gold==0))return HD_TRANSPORT_DENIED;
    strncpy(m.owner,p->owner,sizeof m.owner-1U);
    strcpy(m.claim_id,parts[1]);strcpy(m.digest,parts[2]);
    m.gold=gold;m.count=(unsigned)count;
    for(i=0;i<(int)count;++i) {
        char *fields[4], *line=parts[5+i], *pos;
        int z;
        fields[0]=line;
        for(z=1;z<4;++z) {
            pos=strchr(fields[z-1],',');
            if(!pos || pos==fields[z-1]) return HD_TRANSPORT_DENIED;
            *pos='\0';fields[z]=pos+1;
        }
        if(!*fields[3]||strchr(fields[3],',') || !id32(fields[0]) ||
           !decimal(fields[1],OMAX-1,&tid) || tid<1 ||
           (strcmp(fields[2],"i") && strcmp(fields[2],"m")) ||
           !decimal(fields[3],0,&power) || power) return HD_TRANSPORT_DENIED;
        strcpy(m.items[i].instance_id,fields[0]);
        m.items[i].template_id=(int)tid;
        m.items[i].kind=fields[2][0];
        m.items[i].enchant_power=0;
        for(z=0;z<i;++z)
            if(!strcmp(m.items[z].instance_id,m.items[i].instance_id))
                return HD_TRANSPORT_DENIED;
    }
    *out=m;
    return HD_TRANSPORT_MANIFEST;
}
int hd_reward_ack(const char *sock,uid_t uid,const hd_guard_proof *p,
                  const hd_native_reward *m) {
    char request[320],reply[64];
    int n;
    if(!p||!m||!id32(p->encounter_id)||!id32(m->claim_id)||
       !id64(m->digest)||!token(p->owner,80)||!token(p->map,33)||
       strcmp(p->owner,m->owner))return HD_TRANSPORT_DENIED;
    n=snprintf(request,sizeof request,"ACK|%s|%s|%s|%s|%s\n",
               p->encounter_id,p->owner,p->map,m->claim_id,m->digest);
    if(n<0||(size_t)n>=sizeof request || exchange(sock,uid,request,reply,sizeof reply))return HD_TRANSPORT_DENIED;
    return !strcmp(reply,"DELIVERED") ? 0 : HD_TRANSPORT_DENIED;
}
