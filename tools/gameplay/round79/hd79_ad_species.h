/* Dedicated private mount definitions. No templates, awards or save ABI edits. */
#ifndef HD79_AD_SPECIES_H
#define HD79_AD_SPECIES_H
#include "hd_mount_travel.h"
typedef struct hd79_ad_species_profile {
    int species;
    const char *name;
    const char *key;
    unsigned level,hp,armor,thaco,dice,sides,plus;
} hd79_ad_species_profile;
const hd79_ad_species_profile *hd79_ad_species_get(int species);
#endif
