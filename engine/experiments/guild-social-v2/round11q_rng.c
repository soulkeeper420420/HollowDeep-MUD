/* Private replay only. Select native RNG draws without modifying the binary. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>

int rand(void)
{
    int value;
    int (*original)(void) = dlsym(RTLD_NEXT, "rand");
    FILE *fixture = fopen("hollowdeep-data/round11q-rng", "r");
    if (!fixture)
        return original();
    int valid = fscanf(fixture, "%d", &value) == 1 && value >= 0;
    fclose(fixture);
    return valid ? value : original();
}
