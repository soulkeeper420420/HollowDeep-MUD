/* Round79AC3D: only ABI metadata; no game logic, I/O or creature allocations. */
#include "hd_player_store.h"
#include "mextern.h"
#include <stddef.h>
#include <stdio.h>
int main(void) {
 printf("HD79_NATIVE_ABI %lu %lu %lu %lu %lu %lu %d\n",
  (unsigned long)sizeof(creature),(unsigned long)offsetof(creature,name),
  (unsigned long)offsetof(creature,type),(unsigned long)offsetof(creature,level),
  (unsigned long)offsetof(creature,hpmax),(unsigned long)offsetof(creature,hpcur),
  MONSTER);
 return 0;
}
