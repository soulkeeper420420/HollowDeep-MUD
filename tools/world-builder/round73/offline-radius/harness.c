#include "mstruct.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAP_FILE ROOMPATH "/wilderness.map"
extern int hd_wilderness_map(creature *p, cmd *c);
extern int hd_wilderness_mapradius(creature *p, cmd *c);
static char output[131072];
static size_t length;
int print(int fd, const char *fmt, ...) {
    int n; va_list a; (void)fd;
    assert(length < sizeof(output));
    va_start(a, fmt); n = vsnprintf(output + length, sizeof(output)-length, fmt, a);
    va_end(a);
    assert(n >= 0 && (size_t)n < sizeof(output)-length);
    length += (size_t)n;
    return n;
}
static void reset(void) { output[0] = '\0'; length = 0; }
/* Mimic the verified legacy parse(): numeric words attach to val[0],
 * str[1] stays empty, and num stays 1. Non-numeric words occupy str[1].
 * The raw fullstr is retained before parsing (see command1.c).
 */
static void run_radius(creature *p, const char *value) {
    cmd c = {0};
    c.num = 1;
    c.val[0] = 1;
    strcpy(c.str[0], "mapradius");
    if (value) {
        assert(strlen(value) < 200);
        snprintf(c.fullstr, sizeof(c.fullstr), "mapradius %s", value);
        if (value[0] >= '0' && value[0] <= '9') {
            c.val[0] = strtol(value, NULL, 10);
        } else if (value[0] == '-' && value[1] >= '0' && value[1] <= '9') {
            c.val[0] = strtol(value, NULL, 10);
        } else {
            c.num = 2;
            strncpy(c.str[1], value, sizeof(c.str[1]) - 1);
        }
    } else {
        strcpy(c.fullstr, "mapradius");
    }
    reset(); hd_wilderness_mapradius(p, &c);
}
static void run_map(creature *p) {
    cmd c = {0}; c.num = 1; reset(); hd_wilderness_map(p, &c);
}
static int rows(void) {
    char *p = strstr(output, "          N\n"), *end;
    int count=0;
    if (!p) return 0;
    p += strlen("          N\n");
    end = strstr(p, "          S\n"); if (!end) return 0;
    while (p < end) { char *nl = strchr(p, '\n'); if (!nl) break; count++; p = nl+1; }
    return count;
}
static void make_sidecar(void) {
    FILE *f = fopen(MAP_FILE, "w"); assert(f);
    fputs("HDW1\n10001\t1\t1\t#\tCopperreach\tCopper Cairn\n"
          "10002\t2\t1\t=\tCopperreach\t-\n"
          "10003\t3\t1\tF\tCopperreach\t-\n", f);
    assert(fclose(f)==0);
}
int main(void) {
    exit_ e={10002,0}; xtag t={&e, NULL}; room r={10001,&t};
    creature alice = {1,0,"Alice",&r}, bob={2,0,"Bob",&r};
    make_sidecar();
    run_radius(&alice, NULL);
    assert(strstr(output, "Map radius is 3") != NULL);
    puts("PASS: Default radius 3");
    run_map(&alice);
    assert(strstr(output,"Copperreach (column 1, row 1)") && strstr(output,"Landmark: Copper Cairn"));
    assert(rows() == 7 && strstr(output,"= ") && strstr(output,"? "));
    puts("PASS: Existing 7x7 map default and fog of war preserved");
    run_radius(&alice, "1"); assert(strstr(output,"Map radius set to 1"));
    run_radius(&alice, NULL); assert(strstr(output,"Map radius is 1"));
    run_map(&alice); assert(rows()==3);
    puts("PASS: Radius 1 displays 3x3");
    run_radius(&alice, "10"); assert(strstr(output,"Map radius set to 10"));
    run_map(&alice); assert(rows()==21);
    puts("PASS: Radius 10 displays 21x21 without revealing hidden tiles");
    run_radius(&alice, "1 2"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "abc"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "10 1"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "11"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "01"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "-1"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, "99999999"); assert(strstr(output, "Use mapradius"));
    run_radius(&alice, NULL); assert(strstr(output,"Map radius is 10"));
    puts("PASS: Invalid and overflowing radii do not mutate settings");
    run_radius(&bob, NULL); assert(strstr(output, "Map radius is 3"));
    puts("PASS: Per-player session radius isolation");
    run_radius(&alice, "0"); assert(strstr(output, "Map radius set to 0 (off)"));
    run_map(&alice); assert(strstr(output, "Wilderness map is off"));
    run_radius(&alice,"3");
    puts("PASS: Radius zero disables map; reenabled at 3");
    alice.flags = PANSIC; run_map(&alice); assert(strstr(output,"\033[33m=\033[0m"));
    puts("PASS: ANSI colors survive adjustable radius");
    { FILE *f = fopen(MAP_FILE,"a"); assert(f); fputs("bad invalid record\n",f); fclose(f); }
    run_map(&alice); assert(strstr(output, "No wilderness map"));
    puts("PASS: Malformed sidecar fails closed");
    remove(MAP_FILE);
    run_map(&alice); assert(strstr(output, "No wilderness map"));
    puts("PASS: Missing wilderness sidecar safe");
    puts("ROUND 73E: adjustable mapradius C tests PASS");
    return 0;
}
