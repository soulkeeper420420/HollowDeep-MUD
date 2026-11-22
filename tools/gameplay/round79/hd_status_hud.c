/* Round 79B: legacy Telnet compatible; ANSI is optional.
 * This function does not write any player flags or game state.
 */
#include "hd_status_hud.h"
#include <stdio.h>
#include <string.h>

static int bounded(int value, int maximum)
{
    if (value < 0) return 0;
    if (value > maximum) return maximum;
    return value;
}
static int percent_color(int current, int maximum, int normal)
{
    if (maximum <= 0) return 31;
    if ((long)current * 4L <= maximum) return 31;
    if ((long)current * 2L <= maximum) return 33;
    return normal;
}

int hd_status_hud_format(char *out, size_t capacity,
                         const hd_status_hud_values *values)
{
    char staging[192], hp[32], mp[32], breath[32];
    const char *hp_esc, *mp_esc, *breath_esc, *reset;
    int hp_now, mp_now, breath_now, hp_color, breath_color, used;
    if (!out || !values || capacity == 0 ||
        values->hp_max < 0 || values->mp_max < 0 ||
        values->breath_available < 0 || values->breath_available > 1 ||
        values->ansi_enabled < 0 || values->ansi_enabled > 1 ||
        (values->breath_available && values->breath_max <= 0))
        return -1;

    hp_now = bounded(values->hp_current, values->hp_max);
    mp_now = bounded(values->mp_current, values->mp_max);
    breath_now = values->breath_available ?
                 bounded(values->breath_current, values->breath_max) : 0;

    if (snprintf(hp,sizeof hp,"HP %d/%d",hp_now,values->hp_max) < 0 ||
        snprintf(mp,sizeof mp,"MP %d/%d",mp_now,values->mp_max) < 0)
        return -1;
    if (values->breath_available)
        used=snprintf(breath,sizeof breath,"Breath %d/%d",breath_now,
                      values->breath_max);
    else
        used=snprintf(breath,sizeof breath,"Breath --");
    if (used < 0 || (size_t)used >= sizeof breath)
        return -1;

    if (values->ansi_enabled) {
        hp_color=percent_color(hp_now, values->hp_max, 32);
        breath_color=percent_color(breath_now, values->breath_max, 36);
        hp_esc=hp_color==31 ? "\033[1;31m" :
               hp_color==33 ? "\033[1;33m" : "\033[1;32m";
        mp_esc="\033[1;34m";
        breath_esc=!values->breath_available ? "\033[0;37m" :
                   breath_color==31 ? "\033[1;31m" :
                   breath_color==33 ? "\033[1;33m" : "\033[1;36m";
        reset="\033[0m";
    } else {
        hp_esc=mp_esc=breath_esc=reset="";
    }

    used=snprintf(staging,sizeof staging,
                  "%s%s%s | %s%s%s | %s%s%s",
                  hp_esc,hp,reset,mp_esc,mp,reset,
                  breath_esc,breath,reset);
    if (used < 0 || (size_t)used >= sizeof staging ||
        (size_t)used >= capacity)
        return -1;
    memcpy(out,staging,(size_t)used+1U);
    return used;
}
