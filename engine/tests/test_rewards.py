#!/usr/bin/env python3
"""Execute the prepared engine's actual monster reward blocks with test actors."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
parser.add_argument('--runner')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
native = (args.source / 'creature.c').read_text(encoding='latin-1')
death = native[native.index('void die('):]
begin = death.index('        ep = crt_ptr->first_enm;')
end = death.index('if(!F_ISSET(crt_ptr, MTRADE))', begin)
xp = death[begin:end]
begin = death.index('        if(crt_ptr->gold) {')
end = death.index('if(F_ISSET(crt_ptr, MDMFOL)', begin)
gold = death[begin:end]
assert xp.count('hd_bonus_xp(') == 1 and gold.count('hd_bonus_gold(') == 1
fixture = r'''
#include "mstruct.h"
#include "hollowdeep_bonus.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
static creature hero, friend;
static object coins;
static long clock_now = 1800000000L;
long hd_staff_test_now(void) { return clock_now; }
void print(int fd, const char *format, ...) { (void)fd; (void)format; }
void broadcast(const char *format, ...) { (void)format; }
void disconnect(int fd) { (void)fd; }
void output_buf(void) {}
creature *find_who(char *name) { return !strcmp(name, "Hero") ? &hero : &friend; }
int load_obj(int id, object **result) { (void)id; memset(&coins, 0, sizeof(coins)); *result = &coins; return 0; }
void add_obj_rom(object *item, room *where) { (void)where; assert(item == &coins); }
static void kill_rewards(creature *crt_ptr) {
    etag *ep;
    creature *ply_ptr;
    object *obj_ptr;
    int levels = 0, expdiv = 0, i = 0;
    char str[2048] = "";
/*ACTUAL_XP*/
/*ACTUAL_GOLD*/
}
int main(int argc, char **argv) {
    creature monster;
    etag first, second;
    FILE *file;
    (void)argc;
    assert(!chdir(argv[1])); assert(!mkdir("hollowdeep-data", 0700));
    file = fopen("hollowdeep-data/bonus.db", "w"); assert(file);
    fputs("HOLLOWDEEP_BONUS 1 2 3 1800000060 3\n", file); fclose(file);
    memset(&monster, 0, sizeof(monster)); memset(&first, 0, sizeof(first)); memset(&second, 0, sizeof(second));
    hero.level = friend.level = 1; hero.experience = 1000;
    monster.experience = 100; monster.hpmax = 100; monster.gold = 10;
    strcpy(first.enemy, "Hero"); first.damage = 25; first.next_tag = &second;
    strcpy(second.enemy, "Friend"); second.damage = 75; monster.first_enm = &first;
    kill_rewards(&monster);
    assert(hero.experience == 1050 && friend.experience == 150);
    assert(coins.value == 30 && !strcmp(coins.name, "30 gold coins"));
    assert(monster.experience == 100 && monster.gold == 10);
    clock_now += 60;
    kill_rewards(&monster);
    assert(hero.experience == 1075 && friend.experience == 225 && coins.value == 10);
    file = fopen("hollowdeep-data/bonus.db", "w"); assert(file);
    fputs("HOLLOWDEEP_BONUS 1 20 20 1800000120 3\n", file); fclose(file);
    kill_rewards(&monster);
    assert(hero.experience == 1575 && friend.experience == 1725 && coins.value == 200);
    hero.experience = 2147483640L; monster.gold = 2147483640L;
    kill_rewards(&monster);
    assert(hero.experience == 2147483647L && coins.value == 2147483647L);
    assert(!strcmp(coins.name, "2147483647 gold coins"));
    puts("PASS: actual native monster rewards, contribution splits, 20x limits, overflow clamps and exact event expiry");
    return 0;
}
'''.replace('/*ACTUAL_XP*/', xp).replace('/*ACTUAL_GOLD*/', gold)
with tempfile.TemporaryDirectory(prefix='hollowdeep-native-rewards-') as temporary:
    work = Path(temporary)
    source = work / 'native_rewards.c'
    source.write_text(fixture)
    executable = work / 'native-rewards'
    subprocess.run([args.cc, '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-DHOLLOWDEEP_STAFF_TEST_TIME', '-I', str(args.source.resolve()),
                    '-I', str(root / 'extensions'), str(source),
                    str(root / 'extensions/hollowdeep_staff.c'),
                    str(root / 'extensions/hollowdeep_bonus.c'), '-o', str(executable)], check=True)
    subprocess.run(([args.runner] if args.runner else []) + [str(executable), temporary], check=True, timeout=20)
