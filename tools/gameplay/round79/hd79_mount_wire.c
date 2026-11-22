/* Round79T: two 64-hex, checksummed mount fragments, pure C99.
 * Neither the hex receipt IDs nor the player-lock transaction are
 * selected here. Mixed-generation fragments fail closed by CRC32.
 */
#include "hd79_mount_wire.h"
#include <stdint.h>
#include <string.h>

#define HD79_MAGIC 0x4dU
#define HD79_VERSION 1U
#define HD79_CHECKSUM_OFFSET 56U

static unsigned nibble(char ch)
{
    if (ch>='0' && ch<='9') return (unsigned)(ch-'0');
    if (ch>='a' && ch<='f') return (unsigned)(ch-'a'+10);
    return 255U;
}
static char hexchar(unsigned value)
{
    return "0123456789abcdef"[value&15U];
}
static void put_u24(unsigned char *out,unsigned value)
{
    out[0]=(unsigned char)(value>>16);
    out[1]=(unsigned char)(value>>8);
    out[2]=(unsigned char)value;
}
static unsigned get_u24(const unsigned char *data)
{
    return ((unsigned)data[0]<<16)|
           ((unsigned)data[1]<<8)|data[2];
}
static void put_u32(unsigned char *out,uint32_t value)
{
    out[0]=(unsigned char)(value>>24);
    out[1]=(unsigned char)(value>>16);
    out[2]=(unsigned char)(value>>8);
    out[3]=(unsigned char)value;
}
static uint32_t get_u32(const unsigned char *data)
{
    return ((uint32_t)data[0]<<24)|
           ((uint32_t)data[1]<<16)|
           ((uint32_t)data[2]<<8)|data[3];
}
static uint32_t crc32(const unsigned char *data,unsigned len)
{
    uint32_t crc=UINT32_MAX;
    unsigned i,j;
    for(i=0;i<len;i++) {
        crc^=data[i];
        for(j=0;j<8;j++)
            crc=(crc>>1) ^ (crc&1U ? UINT32_C(0xedb88320):0U);
    }
    return ~crc;
}
static void to_hex(const unsigned char *data,char out[65])
{
    unsigned i;
    for(i=0;i<32;i++) {
        out[2*i]=hexchar((unsigned)data[i]>>4);
        out[2*i+1]=hexchar(data[i]);
    }
    out[64]=0;
}
static int from_hex(const char *input,unsigned char out[32])
{
    unsigned i;
    if (!input) return -1;
    for(i=0;i<64;i++) {
        unsigned hi,lo;
        /* A NUL inside the 64 required characters fails closed. */
        if (!input[i]) return -1;
        hi=nibble(input[i]);
        i++;
        if (!input[i]) return -1;
        lo=nibble(input[i]);
        if (hi>15U || lo>15U) return -1;
        out[(i-1)/2]=(unsigned char)((hi<<4)|lo);
    }
    /* Loop increments twice: i ends at 64, checked below. */
    return input[64]==0 ? 0:-1;
}
int hd79_mount_wire_encode(const hd79_mount_roster *roster,
                           char first[65],char second[65])
{
    unsigned char bytes[64]={0};
    char a[65],b[65];
    unsigned i;
    if (!first || !second || first==second ||
        !hd79_mount_roster_valid(roster)) return -1;
    bytes[0]=HD79_MAGIC;
    bytes[1]=HD79_VERSION;
    bytes[2]=(unsigned char)roster->count;
    bytes[3]=(unsigned char)roster->active_id;
    for(i=0;i<12;i++) {
        unsigned hi=nibble(roster->epoch[i*2]);
        unsigned lo=nibble(roster->epoch[i*2+1]);
        if (hi>15 || lo>15) return -1;
        bytes[4+i]=(unsigned char)((hi<<4)|lo);
    }
    put_u32(bytes+16,roster->revision);
    for(i=0;i<roster->count;i++) {
        const hd79_owned_mount *m=&roster->entries[i];
        unsigned char *slot=bytes+20+i*6;
        if (m->stable_room>HD79_MOUNT_MAX_STABLE_ROOM)
            return -1;
        slot[0]=(unsigned char)m->species;
        slot[1]=(unsigned char)m->endurance;
        slot[2]=(unsigned char)m->stabled;
        put_u24(slot+3,m->stable_room);
    }
    put_u32(bytes+HD79_CHECKSUM_OFFSET,crc32(bytes,HD79_CHECKSUM_OFFSET));
    to_hex(bytes,a);
    to_hex(bytes+32,b);
    memcpy(first,a,sizeof a);
    memcpy(second,b,sizeof b);
    return 0;
}
int hd79_mount_wire_decode(const char *first,const char *second,
                           hd79_mount_roster *out)
{
    unsigned char bytes[64]={0};
    hd79_mount_roster result;
    uint32_t stored,actual;
    unsigned i;
    if (!out || !first || !second) return -1;
    if (from_hex(first,bytes) || from_hex(second,bytes+32))
        return -1;
    if (bytes[0]!=HD79_MAGIC || bytes[1]!=HD79_VERSION ||
        bytes[2]>HD79_MOUNT_MAX_OWNED)
        return -1;
    if (bytes[60] || bytes[61] || bytes[62] || bytes[63])
        return -1;
    stored=get_u32(bytes+HD79_CHECKSUM_OFFSET);
    actual=crc32(bytes,HD79_CHECKSUM_OFFSET);
    if (stored!=actual) return -1;
    memset(&result,0,sizeof result);
    result.count=bytes[2];
    result.active_id=bytes[3];
    for(i=0;i<12;i++) {
        result.epoch[i*2]=hexchar(bytes[4+i]>>4);
        result.epoch[i*2+1]=hexchar(bytes[4+i]);
    }
    result.epoch[24]=0;
    result.revision=get_u32(bytes+16);
    for(i=0;i<result.count;i++) {
        const unsigned char *slot=bytes+20+i*6;
        hd79_owned_mount *m=&result.entries[i];
        m->id=i+1;
        m->species=(int)slot[0];
        m->endurance=slot[1];
        m->stabled=slot[2];
        m->stable_room=get_u24(slot+3);
    }
    /* Unused bytes must be zero to keep encoding canonical. */
    for(i=result.count;i<HD79_MOUNT_MAX_OWNED;i++) {
        const unsigned char *slot=bytes+20+i*6;
        unsigned j;
        for(j=0;j<6;j++)
            if (slot[j]) return -1;
    }
    if (!hd79_mount_roster_valid(&result)) return -1;
    *out=result;
    return 0;
}
