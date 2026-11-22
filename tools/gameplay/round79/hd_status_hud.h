/* Round 79B: portable read-only HP/MP/Breath display formatter.
 * Player save format and engine creature ABI remain unchanged.
 */
#ifndef HD_STATUS_HUD_H
#define HD_STATUS_HUD_H
#include <stddef.h>

typedef struct hd_status_hud_values {
    int hp_current;
    int hp_max;
    int mp_current;
    int mp_max;
    int breath_current;
    int breath_max;
    int breath_available; /* 1 only if native engine supplies real breath values */
    int ansi_enabled;     /* saved PANSIC flag in native integration */
} hd_status_hud_values;

/* Returns formatted byte length or -1; no partial output on failure.
 * Unknown breath prints "--", never an invented 100/100 value.
 */
int hd_status_hud_format(char *out, size_t capacity,
                         const hd_status_hud_values *values);
#endif
