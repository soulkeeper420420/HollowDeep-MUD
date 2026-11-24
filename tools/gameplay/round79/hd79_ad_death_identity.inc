/* R4: compiled at the END of the private native world identity translation
 * unit: registry[] is intentionally private to this module. A naked pointer,
 * name or template match can NEVER create authority. No persistence here.
 */
#ifdef HD79_AD_COMBAT_DEATH_PLAYTEST
int hd79_ad_death_identity(creature *dead,creature **out_owner,
                            unsigned *out_id,char out_epoch[25])
{
    unsigned i;
    if (!dead || !out_owner || !out_id || !out_epoch ||
        dead->type!=MONSTER || dead->hpcur>0)
        return 0;
    for(i=0;i<HD79_WORLD_BINDINGS;i++) {
        const hd79_native_mount_binding *entry=&registry[i];
        creature *owner;
        room *world;
        if(entry->mount!=dead) continue;
        owner=entry->owner;
        world=entry->world_room;
        /* Check membership by exact pointer before reading stale actors.
         * AC3B invalidation clears these bindings on remove/free/unload. */
        if(!owner || !world || !entry->id ||
           entry->id>HD79_MOUNT_MAX_OWNED ||
           !exactly_once(world->first_mon,dead) ||
           !exactly_once(world->first_ply,owner))return 0;
        if(owner->type!=PLAYER ||
           owner->parent_rom!=world ||
           owner->rom_num!=world->rom_num ||
           (unsigned)owner->rom_num!=entry->room_id ||
           !terminated_name(owner->name,sizeof owner->name) ||
           strcmp(owner->name,entry->owner_name) ||
           dead->type!=MONSTER || dead->hpcur>0 ||
           dead->parent_rom!=world ||
           dead->rom_num!=world->rom_num)return 0;
        *out_owner=owner;
        *out_id=entry->id;
        memcpy(out_epoch,entry->epoch,HD79_MOUNT_EPOCH_CHARS+1U);
        return 1;
    }
    return 0;
}
#endif
