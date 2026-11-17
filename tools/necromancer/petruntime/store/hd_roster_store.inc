/* Included by the native player store. Its directory lock protects both
 * migration and checkpoints; ordinary saves carry the trailer through. */
#include "hd_pet_roster.c"

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

/* Save an unchanged migration, checkpoint, or removal. A future raise
 * transaction must handle additions with the native mana and XP write. */
int hd_roster_store_checkpoint(const char *name, const hd_pet_roster *expected,
                               const hd_pet_roster *requested, hd_pet_roster *out)
{
    unsigned char *raw = NULL, *packed = NULL;
    unsigned char expected_wire[HD_ROSTER_WIRE_MAX], old_wire[HD_ROSTER_WIRE_MAX];
    hd_receipt_set set;
    hd_pet_roster old, next;
    size_t size, native, total, expected_size, i, j = 0;
    int idx, length, lock = -1, result = HD_PET_ERROR;

    if (!out || !requested || !valid_name(name))
        return result;
    expected_size = hd_roster_encode(expected, expected_wire, sizeof expected_wire);
    if (!expected_size || !hd_roster_encode(requested, old_wire, sizeof old_wire) ||
        memcmp(expected->epoch, requested->epoch, sizeof expected->epoch) ||
        expected->revision != requested->revision || expected->revision == UINT32_MAX ||
        expected->next_id != requested->next_id)
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
    for (i = 0; i < requested->count; ++i) {
        const hd_roster_pet *pet = &requested->pets[i];
        while (j < old.count && old.pets[j].id < pet->id)
            ++j;
        if (j == old.count || old.pets[j].id != pet->id ||
            old.pets[j].template_id != pet->template_id ||
            old.pets[j].level != pet->level ||
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
        result = idx == HD_SNAPSHOT_OK ? HD_PET_OK : HD_PET_UNCERTAIN;
    }
done:
    if (lock >= 0)
        close(lock);
    free(raw);
    free(packed);
    return result;
}
