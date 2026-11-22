/* Round79Z: root-owned world stable registry, no player-save effects. */
#ifndef HD79_STABLE_REGISTRY_H
#define HD79_STABLE_REGISTRY_H
/* 1 = verified stable, 0 = valid registry but room not listed;
 * -1 = unsafe/unreadable/malformed/absent registry.
 * No path comes from a client or gameplay command.
 */
int hd79_stable_registry_check(const char *directory,
                               const char *filename,
                               unsigned room_id);
#endif
