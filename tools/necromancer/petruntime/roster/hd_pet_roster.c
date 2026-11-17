#include "hd_pet_roster.h"

#include <string.h>

enum { HEADER_SIZE = 32, PET_SIZE = 28 };

static uint32_t read_uint(const unsigned char *wire, size_t size)
{
    uint32_t value = 0;
    while (size--)
        value = (value << 8) | *wire++;
    return value;
}

static void write_uint(unsigned char *wire, size_t size, uint32_t value)
{
    while (size) {
        wire[--size] = (unsigned char)value;
        value >>= 8;
    }
}

static int valid(const hd_pet_roster *roster)
{
    static const unsigned char zero_epoch[12] = {0};
    uint32_t previous = 0;
    size_t i;

    if (!roster || !roster->revision || !roster->next_id ||
        roster->count > HD_ROSTER_CAP ||
        !memcmp(roster->epoch, zero_epoch, sizeof zero_epoch))
        return 0;

    for (i = 0; i < roster->count; ++i) {
        const hd_roster_pet *pet = &roster->pets[i];
        if (pet->id <= previous || pet->id >= roster->next_id ||
            (!pet->template_id && pet->id != 1) ||
            !pet->level || pet->level > 60 || pet->room >= 16000 || !pet->hpcur ||
            pet->hpcur > pet->hpmax || pet->hpmax > 32767 ||
            pet->mpcur > pet->mpmax || pet->mpmax > 32767 || pet->stay > 1)
            return 0;
        previous = pet->id;
    }
    return 1;
}

int hd_roster_decode(const unsigned char *wire, size_t length, hd_pet_roster *out)
{
    hd_pet_roster roster = {0};
    size_t i;

    if (!wire || !out || length < HEADER_SIZE || memcmp(wire, "HDPR", 4) ||
        read_uint(wire + 4, 4) != 1)
        return -1;
    memcpy(roster.epoch, wire + 8, sizeof roster.epoch);
    roster.revision = read_uint(wire + 20, 4);
    roster.next_id = read_uint(wire + 24, 4);
    roster.count = read_uint(wire + 28, 4);
    if (roster.count > HD_ROSTER_CAP || length != HEADER_SIZE + PET_SIZE * roster.count)
        return -1;

    wire += HEADER_SIZE;
    for (i = 0; i < roster.count; ++i, wire += PET_SIZE) {
        hd_roster_pet *pet = &roster.pets[i];
        if (read_uint(wire + 25, 3))
            return -1;
        pet->id = read_uint(wire, 4);
        pet->template_id = read_uint(wire + 4, 4);
        pet->experience = read_uint(wire + 8, 4);
        pet->level = read_uint(wire + 12, 2);
        pet->room = read_uint(wire + 14, 2);
        pet->hpmax = read_uint(wire + 16, 2);
        pet->hpcur = read_uint(wire + 18, 2);
        pet->mpmax = read_uint(wire + 20, 2);
        pet->mpcur = read_uint(wire + 22, 2);
        pet->stay = wire[24];
    }

    if (!valid(&roster))
        return -1;
    *out = roster;
    return 0;
}

size_t hd_roster_encode(const hd_pet_roster *roster, unsigned char *wire, size_t capacity)
{
    size_t i, length;

    if (!wire || !valid(roster))
        return 0;
    length = HEADER_SIZE + PET_SIZE * roster->count;
    if (capacity < length)
        return 0;

    memset(wire, 0, length);
    memcpy(wire, "HDPR", 4);
    write_uint(wire + 4, 4, 1);
    memcpy(wire + 8, roster->epoch, sizeof roster->epoch);
    write_uint(wire + 20, 4, roster->revision);
    write_uint(wire + 24, 4, roster->next_id);
    write_uint(wire + 28, 4, roster->count);

    wire += HEADER_SIZE;
    for (i = 0; i < roster->count; ++i, wire += PET_SIZE) {
        const hd_roster_pet *pet = &roster->pets[i];
        write_uint(wire, 4, pet->id);
        write_uint(wire + 4, 4, pet->template_id);
        write_uint(wire + 8, 4, pet->experience);
        write_uint(wire + 12, 2, pet->level);
        write_uint(wire + 14, 2, pet->room);
        write_uint(wire + 16, 2, pet->hpmax);
        write_uint(wire + 18, 2, pet->hpcur);
        write_uint(wire + 20, 2, pet->mpmax);
        write_uint(wire + 22, 2, pet->mpcur);
        wire[24] = pet->stay;
    }
    return length;
}

int hd_roster_migrate(const char *legacy_wire, hd_pet_roster *out)
{
    static const char hex[] = "0123456789abcdef";
    unsigned char bytes[32];
    hd_pet_roster roster = {0};
    hd_roster_pet *pet = &roster.pets[0];
    size_t i;

    if (!legacy_wire || !out || strlen(legacy_wire) != 64 ||
        memcmp(legacy_wire, "a74d0001", 8))
        return -1;
    for (i = 0; i < sizeof bytes; ++i) {
        const char *hi = strchr(hex, legacy_wire[i * 2]);
        const char *lo = strchr(hex, legacy_wire[i * 2 + 1]);
        if (!hi || !lo)
            return -1;
        bytes[i] = (unsigned char)(((hi - hex) << 4) | (lo - hex));
    }

    memcpy(roster.epoch, bytes + 4, sizeof roster.epoch);
    roster.revision = read_uint(bytes + 16, 4);
    roster.next_id = 2;
    pet->level = read_uint(bytes + 20, 2);
    pet->room = read_uint(bytes + 22, 2);
    pet->hpmax = read_uint(bytes + 24, 2);
    pet->hpcur = read_uint(bytes + 26, 2);
    pet->mpmax = read_uint(bytes + 28, 2);
    pet->mpcur = read_uint(bytes + 30, 2);
    if (pet->hpcur) {
        pet->id = 1;
        roster.count = 1;
    } else if (pet->level || pet->room || pet->hpmax || pet->mpmax || pet->mpcur) {
        return -1;
    }

    if (!valid(&roster))
        return -1;
    *out = roster;
    return 0;
}

unsigned hd_roster_capacity(unsigned level)
{
    static const unsigned unlocks[] = {7, 14, 20, 27, 34, 40, 47, 54, 60};
    unsigned i = 0;
    if (!level)
        return 0;
    while (i < sizeof unlocks / sizeof unlocks[0] && level >= unlocks[i])
        ++i;
    return 3 + i;
}

unsigned hd_roster_chance(unsigned caster_level, unsigned monster_level)
{
    int64_t chance;

    if (!caster_level || !monster_level)
        return 0;
    chance = 49 + 6 * (int64_t)caster_level - 5 * (int64_t)monster_level;
    if (chance < 10)
        return 10;
    if (chance > 95)
        return 95;
    return (unsigned)chance;
}

uint32_t hd_roster_raise_xp(uint32_t monster_xp)
{
    return monster_xp / 10;
}
