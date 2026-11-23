/* Round79AC3E: private read-only native creature trait offsets. */
#include "hd_player_store.h"
#include "mextern.h"
#include <stddef.h>
#include <stdio.h>
int main(void)
{
    printf("HD79_AC3E %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu\n",
      (unsigned long)sizeof(creature),
      (unsigned long)offsetof(creature,mpmax),
      (unsigned long)offsetof(creature,mpcur),
      (unsigned long)offsetof(creature,ndice),
      (unsigned long)offsetof(creature,sdice),
      (unsigned long)offsetof(creature,pdice),
      (unsigned long)offsetof(creature,flags),
      (unsigned long)sizeof(((creature *)0)->flags),
      (unsigned long)offsetof(creature,spells),
      (unsigned long)sizeof(((creature *)0)->spells),
      (unsigned long)offsetof(creature,carry),
      (unsigned long)sizeof(((creature *)0)->carry));
    return 0;
}
