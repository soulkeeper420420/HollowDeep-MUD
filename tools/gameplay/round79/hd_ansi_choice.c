/* Round 79B: parse an explicit YES/NO color choice at creation. */
#include "hd_ansi_choice.h"
#include <stddef.h>

static int same_folded(const char *text, const char *expected)
{
    size_t i=0;
    unsigned char a,b;
    while ((a=(unsigned char)text[i]) &&
           (b=(unsigned char)expected[i])) {
        if (a>='A' && a<='Z') a=(unsigned char)(a-'A'+'a');
        if (a!=b) return 0;
        i++;
    }
    return !text[i] && !expected[i];
}
int hd_parse_ansi_choice(const char *answer)
{
    if (!answer) return -1;
    if (same_folded(answer,"yes") || same_folded(answer,"y") ||
        same_folded(answer,"on")) return 1;
    if (same_folded(answer,"no") || same_folded(answer,"n") ||
        same_folded(answer,"off")) return 0;
    return -1;
}
