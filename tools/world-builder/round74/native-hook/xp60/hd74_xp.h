#ifndef HD74_XP_H
#define HD74_XP_H
/* Private Round 74B: signed ELF32-safe XP migration, no ABI changes. */
#define HD74_LEVEL_CAP 60
#define HD74_XP_MAX 2147483647L
/* Level 1 starts at 0 XP. At cap, no further training is allowed. */
long hd74_xp_for_level(int level);
long hd74_xp_for_next(int current_level);
int hd74_level_from_xp(long xp);
long hd74_xp_add_bounded(long current, long delta);
#endif
