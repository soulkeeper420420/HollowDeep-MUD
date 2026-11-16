/* ELF32-only native ABI compatibility smoke check. */
#include "mstruct.h"
#include "hd74_progression.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    assert(sizeof(long)==4); /* actual 32-bit Mordor player experience */
    assert(sizeof(((creature *)0)->experience)==4);
    assert(sizeof(((creature *)0)->level)==1);
    assert(sizeof(((creature *)0)->class)==1);
    assert(sizeof(((creature *)0)->strength)==1);
    assert(sizeof(((creature *)0)->piety)==1);
    assert(ASSASSIN==1 && FIGHTER==4 && MONK==10);
    assert(HD74_CLASSES==10 && HD74_STATS==5);
    puts("ROUND 74A: native ELF32 Mordor level/XP/stats/class ABI PASS");
    return 0;
}
