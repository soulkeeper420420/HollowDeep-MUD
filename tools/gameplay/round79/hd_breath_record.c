/* Round 79F: standalone, deterministic Breath atomic-receipt payload.
 * No native pointer access, no file writes, no shared mutable globals.
 */
#include "hd_breath_record.h"
#include "hd_wilderness_breath.h"
#include <stdio.h>
#include <string.h>

static int hd_breath_nibble(char ch)
{
    if (ch>='0' && ch<='9') return ch-'0';
    if (ch>='a' && ch<='f') return ch-'a'+10;
    return -1;
}
static int hd_breath_epoch_ok(const char *p)
{
    unsigned i,nonzero=0;
    if (!p) return 0;
    for(i=0;i<24;i++) {
        int v;
        if (!p[i]) return 0;
        v=hd_breath_nibble(p[i]);
        if(v<0) return 0;
        nonzero|=(unsigned)v;
    }
    return p[24]==0 && nonzero!=0;
}
static int hd_breath_read_hex(const char *in, unsigned n, uint32_t *out)
{
    unsigned i;
    uint32_t value=0;
    for(i=0;i<n;i++) {
        int d=hd_breath_nibble(in[i]);
        if(d<0) return -1;
        value=(value<<4)|(uint32_t)d;
    }
    *out=value;
    return 0;
}
int hd_breath_record_valid(const hd_breath_record *s)
{
    return s && hd_breath_epoch_ok(s->epoch) && s->revision &&
           s->last_recover && s->current<=HD_BREATH_MAX;
}
int hd_breath_record_new(hd_breath_record *out,const char *epoch,
                         uint32_t now)
{
    hd_breath_record s;
    if (!out || !hd_breath_epoch_ok(epoch) || !now) return -1;
    memset(&s,0,sizeof s);
    memcpy(s.epoch,epoch,25);
    s.revision=1;
    s.last_recover=now;
    s.current=HD_BREATH_MAX;
    *out=s;
    return 0;
}
int hd_breath_record_encode(const hd_breath_record *s,char out[65])
{
    char wire[65];
    int n;
    if (!out || !hd_breath_record_valid(s)) return -1;
    /* v1(2) + epoch(24) + revision(8) + tick(8) + current(2)
       + max(2) + flags(2) + reserved(16) = 64 printable hex bytes. */
    n=snprintf(wire,sizeof wire,
        "01%s%08lx%08lx%02x%02x000000000000000000",
        s->epoch,(unsigned long)s->revision,
        (unsigned long)s->last_recover,s->current,
        HD_BREATH_MAX);
    if (n!=64) return -1;
    memcpy(out,wire,65);
    return 0;
}
int hd_breath_record_decode(const char *wire,hd_breath_record *out)
{
    hd_breath_record s;
    char echo[65];
    uint32_t rev,tick,cur,max;
    if(!wire || !out || strlen(wire)!=64 ||
       wire[0]!='0' || wire[1]!='1') return -1;
    memset(&s,0,sizeof s);
    memcpy(s.epoch,wire+2,24);
    s.epoch[24]=0;
    if (!hd_breath_epoch_ok(s.epoch) ||
        hd_breath_read_hex(wire+26,8,&rev) ||
        hd_breath_read_hex(wire+34,8,&tick) ||
        hd_breath_read_hex(wire+42,2,&cur) ||
        hd_breath_read_hex(wire+44,2,&max) ||
        max!=HD_BREATH_MAX)
        return -1;
    s.revision=rev;
    s.last_recover=tick;
    s.current=(unsigned)cur;
    if (!hd_breath_record_valid(&s) ||
        hd_breath_record_encode(&s,echo) ||
        strcmp(echo,wire))
        return -1;
    *out=s;
    return 0;
}
int hd_breath_record_step(const hd_breath_record *expected,
                          hd_breath_record *next,unsigned operation,
                          int wilderness,int resting,uint32_t now)
{
    hd_breath_record updated;
    int value;
    if (!next || !hd_breath_record_valid(expected)) return -1;
    updated=*expected;

    /* A safe retreat to an interior never costs Breath or increments
       revisions. Even a clock failure or exhausted revision space must
       not trap a player inside wilderness. */
    if (operation==HD_BREATH_OP_TRAVEL &&
        !resting && wilderness==0) {
        *next=updated;
        return 0;
    }
    if (expected->revision==UINT32_MAX || !now) return -1;

    if (operation==HD_BREATH_OP_TRAVEL) {
        if (resting || wilderness!=1)
            return -1;
        value=hd_breath_after_move((int)expected->current,1);
    } else if (operation==HD_BREATH_OP_RECOVER) {
        if (wilderness || (resting!=0 && resting!=1) ||
            now<=expected->last_recover)
            return -1;
        value=hd_breath_recover((int)expected->current,resting);
        updated.last_recover=now;
    } else {
        return -1;
    }
    if (value<0) return -1;
    updated.current=(unsigned)value;
    updated.revision++;
    *next=updated;
    return 0;
}
