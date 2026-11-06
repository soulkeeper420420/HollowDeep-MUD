/* Exercise persistent stances using the original engine's actual types. */
#include "mstruct.h"
#include "hollowdeep_stance.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static char output[4000];
static long now = 1700000000L;
static int checks;
long hd_stance_test_now(void) { return now; }
void print(int fd, const char *format, ...)
{
    va_list args;
    size_t used = strlen(output);
    (void)fd;
    va_start(args, format);
    vsnprintf(output + used, sizeof(output) - used, format, args);
    va_end(args);
}
static void contains(const char *text)
{
    if (!strstr(output, text)) { fprintf(stderr, "Expected %s in:\n%s", text, output); exit(1); }
    checks++;
}
static void threshold(creature *attacker, creature *defender, int expected)
{
    int actual = hd_stance_threshold(attacker, defender, 10);
    if (actual != expected) { fprintf(stderr, "Expected threshold %d, received %d\n", expected, actual); exit(1); }
    checks++;
}
static void choose(creature *player, const char *choice)
{
    cmd command;
    memset(&command, 0, sizeof(command));
    command.num = choice ? 2 : 1;
    strcpy(command.str[0], "hstance");
    if (choice) snprintf(command.str[1], sizeof(command.str[1]), "%s", choice);
    output[0] = '\0';
    hstance(player, &command);
}
static void write_raw(const char *path, const char *content)
{
    FILE *file = fopen(path, "w");
    assert(file && fputs(content, file) >= 0 && fclose(file) == 0);
}
static void unchanged(const char *path, const char *expected)
{
    FILE *file = fopen(path, "r");
    char buffer[512] = {0};
    assert(file && fread(buffer, 1, sizeof(buffer)-1, file) == strlen(expected));
    assert(!strcmp(buffer, expected) && fclose(file) == 0); checks++;
}
int main(int argc, char **argv)
{
    creature hero, foe, npc, reload;
    struct stat st;
    const char *path = "hollowdeep-data/hero.stance";
    assert(argc == 2 && chdir(argv[1]) == 0);
    memset(&hero, 0, sizeof(hero));
    strcpy(hero.name, "Hero"); hero.type = PLAYER; hero.class = FIGHTER; hero.level = 1;
    hero.hpcur = 12; hero.hpmax = 24; hero.armor = 90; hero.thaco = 18;
    hero.gold = 123; hero.experience = 456;
    foe = hero; strcpy(foe.name, "Rival");
    npc = foe; npc.type = MONSTER;

    choose(&hero, NULL); contains("Combat stance: balanced");
    threshold(&hero, &foe, 10);
    assert(access("hollowdeep-data", F_OK) != 0); checks++;
    choose(&hero, "missing"); contains("Usage:");
    choose(&hero, "aggressive"); contains("accuracy +1; defense -1");
    threshold(&hero, &foe, 9);
    threshold(&foe, &hero, 9);
    threshold(&npc, &hero, 9);
    threshold(&hero, &npc, 9);
    assert(stat(path, &st) == 0 && (st.st_mode & 0777) == 0600); checks++;
    assert(hero.hpcur == 12 && hero.hpmax == 24 && hero.armor == 90 && hero.thaco == 18 && hero.gold == 123 && hero.experience == 456); checks++;

    choose(&hero, "guarded"); contains("Wait 20 more seconds"); threshold(&hero, &foe, 9);
    now += 19; choose(&hero, "guarded"); contains("Wait 1 more seconds");
    choose(&hero, "aggressive"); contains("Combat stance: aggressive");
    now++; choose(&hero, "guarded"); contains("accuracy -1; defense +1");
    threshold(&hero, &foe, 11); threshold(&foe, &hero, 11);
    reload = hero; threshold(&reload, &foe, 11); /* Load from disk, no process cache. */

    hero.level = 4; threshold(&hero, &foe, 11);
    hero.level = 5; threshold(&hero, &foe, 12);
    hero.level = 9; threshold(&hero, &foe, 12);
    hero.level = 10; threshold(&hero, &foe, 13);
    hero.level = 127; threshold(&hero, &foe, 13);
    hero.level = 0; threshold(&hero, &foe, 10);
    hero.level = -1; threshold(&hero, &foe, 10);
    hero.level = 10;

    now += 20; choose(&foe, "aggressive"); contains("accuracy +1");
    threshold(&hero, &foe, 12); threshold(&foe, &hero, 12);
    npc = hero; npc.type = MONSTER; threshold(&npc, &npc, 10);
    threshold(&npc, &foe, 9);
    npc.type = PLAYER; npc.class = DM; choose(&npc, "aggressive"); contains("ten playable classes");
    threshold(&npc, &npc, 10);
    threshold(NULL, NULL, 10);

    hero.lasttime[LT_ATTCK].ltime = now;
    hero.lasttime[LT_ATTCK].interval = 3;
    choose(&hero, "balanced"); contains("Wait 23 more seconds"); threshold(&hero, &npc, 13);
    now += 23; hero.lasttime[LT_SPELL].ltime = now; hero.lasttime[LT_SPELL].interval = 5;
    choose(&hero, "balanced"); contains("Wait 25 more seconds");
    now += 25; choose(&hero, "balanced"); contains("Combat stance: balanced"); threshold(&hero, &npc, 10);
    now -= 1; choose(&hero, "guarded"); contains("Wait 21 more seconds");
    now += 21;

    reload = hero; strcpy(reload.name, "Abcdefghijklmno");
    choose(&reload, "guarded"); contains("Combat stance: guarded");
    threshold(&reload, &npc, 13);
    strcpy(reload.name, "Abcdefghijklmnopqrs");
    choose(&reload, "aggressive"); contains("Combat stance: aggressive");
    threshold(&reload, &npc, 7);
    assert(stat("hollowdeep-data/abcdefghijklmnopqrs.stance", &st) == 0 && (st.st_mode & 0777) == 0600); checks++;
    strcpy(reload.name, "Abcdefghijklmnopqrst");
    choose(&reload, "aggressive"); contains("could not be read");
    threshold(&reload, &npc, 10);

    write_raw(path, "HOLLOWDEEP_STANCE 1 aggressive 2147483647\n");
    threshold(&hero, &npc, 10); choose(&hero, "guarded"); contains("could not be read");
    unchanged(path, "HOLLOWDEEP_STANCE 1 aggressive 2147483647\n");
    write_raw(path, "HOLLOWDEEP_STANCE 1 aggressive 0 extra\n"); threshold(&hero, &npc, 10);
    choose(&hero, "balanced"); contains("could not be read");
    unchanged(path, "HOLLOWDEEP_STANCE 1 aggressive 0 extra\n");
    write_raw(path, "HOLLOWDEEP_STANCE 1 berserk 0\n"); threshold(&hero, &npc, 10);
    write_raw(path, "HOLLOWDEEP_STANCE 2 aggressive 0\n"); threshold(&hero, &npc, 10);
    write_raw(path, "HOLLOWDEEP_STANCE 1 aggressive -1\n"); threshold(&hero, &npc, 10);
    assert(unlink(path) == 0);

    write_raw("outside", "unchanged"); assert(symlink("../outside", path) == 0);
    threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read"); unchanged("outside", "unchanged");
    assert(unlink(path) == 0 && mkfifo(path, 0600) == 0);
    threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read");
    assert(unlink(path) == 0 && mkdir(path, 0700) == 0);
    threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read");
    assert(rmdir(path) == 0);
    strcpy(hero.name, "../outside"); threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read");
    memset(hero.name, 'A', sizeof(hero.name)); threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read");
    strcpy(hero.name, "Hero");
    assert(rename("hollowdeep-data", "data-backup") == 0 && symlink("data-backup", "hollowdeep-data") == 0);
    threshold(&hero, &npc, 10); choose(&hero, "aggressive"); contains("could not be read");
    assert(unlink("hollowdeep-data") == 0 && rename("data-backup", "hollowdeep-data") == 0);
    now = 2147483640L; choose(&hero, "aggressive"); contains("clock cannot safely");
    printf("%d stance behavior checks passed.\n", checks);
    return 0;
}
