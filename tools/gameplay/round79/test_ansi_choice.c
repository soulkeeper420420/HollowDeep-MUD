#include "hd_ansi_choice.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    assert(hd_parse_ansi_choice("Yes")==1);
    assert(hd_parse_ansi_choice("YES")==1);
    assert(hd_parse_ansi_choice("y")==1);
    assert(hd_parse_ansi_choice("ON")==1);
    assert(hd_parse_ansi_choice("No")==0);
    assert(hd_parse_ansi_choice("N")==0);
    assert(hd_parse_ansi_choice("off")==0);
    assert(hd_parse_ansi_choice("maybe")==-1);
    assert(hd_parse_ansi_choice("yes; reboot")==-1);
    assert(hd_parse_ansi_choice("y\033[31m")==-1);
    assert(hd_parse_ansi_choice("")==-1);
    assert(hd_parse_ansi_choice(NULL)==-1);
    puts("ROUND 79B: ANSI CREATION CHOICE RULES PASS");
    puts("NATIVE PANSIC CREATION FLAG: NOT YET INTEGRATED");
    return 0;
}
