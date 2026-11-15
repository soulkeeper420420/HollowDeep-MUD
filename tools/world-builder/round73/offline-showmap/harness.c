/* Offline Round 73F showmap harness: real C source with mock Mordor movement. */
#include "mstruct.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAP_FILE ROOMPATH "/wilderness.map"
extern int hd_wilderness_map(creature *, cmd *);
extern int hd_wilderness_mapradius(creature *, cmd *);
extern int hd_wilderness_showmap(creature *, cmd *);
extern int hd_wilderness_move(creature *, cmd *);
extern int hd_wilderness_go(creature *, cmd *);
static char output[160000];
static size_t length;
static room *destination;
static int movement_return = 0, called_move = 0, called_go = 0;
int print(int fd, const char *fmt, ...) {
    int n; va_list a; (void)fd;
    assert(length < sizeof output);
    va_start(a, fmt); n = vsnprintf(output + length, sizeof output-length, fmt, a);
    va_end(a);
    assert(n >= 0 && (size_t)n < sizeof output-length);
    length += (size_t)n;
    return n;
}
static void reset(void) { length = 0; output[0] = 0; }
int move(creature *p, cmd *c) {
    (void)c; ++called_move;
    if (destination) { p->parent_rom = destination; p->rom_num = destination->rom_num; }
    return movement_return;
}
int go(creature *p, cmd *c) {
    (void)c; ++called_go;
    if (destination) { p->parent_rom = destination; p->rom_num = destination->rom_num; }
    return movement_return;
}
static void run_showmap(creature *p, const char *suffix) {
    cmd c = {0}; c.num=1; strcpy(c.str[0], "showmap");
    snprintf(c.fullstr, sizeof c.fullstr, "%s%s", "showmap", suffix ? suffix : "");
    reset(); hd_wilderness_showmap(p, &c);
}
static void run_radius(creature *p, const char *v) {
    cmd c={0}; c.num=1; strcpy(c.str[0], "mapradius");
    snprintf(c.fullstr, sizeof c.fullstr,"mapradius%s%s",v?" ":"",v?v:"");
    reset(); hd_wilderness_mapradius(p, &c);
}
static void run_map(creature *p) { cmd c={0}; reset(); hd_wilderness_map(p,&c); }
static int occurrence(const char *needle) { int n=0; const char *s=output; while ((s=strstr(s,needle))) { ++n; s+=strlen(needle); } return n; }
static void next_move(creature *p, room *target, int named, int expected_result) {
    cmd c={0}; int actual;
    destination=target; movement_return=expected_result;
    reset(); actual = named ? hd_wilderness_go(p,&c) : hd_wilderness_move(p,&c);
    assert(actual==expected_result);
}
static void make_map(void) {
    FILE *f=fopen(MAP_FILE,"w");assert(f);
    fputs("HDW1\n10001\t1\t1\t#\tCopperreach\tCopper Cairn\n"
          "10002\t2\t1\t=\tCopperreach\t-\n"
          "10003\t3\t1\tF\tCopperreach\t-\n",f);
    assert(fclose(f)==0);
}
int main(void) {
    exit_ e={10002,0}; xtag tag={&e,0};
    room r1={10001,&tag},r2={10002,0},old={14,0};
    creature alice={1,0,10001,"Alice",&r1},bob={2,0,10001,"Bob",&r1};
    make_map();
    run_showmap(&alice," status"); assert(strstr(output,"is off."));
    puts("PASS: showmap defaults off for each session");
    next_move(&alice,&r2,0,3); assert(!strstr(output,"Copperreach ("));
    run_showmap(&alice," on"); assert(strstr(output,"now on"));
    run_showmap(&alice," status"); assert(strstr(output,"is on."));
    puts("PASS: explicit showmap on/status with real command text");
    next_move(&alice,&r1,0,0); assert(occurrence("Copperreach (")==1);
    assert(strstr(output,"column 1, row 1"));
    puts("PASS: successful directional movement auto-renders map exactly once");
    next_move(&alice,0,0,0); assert(!strstr(output,"Copperreach ("));
    puts("PASS: failed/no-op movement never renders map");
    next_move(&alice,&r2,1,7); assert(occurrence("Copperreach (")==1);
    assert(strstr(output,"column 2, row 1"));
    assert(called_move==3 && called_go==1);
    puts("PASS: go/named-exit wrapper preserves return and redraws once");
    next_move(&alice,&old,0,0); assert(!strstr(output,"Copperreach ("));
    puts("PASS: entering old-world rooms suppresses auto redraw");
    run_showmap(&alice," toggle"); assert(strstr(output,"now off"));
    next_move(&alice,&r1,1,0); assert(!strstr(output,"Copperreach ("));
    puts("PASS: toggle off prevents named-exit redraw");
    run_showmap(&alice,0); assert(strstr(output,"now on"));
    puts("PASS: bare showmap toggles on");
    run_radius(&alice,"0"); assert(strstr(output,"Map radius set to 0"));
    next_move(&alice,&r2,1,0); assert(!strstr(output,"Copperreach ("));
    puts("PASS: mapradius zero suppresses automatic redraw");
    run_radius(&alice,"1"); assert(strstr(output,"Map radius set to 1"));
    next_move(&alice,&r1,0,0); assert(occurrence("Copperreach (")==1);
    assert(strstr(output,"Landmark: Copper Cairn"));
    puts("PASS: auto redraw uses active radius and retains landmark");
    run_showmap(&bob," status"); assert(strstr(output,"is off."));
    puts("PASS: showmap session isolation");
    run_showmap(&alice," potato"); assert(strstr(output,"Use showmap"));
    run_showmap(&alice," on extra"); assert(strstr(output,"Use showmap"));
    run_showmap(&alice," status extra"); assert(strstr(output,"Use showmap"));
    run_showmap(&alice," status"); assert(strstr(output,"is on."));
    puts("PASS: invalid showmap arguments never mutate settings");
    {FILE *f=fopen(MAP_FILE,"a");assert(f);fputs("broken row\n",f);fclose(f);}
    next_move(&alice,&r2,1,0); assert(!strstr(output,"No wilderness map") && !strstr(output,"Copperreach ("));
    run_map(&alice); assert(strstr(output,"No wilderness map"));
    puts("PASS: malformed metadata silent on movement but explicit map fails closed");
    remove(MAP_FILE);
    next_move(&alice,&r1,0,0); assert(!strstr(output,"No wilderness map") && !strstr(output,"Copperreach ("));
    puts("PASS: missing sidecar silently suppresses auto map");
    run_showmap(&alice," off"); assert(strstr(output,"now off"));
    puts("ROUND 73F: native showmap control and movement wrapper C tests PASS");
    return 0;
}
