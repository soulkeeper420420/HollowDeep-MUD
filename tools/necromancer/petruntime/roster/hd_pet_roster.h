#ifndef HD_PET_ROSTER_H
#define HD_PET_ROSTER_H

#include <stddef.h>
#include <stdint.h>

#define HD_ROSTER_CAP 12
#define HD_ROSTER_NAME_MAX 80
#define HD_ROSTER_WIRE_MAX (32 + (32 + HD_ROSTER_NAME_MAX) * HD_ROSTER_CAP)
#define HD_ROSTER_LEGACY_SKELETON 0

/* Template zero identifies the skeleton preserved from a legacy save. */
typedef struct {
    uint32_t id, template_id, experience;
    uint16_t level, room, hpmax, hpcur, mpmax, mpcur;
    uint8_t stay, unique;
    uint8_t strength, dexterity, constitution, intelligence, piety;
    char name[HD_ROSTER_NAME_MAX];
} hd_roster_pet;

typedef struct {
    uint8_t epoch[12];
    uint32_t revision;
    uint32_t next_id;
    size_t count;
    hd_roster_pet pets[HD_ROSTER_CAP];
} hd_pet_roster;

/* The codec is independent of the outer player snapshot and lock. */
int hd_roster_decode(const unsigned char *wire, size_t length, hd_pet_roster *out);
size_t hd_roster_encode(const hd_pet_roster *roster, unsigned char *wire, size_t capacity);
int hd_roster_migrate(const char *legacy_wire, hd_pet_roster *out);

unsigned hd_roster_capacity(unsigned level);
unsigned hd_roster_chance(unsigned caster_level, unsigned monster_level);
uint32_t hd_roster_raise_xp(uint32_t monster_xp);

#endif
