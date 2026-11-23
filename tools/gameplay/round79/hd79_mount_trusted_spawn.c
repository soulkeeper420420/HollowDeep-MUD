/* Round79AC3C: unexposed native mount creation via verified template IDs.
 * No public command path and NO automatic login/award. Private playtest only.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_mount_trusted_spawn.h"
#include "hd79_mount_world_identity.h"
#include <string.h>

#define HD79_SPAWN_LIST_BOUND 2048U

static int name_bounded(const char *name,unsigned max)
{
    unsigned i;
    if (!name || !max || !name[0]) return 0;
    for(i=0;i<max;i++) if(!name[i]) return 1;
    return 0;
}
static int in_room_once(const ctag *list,const creature *actor)
{
    unsigned n=0,count=0;
    while(list && n<HD79_SPAWN_LIST_BOUND) {
        if(list->crt==actor) ++count;
        if(count>1) return 0;
        list=list->next_tag;
        ++n;
    }
    return !list && count==1;
}
static int catalog_valid(const hd79_trusted_mount_catalog *catalog)
{
    unsigned i,j;
    if(!catalog) return 0;
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++) {
        int value=catalog->native_template_id[i];
        if(value<0 || value>=CMAX) return 0;
        if(!value) continue;
        for(j=0;j<i;j++)
            if(value==catalog->native_template_id[j]) return 0;
    }
    return 1;
}
static int owner_ready(const creature *owner)
{
    const room *world;
    if(!owner || owner->type!=PLAYER || owner->hpcur<=0 ||
       !name_bounded(owner->name,(unsigned)sizeof owner->name) ||
       owner->rom_num<1 || !owner->parent_rom) return 0;
    world=owner->parent_rom;
    if(world->rom_num!=owner->rom_num ||
       !in_room_once(world->first_ply,owner)) return 0;
    return 1;
}
int hd79_mount_spawn_trusted(creature *owner,unsigned mount_id,
                            const hd79_trusted_mount_catalog *catalog,
                            creature **out)
{
    hd79_mount_roster roster;
    hd79_mount_presence location;
    creature *monster=0;
    int species,template_id,rc;
    if(!out || !owner_ready(owner) || !catalog_valid(catalog) ||
       mount_id<1 || mount_id>HD79_MOUNT_MAX_OWNED) return 0;
    rc=hd79_presence_store_read(owner->name,&roster,&location);
    if(rc!=HD79_PRESENCE_STORE_OK ||
       !hd79_presence_valid(&roster,&location) ||
       mount_id>roster.count || roster.active_id ||
       roster.entries[mount_id-1].stabled ||
       location.room[mount_id-1]!=(unsigned)owner->rom_num) return 0;
    species=roster.entries[mount_id-1].species;
    if(species<HD_MOUNT_HORSE || species>HD_MOUNT_DARK_DRAGON)
        return 0;
    template_id=catalog->native_template_id[(unsigned)(species-HD_MOUNT_HORSE)];
    if(template_id<=0 || template_id>=CMAX) return 0;
    /* Already registered in this process: never create a duplicate. */
    if(hd79_world_mount_present(owner,mount_id,&roster,&location)) return 0;
    if(load_crt(template_id,&monster)!=0) return -1;
    if(!monster) return -1;
    if(monster==owner || monster->type!=MONSTER ||
       monster->hpcur<=0 || monster->hpmax<=0 ||
       monster->parent_rom || monster->rom_num ||
       monster->following || monster->first_fol || monster->first_enm) {
        free_crt(monster);
        return 0;
    }
    /* Insertion revalidates the live owner/room after a native template load. */
    if(!owner_ready(owner) ||
       location.room[mount_id-1]!=(unsigned)owner->rom_num) {
        free_crt(monster);
        return 0;
    }
    add_crt_rom(monster,owner->parent_rom,0);
    if(!hd79_world_mount_bind(owner,monster,mount_id,&roster,&location)) {
        /* Native insertion is complete; exact-pointer removal precedes free.
         * The accepted lifecycle hook revokes the binding on removal/free.
         */
        if(monster->parent_rom) del_crt_rom(monster,monster->parent_rom);
        free_crt(monster);
        return -1;
    }
    *out=monster;
    return 1;
}
