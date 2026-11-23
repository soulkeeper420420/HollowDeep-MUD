/* Round79AC2 private native live-creature authority contract.
 * No gameplay commands call this file. NO physical mount is auto-awarded,
 * summoned, spawned, boarded, stabled or revived by this module.
 */
#include "mextern.h"
#include "hd79_mount_world_identity.h"
#include <string.h>

#define HD79_WORLD_BINDINGS 128U
#define HD79_WORLD_TAG_LIMIT 2048U

/* Pointers are ephemeral process-local attestations. Never serialized.
 * Do not trust pointers after deletion: unbind hooks are a future gate.
 */
typedef struct hd79_native_mount_binding {
    creature *owner;
    creature *mount;
    room *world_room;
    unsigned id;
    unsigned species;
    unsigned room_id;
    char owner_name[80];
    char epoch[HD79_MOUNT_EPOCH_CHARS+1U];
} hd79_native_mount_binding;

static hd79_native_mount_binding registry[HD79_WORLD_BINDINGS];

static int terminated_name(const char *name,size_t capacity)
{
    size_t i;
    if (!name || !capacity || !name[0]) return 0;
    for (i=0;i<capacity;i++) if (!name[i]) return 1;
    return 0;
}

/* List membership is identity by actual native pointer, never by monster
 * display name, template ID, player input, or copied key strings.
 * A duplicated or oversized/cyclic room list is denied.
 */
static int exactly_once(const ctag *head,const creature *actor)
{
    const ctag *tag=head;
    unsigned n=0,hits=0;
    while (tag && n<HD79_WORLD_TAG_LIMIT) {
        if (tag->crt==actor) ++hits;
        if (hits>1) return 0;
        tag=tag->next_tag;
        ++n;
    }
    return !tag && hits==1;
}

static int native_same_room(const creature *owner,const creature *mount,
                            unsigned room_id)
{
    const room *world;
    if (!owner || !mount || owner==mount ||
        owner->type!=PLAYER || owner->hpcur<=0 ||
        !owner->parent_rom || owner->rom_num<1 ||
        (unsigned)owner->rom_num!=room_id) return 0;
    world=owner->parent_rom;
    if (world->rom_num!=owner->rom_num ||
        !exactly_once(world->first_ply,owner) ||
        !exactly_once(world->first_mon,mount)) return 0;
    /* We dereference mount only after native list membership is proven. */
    if (mount->type!=MONSTER || mount->hpcur<=0 || mount->hpmax<=0 ||
        mount->parent_rom!=world || mount->rom_num!=owner->rom_num)
        return 0;
    return 1;
}

static int durable_location(const creature *owner,unsigned id,
                            const hd79_mount_roster *roster,
                            const hd79_mount_presence *position)
{
    if (!owner || !roster || !position ||
        !terminated_name(owner->name,sizeof owner->name) ||
        !hd79_presence_valid(roster,position) ||
        !id || id>roster->count ||
        owner->rom_num<1 ||
        (unsigned)owner->rom_num>HD79_PRESENCE_MAX_ROOM ||
        roster->active_id ||
        roster->entries[id-1].stabled ||
        position->room[id-1]!=(unsigned)owner->rom_num)
        return 0;
    return 1;
}

int hd79_world_mount_bind(creature *owner,creature *mount,unsigned id,
                           const hd79_mount_roster *roster,
                           const hd79_mount_presence *position)
{
    unsigned i,slot=HD79_WORLD_BINDINGS;
    hd79_native_mount_binding next;
    if (!durable_location(owner,id,roster,position) ||
        !native_same_room(owner,mount,position->room[id-1])) return 0;
    for (i=0;i<HD79_WORLD_BINDINGS;i++) {
        const hd79_native_mount_binding *p=&registry[i];
        if (!p->mount) { if (slot==HD79_WORLD_BINDINGS) slot=i; continue; }
        if (p->mount==mount || (p->owner==owner && p->id==id) ||
            (p->owner==owner && p->mount==mount)) return 0;
    }
    if (slot==HD79_WORLD_BINDINGS) return 0;
    memset(&next,0,sizeof next);
    next.owner=owner;
    next.mount=mount;
    next.world_room=owner->parent_rom;
    next.id=id;
    next.species=(unsigned)roster->entries[id-1].species;
    next.room_id=(unsigned)owner->rom_num;
    memcpy(next.owner_name,owner->name,strlen(owner->name)+1U);
    memcpy(next.epoch,roster->epoch,sizeof next.epoch);
    registry[slot]=next;
    return 1;
}

int hd79_world_mount_present(creature *owner,unsigned id,
                              const hd79_mount_roster *roster,
                              const hd79_mount_presence *position)
{
    unsigned i;
    if (!durable_location(owner,id,roster,position)) return 0;
    for (i=0;i<HD79_WORLD_BINDINGS;i++) {
        const hd79_native_mount_binding *p=&registry[i];
        if (!p->mount || p->owner!=owner || p->id!=id) continue;
        if (!p->world_room || p->world_room!=owner->parent_rom ||
            p->room_id!=(unsigned)owner->rom_num ||
            p->room_id!=position->room[id-1] ||
            p->species!=(unsigned)roster->entries[id-1].species ||
            strcmp(p->owner_name,owner->name) ||
            strcmp(p->epoch,roster->epoch)) return 0;
        return native_same_room(owner,p->mount,p->room_id);
    }
    return 0;
}

void hd79_world_mount_unbind_creature(const creature *mount)
{
    unsigned i;
    if (!mount) return;
    for (i=0;i<HD79_WORLD_BINDINGS;i++)
        if (registry[i].mount==mount)
            memset(&registry[i],0,sizeof registry[i]);
}

void hd79_world_mount_unbind_owner(const creature *owner)
{
    unsigned i;
    if (!owner) return;
    for (i=0;i<HD79_WORLD_BINDINGS;i++)
        if (registry[i].owner==owner)
            memset(&registry[i],0,sizeof registry[i]);
}
