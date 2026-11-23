/* Round79AD: six inert native species placeholders in a disposable ELF32 game.
 * Absolutely no command/login caller. No persistent monster template edits.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_private_fleet.h"
#include "hd79_mount_world_identity.h"
#include <stdlib.h>
#include <string.h>

#define HD79_AD_LIST_BOUND 2048U
static const char *const hd79_ad_names[6]={
    "HD-private horse", "HD-private warhorse", "HD-private dire wolf",
    "HD-private nightmare", "HD-private griffin", "HD-private dark dragon"
};

const char *hd79_ad_private_species_name(int species)
{
    if (species<HD_MOUNT_HORSE || species>HD_MOUNT_DARK_DRAGON)
        return NULL;
    return hd79_ad_names[(unsigned)(species-HD_MOUNT_HORSE)];
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
    const char *title;
    creature *mount;
    int species;
    int result;
    if (!out || !native_owner(owner) || !id ||
        id>HD79_MOUNT_MAX_OWNED) return 0;
    if (hd79_presence_store_read(owner->name,&roster,&presence)!=
        HD79_PRESENCE_STORE_OK ||
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
    /* calloc makes carry, flags, spells, combat dice, follower and
     * inventory pointers zero. This test NPC has no attacks, loot or XP. */
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
