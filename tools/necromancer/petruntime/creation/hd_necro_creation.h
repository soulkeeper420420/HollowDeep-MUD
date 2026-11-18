#ifndef HD_NECRO_CREATION_H
#define HD_NECRO_CREATION_H

#define HD_NECRO_STR_MIN 8
#define HD_NECRO_STR_MAX 14
#define HD_NECRO_DEX_MIN 9
#define HD_NECRO_DEX_MAX 15
#define HD_NECRO_CON_MIN 10
#define HD_NECRO_CON_MAX 16
#define HD_NECRO_INT_MIN 14
#define HD_NECRO_INT_MAX 18
#define HD_NECRO_PIETY_MIN 14
#define HD_NECRO_PIETY_MAX 18

/* Called once during new character creation, before
   the existing racial attribute adjustment. */
static void hd_necro_creation_stats(
    creature *p, int selected, int (*roll)(int,int))
{
    if(!p || !selected || !roll)
        return;

    p->strength=roll(HD_NECRO_STR_MIN,HD_NECRO_STR_MAX);
    p->dexterity=roll(HD_NECRO_DEX_MIN,HD_NECRO_DEX_MAX);
    p->constitution=roll(HD_NECRO_CON_MIN,HD_NECRO_CON_MAX);
    p->intelligence=roll(HD_NECRO_INT_MIN,HD_NECRO_INT_MAX);
    p->piety=roll(HD_NECRO_PIETY_MIN,HD_NECRO_PIETY_MAX);
}

#endif
