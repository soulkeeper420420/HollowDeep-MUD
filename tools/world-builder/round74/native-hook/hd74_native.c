/* HollowDeep Round 74B: gated native stats and XP PREVIEW.
 * NEVER enables live XP training, remort, inventory rewards or skill grants.
 */
#include "mstruct.h"
#include "hd74_native.h"
#include "hd74_progression.h"
#include <stdint.h>
#include <string.h>

extern void print();

/* Strict, non-destructive input parsing for character creation.
 * Exactly five ASCII decimal values, each 10..18, totaling 70 (50+20).
 * Never call this on existing character saves; racial bonuses happen later.
 */
int hd74_parse_starting_stats(const char *text, int out[5])
{
    const unsigned char *p;
    unsigned value, sum=0, count;
    int tmp[5];
    if (!text || !out) return 0;
    p=(const unsigned char *)text;
    for (count=0;count<5;count++) {
        value=0;
        while (*p==' ' || *p=='\t') p++;
        if (*p<'0' || *p>'9') return 0;
        while (*p>='0' && *p<='9') {
            value=value*10U+(*p-'0');
            if (value>18) return 0;
            p++;
        }
        if (*p && *p!=' ' && *p!='\t') return 0;
        if (value<10) return 0;
        tmp[count]=(int)value;
        sum+=value;
    }
    while (*p==' ' || *p=='\t') p++;
    if (*p || sum!=70) return 0;
    memcpy(out,tmp,sizeof tmp);
    return 1;
}

/* One audited development rule set. NOT a production config loader. */
static const hd74_rules preview_rules={60,1000,50,10,18,20,3,180,2,10};
int hd74_progress(creature *player, cmd *command)
{
    unsigned level, class_id;
    uint32_t next;
    long remaining;
    (void)command;
    if (!player) return 0;
    level=(unsigned char)player->level;
    class_id=(unsigned char)player->class;
    if (class_id<1 || class_id>10 || level<1 || level>100 ||
        player->experience<0 || player->experience>2147483647L ||
        hd74_valid_rules(&preview_rules)) {
        print(player->fd,"Progression preview unavailable for these character values.\n");
        return 0;
    }
    print(player->fd,"HOLLOWDEEP ROUND 74 DEVELOPMENT PREVIEW\n");
    print(player->fd,"Class ID: %u | Current legacy level: %u | Current XP: %ld\n",
          class_id,level,player->experience);
    print(player->fd,"Current stats STR %d DEX %d CON %d INT %d PIE %d\n",
          (int)player->strength,(int)player->dexterity,
          (int)player->constitution,(int)player->intelligence,
          (int)player->piety);
    if (level>=preview_rules.level_cap) {
        print(player->fd,"Preview cap: %u (no next-level threshold).\n",
              (unsigned)preview_rules.level_cap);
    } else if (hd74_exp_threshold(&preview_rules,level+1U,&next)==HD74_OK) {
        remaining=(player->experience<(long)next)?(long)next-player->experience:0;
        print(player->fd,"Proposed XP for level %u: %lu | Missing: %ld\n",
              level+1U,(unsigned long)next,remaining);
    }
    print(player->fd,"Proposed creation: base 10 per stat + 20 allocated points, 18 per-stat cap.\n");
    print(player->fd,"NOT ACTIVE: legacy train/XP, class skills, remort and rewards are unchanged.\n");
    return 0;
}
