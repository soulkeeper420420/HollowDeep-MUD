#include "hd_player_store.h"
#include "mtype.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

void merror(const char *what,int severity)
{
    fprintf(stderr,"Creation probe: %s (%d)\n",what,severity);
    abort();
}

int main(int argc,char **argv)
{
    creature *p=NULL;
    int necro;

    assert(argc==3);
    assert(hd_store_load_player(argv[1],&p)==0);
    assert(p);

    necro=hd_store_is_necromancer(argv[1]);

    assert(necro==atoi(argv[2]));
    assert(p->class==MAGE);
    assert(p->race==HUMAN);
    assert(p->level==1);

    printf("CREATED: identity=%d STR=%d DEX=%d CON=%d INT=%d PIETY=%d ANSI=%d\n",
           necro,p->strength,p->dexterity,p->constitution,
           p->intelligence,p->piety,F_ISSET(p,PANSIC)?1:0);

    if(necro) {
        assert(p->strength>=8 && p->strength<=14);
        assert(p->dexterity>=9 && p->dexterity<=15);
        assert(p->constitution>=11 && p->constitution<=17);
        assert(p->intelligence>=14 && p->intelligence<=18);
        assert(p->piety>=14 && p->piety<=18);
    }

    return 0;
}
