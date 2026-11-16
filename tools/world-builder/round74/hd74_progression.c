#include "hd74_progression.h"
#include <limits.h>
#include <string.h>

#define HD74_MAX_NATIVE_XP UINT32_C(2147483647)
#define HD74_MAGIC "HD74PRG1"
static int bounded_name(const char *s, size_t cap) {
    size_t n=0;
    unsigned char c;
    if(!s || !cap) return 0;
    while(n<cap && s[n]) {
        c=(unsigned char)s[n];
        if(!((c>='a'&&c<='z') || (c>='A'&&c<='Z') ||
             (c>='0'&&c<='9') || c=='_' || c=='-')) return 0;
        n++;
    }
    return n>=3 && n<cap;
}
static int lower_hex32(const char *s) {
    unsigned n;
    if(!s) return 0;
    for(n=0;n<32;n++) {
        unsigned char c=(unsigned char)s[n];
        if(!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return 0;
    }
    return s[32]=='\0';
}
static int calc_xp(const hd74_rules *r, unsigned level, uint32_t *out) {
    uint64_t n, total;
    if(!r || !out || level<1 || level>r->level_cap ||
       r->level_cap<2 || r->level_cap>100) return HD74_DENIED;
    n=(uint64_t)level-1U;
    total=(uint64_t)r->xp_base*n*n+(uint64_t)r->xp_growth*n*n*n;
    if(total>HD74_MAX_NATIVE_XP) return HD74_DENIED;
    *out=(uint32_t)total;
    return HD74_OK;
}
int hd74_valid_rules(const hd74_rules *r) {
    uint32_t high, low;
    if(!r || r->level_cap<2 || r->level_cap>100 ||
       r->xp_base<1 || r->xp_growth<1 || r->stat_base<1 ||
       r->stat_base>r->stat_max || r->stat_max>100 ||
       r->starting_points<1 || r->starting_points>50 ||
       (unsigned)(r->stat_max-r->stat_base)*HD74_STATS<r->starting_points ||
       r->remort_kills<1 || r->remort_kills>HD74_MAX_KILLS ||
       r->remort_seconds<60 || r->remort_seconds>604800 ||
       r->points_per_remort<1 || r->points_per_remort>10 ||
       r->legacy_points_cap<1 || r->legacy_points_cap>100 ||
       calc_xp(r,r->level_cap,&high) ||
       calc_xp(r,r->level_cap-1U,&low) || high<=low)
        return HD74_DENIED;
    return HD74_OK;
}
int hd74_exp_threshold(const hd74_rules *r, unsigned level, uint32_t *out) {
    if(hd74_valid_rules(r)) return HD74_DENIED;
    return calc_xp(r,level,out);
}
int hd74_new_player(const hd74_rules *r, hd74_player *p,
                    const char *owner, unsigned initial_class) {
    unsigned i;
    if(hd74_valid_rules(r) || !p || !bounded_name(owner,80) ||
       initial_class<1 || initial_class>HD74_CLASSES) return HD74_DENIED;
    memset(p,0,sizeof *p);
    strcpy(p->owner,owner);
    p->current_class=(uint8_t)initial_class;
    p->level=1;
    for(i=0;i<HD74_STATS;i++) p->stats[i]=r->stat_base;
    return HD74_OK;
}
int hd74_allocate_stat(const hd74_rules *r, hd74_player *p,
                       unsigned stat, unsigned amount) {
    if(hd74_valid_rules(r) || !p || hd74_validate_player(r,p) ||
       p->stats_finalized || stat>=HD74_STATS || amount<1 ||
       p->spent_stats>r->starting_points ||
       amount>(unsigned)(r->starting_points-p->spent_stats) ||
       p->stats[stat]>r->stat_max || amount>(unsigned)(r->stat_max-p->stats[stat]))
        return HD74_DENIED;
    p->stats[stat]+=(uint8_t)amount;
    p->spent_stats+=(uint8_t)amount;
    return HD74_OK;
}
int hd74_finalize_stats(const hd74_rules *r, hd74_player *p) {
    if(hd74_valid_rules(r)||!p||hd74_validate_player(r,p)||
       p->stats_finalized||p->spent_stats!=r->starting_points)
        return HD74_DENIED;
    p->stats_finalized=1;
    return HD74_OK;
}
int hd74_award_xp(const hd74_rules *r, hd74_player *p, uint32_t delta) {
    uint32_t max, next;
    if(hd74_valid_rules(r) || !p || !p->stats_finalized ||
       hd74_validate_player(r,p) || hd74_exp_threshold(r,r->level_cap,&max))
        return HD74_DENIED;
    if((uint64_t)p->experience+delta>=max) p->experience=max;
    else p->experience+=delta;
    while(p->level<r->level_cap) {
        if(hd74_exp_threshold(r,(unsigned)p->level+1U,&next) ||
           p->experience<next) break;
        p->level++;
    }
    return HD74_OK;
}
int hd74_can_use_skill(const hd74_rules *r, const hd74_player *p,
                       unsigned class_id, unsigned required_level) {
    if(hd74_valid_rules(r)||!p||hd74_validate_player(r,p) ||
       class_id<1 || class_id>HD74_CLASSES ||
       required_level<1 || required_level>r->level_cap ||
       !p->stats_finalized) return 0;
    if(p->current_class==class_id) return p->level>=required_level;
    return !!(p->past_classes & (uint16_t)(1U<<(class_id-1U)));
}
int hd74_begin_remort(const hd74_rules *r, hd74_player *p,
                      const char *id, uint32_t monster, uint64_t now) {
    if(hd74_valid_rules(r)||!p||hd74_validate_player(r,p)||
       p->level!=r->level_cap || p->quest_active ||
       !lower_hex32(id) || monster<1 || monster>999999 ||
       now==0 || now>UINT64_MAX-r->remort_seconds) return HD74_DENIED;
    p->quest_active=1;
    p->quest_kills=0;
    p->quest_started_at=now;
    p->quest_deadline=now+r->remort_seconds;
    p->target_template=monster;
    strcpy(p->quest_id,id);
    memset(p->kill_events,0,sizeof p->kill_events);
    return HD74_OK;
}
int hd74_credit_kill(const hd74_rules *r, hd74_player *p,
                     const char *killer, uint32_t monster,
                     const char *event, uint64_t now) {
    unsigned i;
    if(hd74_valid_rules(r)||!p||hd74_validate_player(r,p)||
       !p->quest_active || !bounded_name(killer,80) ||
       strcmp(p->owner,killer) || monster!=p->target_template ||
       !lower_hex32(event)) return HD74_DENIED;
    if(now>p->quest_deadline) return HD74_EXPIRED;
    if(now<p->quest_started_at) return HD74_DENIED;
    for(i=0;i<p->quest_kills;i++)
        if(!strcmp(p->kill_events[i],event)) return HD74_ALREADY;
    if(p->quest_kills>=r->remort_kills) return HD74_ALREADY;
    strcpy(p->kill_events[p->quest_kills],event);
    p->quest_kills++;
    return HD74_OK;
}
int hd74_finish_remort(const hd74_rules *r, hd74_player *p,
                       unsigned next_class, uint64_t now) {
    unsigned accrued;
    if(hd74_valid_rules(r)||!p||hd74_validate_player(r,p)||
       !p->quest_active || next_class<1 || next_class>HD74_CLASSES ||
       next_class==p->current_class || p->quest_kills!=r->remort_kills ||
       p->remorts==UINT16_MAX) return HD74_DENIED;
    if(now>p->quest_deadline) return HD74_EXPIRED;
    if(now<p->quest_started_at) return HD74_DENIED;
    accrued=(unsigned)p->legacy_points+r->points_per_remort;
    if(accrued>r->legacy_points_cap) accrued=r->legacy_points_cap;
    p->legacy_points=(uint8_t)accrued;
    p->past_classes|=(uint16_t)(1U<<(p->current_class-1U));
    p->current_class=(uint8_t)next_class;
    p->remorts++;
    p->level=1;
    p->experience=0;
    p->quest_active=0;
    p->quest_kills=0;
    p->quest_deadline=0;
    p->quest_started_at=0;
    p->target_template=0;
    memset(p->quest_id,0,sizeof p->quest_id);
    memset(p->kill_events,0,sizeof p->kill_events);
    return HD74_OK;
}
int hd74_buy_legacy(hd74_player *p, const hd74_legacy_request *req) {
    if(!p||!req||!bounded_name(req->owner,80)||
       strcmp(p->owner,req->owner)||req->bind_to_character!=1 ||
       req->point_cost<1 || req->point_cost>p->legacy_points ||
       p->legacy_items==UINT32_MAX ||
       p->legacy_spent>UINT8_MAX-req->point_cost) return HD74_DENIED;
    p->legacy_points-=(uint8_t)req->point_cost;
    p->legacy_spent+=(uint8_t)req->point_cost;
    p->legacy_items++;
    return HD74_OK;
}
int hd74_validate_player(const hd74_rules *r, const hd74_player *p) {
    unsigned i,total=0;
    uint32_t low,high;
    if(hd74_valid_rules(r)||!p||!bounded_name(p->owner,80)||
       p->current_class<1 || p->current_class>HD74_CLASSES ||
       p->level<1 || p->level>r->level_cap ||
       p->spent_stats>r->starting_points || p->stats_finalized>1 ||
       (p->stats_finalized && p->spent_stats!=r->starting_points) ||
       (p->past_classes & ~UINT16_C(1023)) ||
       p->legacy_points>r->legacy_points_cap ||
       p->quest_active>1 || p->quest_kills>r->remort_kills ||
       hd74_exp_threshold(r,p->level,&low) || p->experience<low ||
       hd74_exp_threshold(r,r->level_cap,&high) || p->experience>high)
       return HD74_DENIED;
    if(p->level<r->level_cap) {
        if(hd74_exp_threshold(r,p->level+1U,&high)||p->experience>=high)
            return HD74_DENIED;
    }
    for(i=0;i<HD74_STATS;i++) {
        if(p->stats[i]<r->stat_base||p->stats[i]>r->stat_max) return HD74_DENIED;
        total+=(unsigned)p->stats[i]-r->stat_base;
    }
    if(total!=p->spent_stats) return HD74_DENIED;
    if(p->quest_active) {
        if(!p->stats_finalized || p->level!=r->level_cap ||
           !lower_hex32(p->quest_id) ||
           p->target_template<1 || p->target_template>999999 ||
           p->quest_started_at==0 ||
           p->quest_started_at>UINT64_MAX-r->remort_seconds ||
           p->quest_deadline!=p->quest_started_at+r->remort_seconds)
            return HD74_DENIED;
        for(i=0;i<p->quest_kills;i++) {
            unsigned j;
            if(!lower_hex32(p->kill_events[i])) return HD74_DENIED;
            for(j=0;j<i;j++) if(!strcmp(p->kill_events[i],p->kill_events[j]))
                return HD74_DENIED;
        }
        for(;i<HD74_MAX_KILLS;i++) if(p->kill_events[i][0]) return HD74_DENIED;
    } else {
        if(p->quest_kills || p->quest_started_at || p->quest_deadline ||
           p->target_template || p->quest_id[0]) return HD74_DENIED;
        for(i=0;i<HD74_MAX_KILLS;i++)
            if(p->kill_events[i][0]) return HD74_DENIED;
    }
    return HD74_OK;
}

static void wr16(unsigned char *b,uint16_t v) {
    b[0]=(unsigned char)v;b[1]=(unsigned char)(v>>8);
}
static void wr32(unsigned char *b,uint32_t v) {
    unsigned i;for(i=0;i<4;i++)b[i]=(unsigned char)(v>>(8U*i));
}
static void wr64(unsigned char *b,uint64_t v) {
    unsigned i;for(i=0;i<8;i++)b[i]=(unsigned char)(v>>(8U*i));
}
static uint16_t rd16(const unsigned char *b) {
    return (uint16_t)(b[0]|(uint16_t)b[1]<<8);
}
static uint32_t rd32(const unsigned char *b) {
    unsigned i;uint32_t v=0;for(i=0;i<4;i++)v|=(uint32_t)b[i]<<(8U*i);return v;
}
static uint64_t rd64(const unsigned char *b) {
    unsigned i;uint64_t v=0;for(i=0;i<8;i++)v|=(uint64_t)b[i]<<(8U*i);return v;
}
static uint32_t crc32_wire(const unsigned char *p,size_t len) {
    uint32_t crc=UINT32_C(0xffffffff);
    size_t i;unsigned j;
    for(i=0;i<len;i++) {
        crc^=p[i];
        for(j=0;j<8;j++) crc=(crc>>1)^(UINT32_C(0xedb88320)&(uint32_t)-(int)(crc&1U));
    }
    return ~crc;
}
int hd74_encode(const hd74_rules *r,const hd74_player *p,
                unsigned char out[HD74_WIRE_BYTES]) {
    if(!out||hd74_validate_player(r,p))return HD74_DENIED;
    memset(out,0,HD74_WIRE_BYTES);
    memcpy(out,HD74_MAGIC,8);wr16(out+8,1);
    memcpy(out+10,p->owner,80);
    out[90]=p->current_class;out[91]=p->level;
    wr32(out+92,p->experience);
    memcpy(out+96,p->stats,5);
    out[101]=p->spent_stats;out[102]=p->stats_finalized;
    wr16(out+103,p->past_classes);wr16(out+105,p->remorts);
    out[107]=p->legacy_points;out[108]=p->legacy_spent;
    wr32(out+109,p->legacy_items);wr32(out+113,p->divine_favor);
    out[117]=p->quest_active;out[118]=p->quest_kills;
    wr64(out+119,p->quest_deadline);wr32(out+127,p->target_template);
    memcpy(out+131,p->quest_id,33);
    memcpy(out+164,p->kill_events,sizeof p->kill_events);
    wr64(out+428,p->quest_started_at);
    wr32(out+HD74_WIRE_BYTES-4,crc32_wire(out,HD74_WIRE_BYTES-4));
    return HD74_OK;
}
int hd74_decode(const hd74_rules *r,const unsigned char *raw,
                size_t raw_len,hd74_player *out) {
    hd74_player p;
    unsigned i;
    if(!out||!raw||raw_len!=HD74_WIRE_BYTES ||
       memcmp(raw,HD74_MAGIC,8)||rd16(raw+8)!=1 ||
       rd32(raw+HD74_WIRE_BYTES-4)!=crc32_wire(raw,HD74_WIRE_BYTES-4))
        return HD74_CORRUPT;
    /* Reject unknown non-zero padding until explicit versioned migration. */
    for(i=436;i<HD74_WIRE_BYTES-4;i++)
        if(raw[i]) return HD74_CORRUPT;
    memset(&p,0,sizeof p);
    memcpy(p.owner,raw+10,80);
    p.current_class=raw[90];p.level=raw[91];
    p.experience=rd32(raw+92);
    memcpy(p.stats,raw+96,5);
    p.spent_stats=raw[101];p.stats_finalized=raw[102];
    p.past_classes=rd16(raw+103);p.remorts=rd16(raw+105);
    p.legacy_points=raw[107];p.legacy_spent=raw[108];
    p.legacy_items=rd32(raw+109);p.divine_favor=rd32(raw+113);
    p.quest_active=raw[117];p.quest_kills=raw[118];
    p.quest_deadline=rd64(raw+119);p.target_template=rd32(raw+127);
    memcpy(p.quest_id,raw+131,33);
    memcpy(p.kill_events,raw+164,sizeof p.kill_events);
    p.quest_started_at=rd64(raw+428);
    if(hd74_validate_player(r,&p)) return HD74_CORRUPT;
    *out=p;
    return HD74_OK;
}
