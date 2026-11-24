/* Round79AD: private native mounts; R1 inert fallback, R5 dedicated definitions
 * only with HD79_AD_SPECIES_PLAYTEST. No public command/login caller.
 * No persistent monster template edits.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_private_fleet.h"
#include "hd79_mount_world_identity.h"
#ifdef HD79_AD_FOUR_STORE_PLAYTEST
#include "hd79_ad_four_store.h"
#endif
#ifdef HD79_AD_SPECIES_PLAYTEST
#include "hd79_ad_species.h"
#endif
#include <stdlib.h>
#include <string.h>

#define HD79_AD_LIST_BOUND 2048U
#ifndef HD79_AD_SPECIES_PLAYTEST
static const char *const hd79_ad_names[6]={
    "HD-private horse", "HD-private warhorse", "HD-private dire wolf",
    "HD-private nightmare", "HD-private griffin", "HD-private dark dragon"
};
#endif

const char *hd79_ad_private_species_name(int species)
{
#ifdef HD79_AD_SPECIES_PLAYTEST
    const hd79_ad_species_profile *definition=hd79_ad_species_get(species);
    return definition ? definition->name : NULL;
#else
    if (species<HD_MOUNT_HORSE || species>HD_MOUNT_DARK_DRAGON)
        return NULL;
    return hd79_ad_names[(unsigned)(species-HD_MOUNT_HORSE)];
#endif
}

int hd79_ad_private_reconnect_allowed(void)
{
    /* A saved room number is NOT proof that a mount survived combat.
     * Never recreate a slain mount using location receipts alone. */
    return 0;
}

static int named(const char *text,size_t n)
{
    size_t i;
    if (!text || !n || !text[0]) return 0;
    for(i=0;i<n;i++) if (!text[i]) return 1;
    return 0;
}
static int once(const ctag *tag,const creature *actor)
{
    unsigned count=0,n=0;
    while (tag && n<HD79_AD_LIST_BOUND) {
        if (tag->crt==actor) ++count;
        if (count>1) return 0;
        tag=tag->next_tag;
        ++n;
    }
    return !tag && count==1;
}
static int native_owner(const creature *owner)
{
    const room *world;
    if (!owner || owner->type!=PLAYER || owner->hpcur<=0 ||
        !named(owner->name,sizeof owner->name) || !owner->parent_rom ||
        owner->rom_num<1 ||
        (unsigned)owner->rom_num>HD79_PRESENCE_MAX_ROOM) return 0;
    world=owner->parent_rom;
    return world->rom_num==owner->rom_num && once(world->first_ply,owner);
}

int hd79_ad_private_spawn(creature *owner,unsigned id,creature **out)
{
    hd79_mount_roster roster;
    hd79_mount_presence presence;
#ifdef HD79_AD_FOUR_STORE_PLAYTEST
    hd79_ad_death_receipt death;
#endif
    const char *title;
    creature *mount;
    int species;
    int result;
    if (!out || !native_owner(owner) || !id ||
        id>HD79_MOUNT_MAX_OWNED) return 0;
#ifdef HD79_AD_FOUR_STORE_PLAYTEST
    /* A populated triple is not survival evidence. Never bypass #83,
     * including from a trusted internal caller or a duplicate spawn. */
    if (hd79_ad_four_store_read(owner->name,&roster,&presence,&death)!=
        HD79_AD_FOUR_OK ||
        !hd79_ad_death_action_eligible(&roster,&death,id)) return 0;
#else
    if (hd79_presence_store_read(owner->name,&roster,&presence)!=
        HD79_PRESENCE_STORE_OK) return 0;
#endif
    if (
        !hd79_presence_valid(&roster,&presence) ||
        id>roster.count || roster.active_id ||
        roster.entries[id-1].stabled ||
        presence.room[id-1]!=(unsigned)owner->rom_num) return 0;
    species=roster.entries[id-1].species;
    title=hd79_ad_private_species_name(species);
    if (!title) return 0;
    if (hd79_world_mount_present(owner,id,&roster,&presence)) return 0;
    mount=(creature *)calloc(1,sizeof *mount);
    if (!mount) return -1;
    if (strlen(title)>=sizeof mount->name) {
        free(mount);
        return -1;
    }
    memcpy(mount->name,title,strlen(title)+1U);
    mount->type=MONSTER;
    mount->level=1;
    mount->hpmax=1;
    mount->hpcur=1;
    mount->mpmax=0;
    mount->mpcur=0;
    mount->fd=-1;
#ifdef HD79_AD_SPECIES_PLAYTEST
    {
        const hd79_ad_species_profile *definition=hd79_ad_species_get(species);
        /* Validated species above; these bounded constants fit native fields. */
        strcpy(mount->key[0],definition->key);
        strcpy(mount->key[1],"mount");
        strcpy(mount->description,"An owned mount watches its surroundings.");
        mount->level=(char)definition->level;
        mount->hpmax=mount->hpcur=(short)definition->hp;
        mount->armor=(char)definition->armor;
        mount->thaco=(char)definition->thaco;
        mount->ndice=(short)definition->dice;
        mount->sdice=(short)definition->sides;
        mount->pdice=(short)definition->plus;
        mount->strength=mount->dexterity=mount->constitution=12;
        mount->intelligence=mount->piety=8;
    }
#endif
    /* calloc keeps carry, flags, spells, follower and inventory pointers zero.
     * Both the inert fallback and dedicated definitions have no loot or XP. */
    if (!native_owner(owner)) {
        free_crt(mount);
        return 0;
    }
    add_crt_rom(mount,owner->parent_rom,0);
    result=hd79_world_mount_bind(owner,mount,id,&roster,&presence);
    if (result!=1) {
        /* Unlink exact native pointer before freeing; accepted AC3B
         * removal hooks invalidate the ephemeral identity token. */
        if (mount->parent_rom)
            del_crt_rom(mount,mount->parent_rom);
        free_crt(mount);
        return -1;
    }
    *out=mount;
    return 1;
}
