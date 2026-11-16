#ifndef HD74_PROGRESSION_H
#define HD74_PROGRESSION_H
/* HollowDeep Round 74A: pure, private, deterministic progression core.
 * No I/O, no MUD command registration, no native player-file writes.
 * 32-bit Mordor ABI: level is a signed char; experience is 32-bit long.
 */
#include <stddef.h>
#include <stdint.h>
#define HD74_CLASSES 10
#define HD74_STATS 5
#define HD74_MAX_KILLS 8
#define HD74_WIRE_BYTES 512
#define HD74_OK 0
#define HD74_ALREADY 1
#define HD74_DENIED (-1)
#define HD74_EXPIRED (-2)
#define HD74_CORRUPT (-3)

typedef struct hd74_rules {
    uint8_t level_cap; /* <=100 and <= native signed-char limit */
    uint16_t xp_base; /* total XP = base*(L-1)^2 + growth*(L-1)^3 */
    uint16_t xp_growth;
    uint8_t stat_base;
    uint8_t stat_max;
    uint8_t starting_points;
    uint8_t remort_kills; /* 1..8 verified native monster deaths */
    uint32_t remort_seconds;
    uint8_t points_per_remort;
    uint8_t legacy_points_cap;
} hd74_rules;

typedef struct hd74_player {
    char owner[80];
    uint8_t current_class; /* Native MUD class numbers 1..10 */
    uint8_t level;
    uint32_t experience;
    uint8_t stats[HD74_STATS]; /* STR, DEX, CON, INT, PIETY */
    uint8_t spent_stats;
    uint8_t stats_finalized;
    uint16_t past_classes; /* class bit (class-1), only after remort */
    uint16_t remorts;
    uint8_t legacy_points;
    uint8_t legacy_spent;
    uint32_t legacy_items; /* purchase count, NOT native objects */
    uint32_t divine_favor; /* separate; no exchange for legacy points */
    uint8_t quest_active;
    uint8_t quest_kills;
    uint64_t quest_started_at;
    uint64_t quest_deadline;
    uint32_t target_template;
    char quest_id[33];
    char kill_events[HD74_MAX_KILLS][33];
} hd74_player;

typedef struct hd74_legacy_request {
    char owner[80];
    uint8_t point_cost;
    uint8_t bind_to_character; /* MUST be 1; never represent No Save */
} hd74_legacy_request;

int hd74_valid_rules(const hd74_rules *rules);
int hd74_exp_threshold(const hd74_rules *rules, unsigned level, uint32_t *out);
int hd74_new_player(const hd74_rules *rules, hd74_player *player,
                    const char *owner, unsigned initial_class);
int hd74_allocate_stat(const hd74_rules *rules, hd74_player *player,
                       unsigned stat, unsigned amount);
int hd74_finalize_stats(const hd74_rules *rules, hd74_player *player);
int hd74_award_xp(const hd74_rules *rules, hd74_player *player, uint32_t delta);
int hd74_can_use_skill(const hd74_rules *rules, const hd74_player *player,
                       unsigned class_id,
                       unsigned required_level);
int hd74_begin_remort(const hd74_rules *rules, hd74_player *player,
                      const char *server_issued_quest_id,
                      uint32_t monster_template, uint64_t now);
int hd74_credit_kill(const hd74_rules *rules, hd74_player *player,
                     const char *trusted_killer, uint32_t monster_template,
                     const char *server_issued_event_id, uint64_t now);
int hd74_finish_remort(const hd74_rules *rules, hd74_player *player,
                       unsigned new_class, uint64_t now);
int hd74_buy_legacy(hd74_player *player, const hd74_legacy_request *request);
int hd74_validate_player(const hd74_rules *rules, const hd74_player *player);
/* Fixed-size LE, CRC-protected in-save trailer. Integrity, NOT authentication.
 * MUST be written inside the same atomic player save, never as a sidecar.
 */
int hd74_encode(const hd74_rules *rules, const hd74_player *player,
                unsigned char out[HD74_WIRE_BYTES]);
int hd74_decode(const hd74_rules *rules, const unsigned char *raw,
                size_t raw_len, hd74_player *out);
#endif
