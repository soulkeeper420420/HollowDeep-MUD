/* Compiled at END of private world-identity translation unit; uses private
 * registry[], native_same_room(), durable_location(), no name-based lookup. */
#ifdef HD79_AD_CREATURE_ACTION_PLAYTEST
creature *hd79_ad_native_bound_creature(creature *owner,unsigned id,
        const hd79_mount_roster *roster,const hd79_mount_presence *position)
{
    unsigned i;
    creature *only=NULL;
    if(!durable_location(owner,id,roster,position))return NULL;
    for(i=0;i<HD79_WORLD_BINDINGS;i++) {
        const hd79_native_mount_binding *entry=&registry[i];
        if(entry->owner!=owner||entry->id!=id||!entry->mount)continue;
        if(only || entry->world_room!=owner->parent_rom ||
           entry->room_id!=(unsigned)owner->rom_num ||
           entry->room_id!=position->room[id-1] ||
           entry->species!=(unsigned)roster->entries[id-1].species ||
           strcmp(entry->owner_name,owner->name) ||
           strcmp(entry->epoch,roster->epoch) ||
           !native_same_room(owner,entry->mount,entry->room_id))return NULL;
        only=entry->mount;
    }
    return only;
}
#endif
