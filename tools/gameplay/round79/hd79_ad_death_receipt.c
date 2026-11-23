/* Round79AD R2: canonical 32-byte, 64-hex prospective mount death receipt.
 * 0:'D';1:version1;2:owner count;3:monotone death bits (max six);
 * 4..7:death serial big endian;8..19:12 raw epoch bytes;
 * 20..27:zero reserved;28..31:CRC32 of bytes 0..27.
 * This is not an auth token and cannot enable reconnect.
 */
#include "hd79_ad_death_receipt.h"
#include <limits.h>
#include <string.h>

static int digit(char c)
{
    if(c>='0'&&c<='9')return c-'0';
    if(c>='a'&&c<='f')return c-'a'+10;
    return -1;
}
static void u32put(unsigned char *p,uint32_t v)
{
    p[0]=(unsigned char)(v>>24);p[1]=(unsigned char)(v>>16);
    p[2]=(unsigned char)(v>>8);p[3]=(unsigned char)v;
}
static uint32_t u32get(const unsigned char *p)
{
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|
           ((uint32_t)p[2]<<8)|p[3];
}
static uint32_t crc32(const unsigned char *data,unsigned n)
{
    uint32_t crc=UINT32_MAX;
    unsigned i,j;
    for(i=0;i<n;i++) {
        crc^=data[i];
        for(j=0;j<8;j++)
            crc=(crc>>1)^((crc&1U)?UINT32_C(0xedb88320):0U);
    }
    return ~crc;
}
static int epoch_bytes(const char *text,unsigned char bytes[12])
{
    unsigned i;
    if(!text)return 0;
    for(i=0;i<12;i++){
        int high=digit(text[i*2]),low=digit(text[i*2+1]);
        if(high<0||low<0)return 0;
        bytes[i]=(unsigned char)((high<<4)|low);
    }
    return text[24]==0;
}
int hd79_ad_death_valid(const hd79_mount_roster *roster,
                        const hd79_ad_death_receipt *death)
{
    unsigned char check[12];
    if(!death || !hd79_mount_roster_valid(roster) ||
       !epoch_bytes(death->epoch,check) ||
       strcmp(roster->epoch,death->epoch) ||
       !death->serial || death->count!=roster->count ||
       death->count>HD79_MOUNT_MAX_OWNED ||
       (death->dead_mask & ~((1U<<death->count)-1U)))return 0;
    return 1;
}
int hd79_ad_death_new_empty(const hd79_mount_roster *roster,
                            hd79_ad_death_receipt *out)
{
    hd79_ad_death_receipt fresh;
    if(!out||!hd79_mount_roster_valid(roster)||roster->count||
       roster->active_id)return -1;
    memset(&fresh,0,sizeof fresh);
    memcpy(fresh.epoch,roster->epoch,sizeof fresh.epoch);
    fresh.serial=1;
    *out=fresh;
    return 1;
}
int hd79_ad_death_wire_encode(const hd79_mount_roster *roster,
                              const hd79_ad_death_receipt *death,char out[65])
{
    unsigned char bytes[32]={0};
    char hex[65];
    unsigned i;
    static const char digits[]="0123456789abcdef";
    if(!out||!hd79_ad_death_valid(roster,death)||
       !epoch_bytes(death->epoch,bytes+8))return -1;
    bytes[0]='D';bytes[1]=1;
    bytes[2]=(unsigned char)death->count;
    bytes[3]=(unsigned char)death->dead_mask;
    u32put(bytes+4,death->serial);
    u32put(bytes+28,crc32(bytes,28));
    for(i=0;i<32;i++){
        hex[i*2]=digits[bytes[i]>>4];
        hex[i*2+1]=digits[bytes[i]&15];
    }
    hex[64]=0;
    memcpy(out,hex,sizeof hex);
    return 0;
}
int hd79_ad_death_wire_decode(const hd79_mount_roster *roster,
                              const char *encoded,hd79_ad_death_receipt *out)
{
    unsigned char bytes[32],expected_epoch[12];
    hd79_ad_death_receipt fresh;
    unsigned i;
    if(!out||!encoded||!hd79_mount_roster_valid(roster)||
       !epoch_bytes(roster->epoch,expected_epoch))return -1;
    /* The fixed player-receipt slot is at least 65 bytes. Read at most
     * 65 and reject noncanonical uppercase and overlong payloads. */
    for(i=0;i<32;i++) {
        int high,low;
        if(!encoded[2*i]||!encoded[2*i+1])return -1;
        high=digit(encoded[2*i]);low=digit(encoded[2*i+1]);
        if(high<0||low<0)return -1;
        bytes[i]=(unsigned char)((high<<4)|low);
    }
    if(encoded[64] || bytes[0]!='D' || bytes[1]!=1 ||
       memcmp(bytes+8,expected_epoch,12) ||
       bytes[20] || bytes[21] || bytes[22] || bytes[23] ||
       bytes[24] || bytes[25] || bytes[26] || bytes[27] ||
       u32get(bytes+28)!=crc32(bytes,28))return -1;
    memset(&fresh,0,sizeof fresh);
    memcpy(fresh.epoch,roster->epoch,sizeof fresh.epoch);
    fresh.serial=u32get(bytes+4);
    fresh.count=bytes[2];fresh.dead_mask=bytes[3];
    if(!hd79_ad_death_valid(roster,&fresh))return -1;
    *out=fresh;
    return 0;
}
int hd79_ad_death_mark(const hd79_mount_roster *roster,
                       const hd79_ad_death_receipt *prior,unsigned id,
                       hd79_ad_death_receipt *next)
{
    hd79_ad_death_receipt copy;
    unsigned bit;
    if(!next||!hd79_ad_death_valid(roster,prior)||!id||
       id>prior->count||prior->serial==UINT32_MAX)return -1;
    bit=1U<<(id-1);
    if(prior->dead_mask&bit)return 0;
    copy=*prior;
    copy.serial++;
    copy.dead_mask|=bit;
    *next=copy;
    return 1;
}
int hd79_ad_death_award_step(const hd79_mount_roster *before,
                             const hd79_ad_death_receipt *prior,
                             const hd79_mount_roster *after,
                             hd79_ad_death_receipt *next)
{
    hd79_ad_death_receipt copy;
    unsigned i;
    if(!next||!hd79_ad_death_valid(before,prior)||
       !hd79_mount_roster_valid(after)||prior->serial==UINT32_MAX||
       before->revision==UINT32_MAX||
       after->revision!=before->revision+1||
       after->count!=before->count+1 ||
       after->active_id!=before->active_id ||
       strcmp(before->epoch,after->epoch)||
       after->entries[after->count-1].id!=after->count)return -1;
    for(i=0;i<before->count;i++) {
        const hd79_owned_mount *a=&before->entries[i],*b=&after->entries[i];
        if(a->id!=b->id||a->species!=b->species||
           a->endurance!=b->endurance||a->stabled!=b->stabled||
           a->stable_room!=b->stable_room)return -1;
    }
    copy=*prior;
    copy.serial++;
    copy.count=after->count;
    if(!hd79_ad_death_valid(after,&copy))return -1;
    *next=copy;
    return 1;
}
int hd79_ad_death_action_eligible(const hd79_mount_roster *roster,
                                  const hd79_ad_death_receipt *death,
                                  unsigned id)
{
    if(!hd79_ad_death_valid(roster,death)||!id||id>death->count)
        return 0;
    return (death->dead_mask&(1U<<(id-1))) ? 0:1;
}
int hd79_ad_death_reconnect_allowed(const hd79_mount_roster *roster,
                                    const hd79_ad_death_receipt *death,
                                    unsigned id)
{
    (void)roster;(void)death;(void)id;
    /* No native death evidence or safe spawn-provenance receipt yet.
     * NEVER interpret a zero death bit as proof of being alive. */
    return 0;
}
