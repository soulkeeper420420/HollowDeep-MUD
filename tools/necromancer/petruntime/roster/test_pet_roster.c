#include "hd_pet_roster.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static const char living[] =
    "a74d00010102030405060708090a0b0c00000007000a000200c8009300400033";
static const char tombstone[] =
    "a74d00010102030405060708090a0b0c00000008000000000000000000000000";

static void migration(void)
{
    hd_pet_roster state;

    assert(hd_roster_migrate(living, &state) == 0);
    assert(state.epoch[0] == 1 && state.epoch[11] == 12);
    assert(state.revision == 7 && state.next_id == 2 && state.count == 1);
    assert(state.pets[0].id == 1 && !state.pets[0].template_id);
    assert(state.pets[0].level == 10 && state.pets[0].room == 2);
    assert(state.pets[0].hpmax == 200 && state.pets[0].hpcur == 147);
    assert(state.pets[0].mpmax == 64 && state.pets[0].mpcur == 51);

    assert(hd_roster_migrate(tombstone, &state) == 0);
    assert(state.revision == 8 && state.next_id == 2 && state.count == 0);
    assert(hd_roster_migrate("a74d0001", &state) == -1);
    assert(hd_roster_migrate(
        "a74d00010102030405060708090a0b0c00000008000100000000000000000000",
        &state) == -1);
    assert(hd_roster_migrate(
        "a74d00010102030405060708090a0b0c00000007000a3e8000c8009300400033",
        &state) == -1);
    assert(state.revision == 8 && state.count == 0);
}

static void serialization(void)
{
    hd_pet_roster state, loaded;
    unsigned char wire[HD_ROSTER_WIRE_MAX + 1];
    unsigned char again[HD_ROSTER_WIRE_MAX];
    size_t i, size;

    assert(hd_roster_migrate(living, &state) == 0);
    for (i = 1; i < HD_ROSTER_CAP; ++i) {
        state.pets[i] = state.pets[0];
        state.pets[i].id = state.next_id++;
        state.pets[i].template_id = 201 + i;
        state.pets[i].experience = i * 200;
        state.pets[i].stay = i % 2;
        ++state.count;
    }
    state.pets[11].unique = 1;
    state.pets[11].strength = 30;
    state.pets[11].dexterity = 24;
    state.pets[11].constitution = 26;
    state.pets[11].intelligence = 18;
    state.pets[11].piety = 14;
    strcpy(state.pets[11].name, "crypt rat");
    assert(hd_roster_encode(&state, wire, HD_ROSTER_WIRE_MAX - 1) == 0);
    size = hd_roster_encode(&state, wire, sizeof wire);
    assert(size == HD_ROSTER_WIRE_MAX);
    assert(hd_roster_decode(wire, size, &loaded) == 0);
    assert(loaded.count == 12 && loaded.next_id == 13);
    assert(loaded.pets[11].id == 12 && loaded.pets[11].experience == 2200);
    assert(loaded.pets[11].template_id == 212 && loaded.pets[11].stay);
    assert(loaded.pets[11].unique && !strcmp(loaded.pets[11].name, "crypt rat"));
    assert(loaded.pets[11].strength == 30 && loaded.pets[11].dexterity == 24 &&
           loaded.pets[11].constitution == 26 && loaded.pets[11].intelligence == 18 &&
           loaded.pets[11].piety == 14);
    assert(hd_roster_encode(&loaded, again, sizeof again) == size);
    assert(memcmp(wire, again, size) == 0);
    for (i = 0; i < size; ++i)
        assert(hd_roster_decode(wire, i, &loaded) == -1);
    assert(hd_roster_decode(wire, size + 1, &loaded) == -1);
    wire[7] = 3;
    assert(hd_roster_decode(wire, size, &loaded) == -1);
    wire[7] = 2;
    wire[63] = 1;
    assert(hd_roster_decode(wire, size, &loaded) == -1);
    assert(loaded.count == 12 && loaded.next_id == 13);
    state.pets[2].id = state.pets[1].id;
    assert(hd_roster_encode(&state, wire, sizeof wire) == 0);

    assert(hd_roster_migrate(tombstone, &state) == 0);
    size = hd_roster_encode(&state, wire, sizeof wire);
    assert(size && hd_roster_decode(wire, size, &loaded) == 0);
    assert(loaded.count == 0 && loaded.next_id == 2 && loaded.revision == 8);
}

static void version_one(void)
{
    unsigned char wire[60] = {
        'H', 'D', 'P', 'R', 0, 0, 0, 1,
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
        0, 0, 0, 7, 0, 0, 0, 2, 0, 0, 0, 1,
        0, 0, 0, 1, 0, 0, 0, 23, 0, 0, 0, 0,
        0, 10, 0, 2, 0, 200, 0, 147, 0, 64, 0, 51, 1, 0, 0, 0
    };
    hd_pet_roster roster;
    assert(hd_roster_decode(wire, sizeof wire, &roster) == 0);
    assert(roster.revision == 7 && roster.count == 1);
    assert(roster.pets[0].template_id == 23 && roster.pets[0].hpcur == 147);
    assert(roster.pets[0].stay == 1 && !roster.pets[0].unique && !roster.pets[0].name[0]);
    wire[57] = 1;
    assert(hd_roster_decode(wire, sizeof wire, &roster) == -1);
}

static void balance(void)
{
    static const unsigned unlocks[] = {7, 14, 20, 27, 34, 40, 47, 54, 60};
    unsigned i;
    assert(hd_roster_capacity(0) == 0 && hd_roster_capacity(1) == 3);
    for (i = 0; i < sizeof unlocks / sizeof unlocks[0]; ++i) {
        assert(hd_roster_capacity(unlocks[i] - 1) == i + 3);
        assert(hd_roster_capacity(unlocks[i]) == i + 4);
    }
    assert(hd_roster_chance(10, 5) == 84);
    assert(hd_roster_chance(10, 10) == 59);
    assert(hd_roster_chance(10, 15) == 34);
    assert(hd_roster_chance(1, 60) == 10);
    assert(hd_roster_chance(60, 1) == 95);
    assert(hd_roster_chance(0, 1) == 0);
    assert(hd_roster_raise_xp(9) == 0 && hd_roster_raise_xp(256) == 25);
    assert(hd_roster_raise_xp(UINT32_MAX) == UINT32_MAX / 10);
}

int main(void)
{
    migration();
    serialization();
    version_one();
    balance();
    puts("PASS: roster migration, serialization, and balance");
    return 0;
}
