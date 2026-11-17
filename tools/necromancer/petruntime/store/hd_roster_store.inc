/* Included by the native player store. Its directory lock protects both
 * migration and checkpoints; ordinary saves carry the trailer through. */
#include "hd_pet_roster.c"
#include "hd74_xp.h"

static int roster_from_record(hd_receipt_set *set, hd_pet_roster *out)
{
    int idx;
    if (set->roster_size)
        return hd_roster_decode(set->roster, set->roster_size, out);
    idx = pet_entry(set);
    return idx < 0 ? HD_PET_ABSENT :
        hd_roster_migrate(set->entries[idx].manifest_sha256, out);
}

int hd_roster_store_read(const char *name, hd_pet_roster *out)
{
    unsigned char *raw;
    hd_receipt_set set;
    size_t size, native;
    int result = HD_PET_ERROR;

    if (!out || !(raw = malloc(HD_RAW_CAPACITY)))
        return result;
    if (!read_record(name, raw, &size, &native, &set) && pet_check_owner(raw, &set))
        result = roster_from_record(&set, out);
    free(raw);
    return result;
}

/* The caller serializes live owner operations and reconciles uncertain writes
 * before acknowledging the raise or updating the in-memory owner. */
static int roster_transaction(const char *name, const hd_pet_roster *expected,
                              const hd_pet_roster *requested, creature *owner,
                              uint32_t monster_xp, long *saved_xp, hd_pet_roster *out)
{
    unsigned char *raw = NULL, *packed = NULL;
    unsigned char expected_wire[HD_ROSTER_WIRE_MAX], old_wire[HD_ROSTER_WIRE_MAX];
    hd_receipt_set set;
    hd_pet_roster old, next;
    creature snapshot;
    otag worn[MAXWEAR];
    size_t size, native, total, expected_size, i, j = 0;
    int idx, length, slot, lock = -1, result = HD_PET_ERROR;

    if (!out || !requested || !valid_name(name))
        return result;
    expected_size = hd_roster_encode(expected, expected_wire, sizeof expected_wire);
    if (!expected_size || !hd_roster_encode(requested, old_wire, sizeof old_wire) ||
        memcmp(expected->epoch, requested->epoch, sizeof expected->epoch) ||
        expected->revision != requested->revision || expected->revision == UINT32_MAX ||
        (!owner && expected->next_id != requested->next_id))
        return result;

    raw = malloc(HD_RAW_CAPACITY);
    packed = malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed)
        goto done;
    lock = open(PLAYERPATH, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (lock < 0 || flock(lock, LOCK_EX) ||
        read_record(name, raw, &size, &native, &set) || !pet_check_owner(raw, &set))
        goto done;
    idx = roster_from_record(&set, &old);
    if (idx == HD_PET_ABSENT ||
        (!idx && (hd_roster_encode(&old, old_wire, sizeof old_wire) != expected_size ||
                  memcmp(old_wire, expected_wire, expected_size)))) {
        result = HD_PET_CONFLICT;
        goto done;
    }
    if (idx)
        goto done;
    if (owner) {
        if (!saved_xp || owner->type != PLAYER || owner->class != MAGE ||
            !native_name(owner->name, name) || owner->level < 1 ||
            owner->level > HD74_LEVEL_CAP || owner->mpcur < 8 ||
            owner->mpcur > owner->mpmax || old.count >= hd_roster_capacity(owner->level) ||
            old.next_id == UINT32_MAX || !requested->pets[old.count].template_id ||
            requested->pets[old.count].room != (unsigned)owner->rom_num)
            goto done;

        snapshot = *owner;
        snapshot.mpcur -= 8;
        snapshot.experience = hd74_xp_add_banked(snapshot.experience,
            hd_roster_raise_xp(monster_xp), snapshot.level, life_remorts(&set));
        for (slot = 0; slot < MAXWEAR; ++slot) {
            if (snapshot.ready[slot]) {
                worn[slot].obj = snapshot.ready[slot];
                worn[slot].next_tag = snapshot.first_obj;
                snapshot.first_obj = &worn[slot];
                snapshot.ready[slot] = NULL;
            }
        }
        if (native_size(&snapshot, &native))
            goto done;
        length = write_crt_to_mem((char *)raw, &snapshot, 0);
        if (length < 0 || (size_t)length != native)
            goto done;
    }
    for (i = 0; i < (owner ? old.count : requested->count); ++i) {
        const hd_roster_pet *pet = &requested->pets[i];
        while (j < old.count && old.pets[j].id < pet->id)
            ++j;
        if (j == old.count || old.pets[j].id != pet->id ||
            old.pets[j].template_id != pet->template_id ||
            old.pets[j].level != pet->level ||
            old.pets[j].unique != pet->unique ||
            strcmp(old.pets[j].name, pet->name) ||
            old.pets[j].strength != pet->strength ||
            old.pets[j].dexterity != pet->dexterity ||
            old.pets[j].constitution != pet->constitution ||
            old.pets[j].intelligence != pet->intelligence ||
            old.pets[j].piety != pet->piety ||
            old.pets[j].hpmax != pet->hpmax || old.pets[j].mpmax != pet->mpmax ||
            old.pets[j].experience > pet->experience)
            goto done;
    }
    next = *requested;
    ++next.revision;
    set.roster_size = hd_roster_encode(&next, set.roster, sizeof set.roster);
    idx = pet_entry(&set);
    if (idx >= 0) {
        --set.count;
        memmove(&set.entries[idx], &set.entries[idx + 1],
                (set.count - (size_t)idx) * sizeof set.entries[0]);
    }
    if (!set.roster_size || hd_receipt_encode(raw, HD_RAW_CAPACITY, native, &set, &total))
        goto done;
    length = hd_compress_bounded((char *)raw, (char *)packed, (int)total,
                                 HD_PLAYER_COMPRESSED_LIMIT);
    if (length < 1 || length > (int)HD_PLAYER_COMPRESSED_LIMIT)
        goto done;
    idx = hd_atomic_player_snapshot(PLAYERPATH, name, packed, (size_t)length);
    if (idx == HD_SNAPSHOT_OK || idx == HD_SNAPSHOT_UNCERTAIN) {
        *out = next;
        if (owner) *saved_xp = snapshot.experience;
        result = idx == HD_SNAPSHOT_OK ? HD_PET_OK : HD_PET_UNCERTAIN;
    }
done:
    if (lock >= 0)
        close(lock);
    free(raw);
    free(packed);
    return result;
}

int hd_roster_store_checkpoint(const char *name, const hd_pet_roster *expected,
                               const hd_pet_roster *requested, hd_pet_roster *out)
{
    return roster_transaction(name, expected, requested, NULL, 0, NULL, out);
}

/* The runtime must supply a fresh eligible corpse after a successful roll.
 * Neither the caller's owner nor the supplied roster is modified. */
int hd_roster_store_raise(const char *name, const hd_pet_roster *expected,
                          const hd_roster_pet *summon, creature *owner,
                          uint32_t monster_xp, long *saved_xp, hd_pet_roster *out)
{
    hd_pet_roster requested;
    hd_roster_pet *pet;
    if (!expected || !summon || !owner || expected->count >= HD_ROSTER_CAP ||
        expected->next_id == UINT32_MAX || summon->id || summon->stay ||
        summon->experience || summon->hpmax != summon->hpcur ||
        summon->mpmax != summon->mpcur)
        return HD_PET_ERROR;
    requested = *expected;
    pet = &requested.pets[requested.count++];
    *pet = *summon;
    pet->id = requested.next_id++;
    return roster_transaction(name, expected, &requested, owner, monster_xp,
                              saved_xp, out);
}
