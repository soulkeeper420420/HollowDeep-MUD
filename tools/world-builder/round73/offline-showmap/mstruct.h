#ifndef MOCK_MSTRUCT_H
#define MOCK_MSTRUCT_H
#define RMAX 16000
#define XSECRT 1
#define XINVIS 2
#define PDINVI 4
#define PANSIC 8
#define F_ISSET(p,f) (((p)->flags & (f)) != 0)
typedef struct exit_ { int room; int flags; } exit_;
typedef struct xtag { exit_ *ext; struct xtag *next_tag; } xtag;
typedef struct room { int rom_num; xtag *first_ext; } room;
typedef struct creature { int fd, flags, rom_num; char name[80]; room *parent_rom; } creature;
typedef struct cmd { int num; char fullstr[256]; char str[4][80]; long val[4]; } cmd;
#endif
