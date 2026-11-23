/* Round 79AA: purely functional physical mount room policy and CRC wire.
 * Nothing here can write a native player save or create a game creature.
 */
#include "hd79_mount_presence.h"
#include <string.h>

static int eq_roster(const hd79_mount_roster *a,const hd79_mount_roster *b)
{
    unsigned i;
    if (!a || !b || strcmp(a->epoch,b->epoch) ||
        a->revision!=b->revision || a->count!=b->count ||
        a->active_id!=b->active_id) return 0;
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++) {
        const hd79_owned_mount *x=&a->entries[i],*y=&b->entries[i];
        if (x->id!=y->id || x->species!=y->species ||
            x->endurance!=y->endurance || x->stabled!=y->stabled ||
            x->stable_room!=y->stable_room) return 0;
    }
    return 1;
}
int hd79_presence_new(const hd79_mount_roster *empty,
                      hd79_mount_presence *out)
{
    hd79_mount_presence p;
    if (!out || !hd79_mount_roster_valid(empty) ||
        empty->count || empty->active_id) return -1;
    memset(&p,0,sizeof p);
    p.revision=empty->revision;
    *out=p;
    return 1;
}
int hd79_presence_valid(const hd79_mount_roster *roster,
                        const hd79_mount_presence *presence)
{
    unsigned i;
    if (!presence || !hd79_mount_roster_valid(roster) ||
        presence->revision!=roster->revision ||
        presence->count!=roster->count ||
        presence->active_id!=roster->active_id) return 0;
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++) {
        unsigned room=presence->room[i];
        if (room>HD79_PRESENCE_MAX_ROOM) return 0;
        if (i>=roster->count || roster->entries[i].stabled ||
            roster->active_id==i+1) {
            if (room) return 0;
        } else if (!room) return 0;
    }
    return 1;
}
static void put_u24(unsigned char *dst,unsigned value)
{
    dst[0]=(unsigned char)(value>>16);
    dst[1]=(unsigned char)(value>>8);
    dst[2]=(unsigned char)value;
}
static unsigned get_u24(const unsigned char *p)
{
    return ((unsigned)p[0]<<16)|((unsigned)p[1]<<8)|p[2];
}
static void put_u32(unsigned char *p,uint32_t v)
{
    p[0]=(unsigned char)(v>>24);
    p[1]=(unsigned char)(v>>16);
    p[2]=(unsigned char)(v>>8);
    p[3]=(unsigned char)v;
}
static uint32_t get_u32(const unsigned char *p)
{
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|
           ((uint32_t)p[2]<<8)|p[3];
}
static uint32_t crc32(const unsigned char *data,unsigned len)
{
    uint32_t crc=UINT32_MAX;
    unsigned i,j;
    for(i=0;i<len;i++) {
        crc^=data[i];
        for(j=0;j<8;j++)
            crc=(crc>>1)^(crc&1U ? UINT32_C(0xedb88320):0U);
    }
    return ~crc;
}
static int nibble(char ch)
{
    if (ch>='0' && ch<='9') return ch-'0';
    if (ch>='a' && ch<='f') return ch-'a'+10;
    return -1;
}
static int unpack(const char *s,unsigned char out[32])
{
    unsigned i;
    /* Header is a fixed-size native receipt field. First validate all
     * expected digits, then require the exact terminator at index 64.
     */
    if (!s) return -1;
    for(i=0;i<32;i++) {
        int h,l;
        if (!s[i*2] || !s[i*2+1]) return -1;
        h=nibble(s[i*2]);l=nibble(s[i*2+1]);
        if (h<0 || l<0) return -1;
        out[i]=(unsigned char)((h<<4)|l);
    }
    return s[64] ? -1:0;
}
static void pack(const unsigned char data[32],char out[65])
{
    static const char hex[]="0123456789abcdef";
    unsigned i;
    for(i=0;i<32;i++) {
        out[2*i]=hex[data[i]>>4];
        out[2*i+1]=hex[data[i]&15U];
    }
    out[64]=0;
}
int hd79_presence_encode(const hd79_mount_roster *roster,
                         const hd79_mount_presence *presence,char out[65])
{
    unsigned char buf[32]={0};
    char output[65];
    unsigned i;
    if (!out || !hd79_presence_valid(roster,presence)) return -1;
    buf[0]='P'; buf[1]=1;
    buf[2]=(unsigned char)presence->count;
    buf[3]=(unsigned char)presence->active_id;
    put_u32(buf+4,presence->revision);
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++)
        put_u24(buf+8+i*3,presence->room[i]);
    put_u32(buf+28,crc32(buf,28));
    pack(buf,output);
    memcpy(out,output,sizeof output);
    return 0;
}
int hd79_presence_decode(const hd79_mount_roster *roster,
                         const char *receipt,hd79_mount_presence *out)
{
    unsigned char buf[32];
    hd79_mount_presence presence;
    unsigned i;
    if (!out || !roster || unpack(receipt,buf) ||
        buf[0]!='P' || buf[1]!=1 || buf[26] || buf[27] ||
        get_u32(buf+28)!=crc32(buf,28)) return -1;
    memset(&presence,0,sizeof presence);
    presence.count=buf[2];
    presence.active_id=buf[3];
    presence.revision=get_u32(buf+4);
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++)
        presence.room[i]=get_u24(buf+8+i*3);
    if (!hd79_presence_valid(roster,&presence)) return -1;
    *out=presence;
    return 0;
}
int hd79_presence_step(const hd79_mount_roster *before,
                       const hd79_mount_presence *old_positions,
                       const hd79_mount_roster *after,
                       unsigned action,unsigned mount_id,
                       unsigned player_room,int native_mount_present,
                       int verified_stable,
                       hd79_mount_presence *new_positions)
{
    hd79_mount_presence next;
    hd79_mount_roster expected;
    int rc=-1;
    if (!new_positions || !hd79_presence_valid(before,old_positions) ||
        !hd79_mount_roster_valid(after) ||
        before->revision==UINT32_MAX ||
        after->revision!=before->revision+1 ||
        strcmp(before->epoch,after->epoch) ||
        !mount_id || mount_id>before->count ||
        !player_room || player_room>HD79_PRESENCE_MAX_ROOM ||
        (native_mount_present!=0 && native_mount_present!=1) ||
        (verified_stable!=0 && verified_stable!=1)) return -1;
    next=*old_positions;
    switch(action) {
    case HD79_PRESENCE_BOARD:
        if (!native_mount_present ||
            old_positions->room[mount_id-1]!=player_room) return 0;
        rc=hd79_mount_board(before,&expected,before->epoch,mount_id,1);
        if (rc==1) next.room[mount_id-1]=0;
        break;
    case HD79_PRESENCE_DISMOUNT:
        if (mount_id!=before->active_id) return 0;
        rc=hd79_mount_dismount(before,&expected,before->epoch);
        if (rc==1) next.room[mount_id-1]=player_room;
        break;
    case HD79_PRESENCE_STABLE:
        if (!verified_stable || !native_mount_present ||
            old_positions->room[mount_id-1]!=player_room) return 0;
        rc=hd79_mount_stable(before,&expected,before->epoch,
                             mount_id,player_room,1,1);
        if (rc==1) next.room[mount_id-1]=0;
        break;
    case HD79_PRESENCE_RETRIEVE:
        if (!verified_stable ||
            before->entries[mount_id-1].stable_room!=player_room) return 0;
        rc=hd79_mount_retrieve(before,&expected,before->epoch,
                               mount_id,player_room,1);
        if (rc==1) next.room[mount_id-1]=player_room;
        break;
    default: return -1;
    }
    if (rc!=1) return rc==0?0:-1;
    if (!eq_roster(&expected,after)) return -1;
    next.revision=after->revision;
    next.count=after->count;
    next.active_id=after->active_id;
    if (!hd79_presence_valid(after,&next)) return -1;
    *new_positions=next;
    return 1;
}
