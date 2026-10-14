#include <stdint.h>
int specialized(uint64_t limit, int *first, uint64_t *counts) {
uint64_t visits = 0; unsigned char used[4096] = {0};
counts[0] = counts[1] = counts[2] = 0;
static const int d0[] = {84,70,79,110,92,69,111,62};
static const int d1[] = {92,70,111,110,79,69,84,62};
static const int d2[] = {84,70,133,111,113,122,140,69,92,105,110,82,152,79};
static const int d3[] = {140,92,82,113,105,152,62,122,133,110,79,116,70,111};
static const int d4[] = {152,122,79,82,105,70,133,92,69,110,111,84,140,113,165};
static const int d5[] = {140,165,122,133,111,105,82,113,84,69,70,79,152,92,110};
static const int d6[] = {105,111,84,62,113,69,140,79,133,122,92,82,152,110,70,116};
static const int d7[] = {92,181,185,122,196,165,140,133,170,113,116,105,203,110,152,111};
static const int d8[] = {122,170,105,196,116,111,92,133,113,152,110,203,181,185,165,140};
static const int d9[] = {113,69,70,111,82,84,110,140,105,152,116,79,62,92,122,133};
static const int d10[] = {133,79,185,165,122,62,181,92,113,116,170,111,152,84,203,105,110,196,140,70};
static const int d11[] = {170,70,84,152,105,92,133,140,62,181,113,165,79,110,196,203,116,111,185,122};
static const int d12[] = {110,122,116,152,165,92,105,185,203,70,111,113,170,84,140,133,196,79,62,181};
static const int d13[] = {152,79,69,111,196,70,122,185,113,82,133,110,105,84,165,116,203,140,92,170,181};
static const int d14[] = {113,84,181,133,69,203,111,79,70,105,116,122,196,165,92,170,152,110,140,185,82};
static const int d15[] = {69,181,82,111,203,165,79,116,152,133,185,170,70,196,113,122,105,92,110,140,84};
static const int d16[] = {113,84,181,82,185,92,69,105,116,140,70,203,111,165,122,79,196,133,152,170,110,62};
static const int d17[] = {133,110,196,105,185,152,62,116,140,79,170,181,82,165,92,122,113,111,203,69,84,70};
static const int d18[] = {152,70,122,140,133,203,92,111,196,113,105,84,116,69,165,110,170,82,79,181,185,62};
static const int d19[] = {113,62,111,196,203,170,110,181,122,133,70,152,69,84,79,116,92,82,140,185,165,105};
static const int d20[] = {203,70,122,62,181,165,92,152,133,113,111,110,170,105,196,185,84,69,79,82,116,140};
static const int d21[] = {62,113,79,203,92,84,181,170,140,122,111,69,116,133,70,185,165,110,82,196,105,152};
for (int p0=0; p0<8; ++p0) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x0=d0[p0];
if (used[x0]) continue;
if (!(((1LL * x0)) + (62LL) <= (154LL) && ((1LL * x0)) + (111LL) >= (154LL))) continue;
if (!(((1LL * x0)) + (246LL) <= (539LL) && ((1LL * x0)) + (558LL) >= (539LL))) continue;
used[x0] = 1;
for (int p1=0; p1<8; ++p1) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x1=d1[p1];
if (used[x1]) continue;
if (!(((1LL * x0) + (1LL * x1)) + (0LL) <= (154LL) && ((1LL * x0) + (1LL * x1)) + (0LL) >= (154LL))) continue;
if (!(((1LL * x1)) + (186LL) <= (475LL) && ((1LL * x1)) + (609LL) >= (475LL))) continue;
used[x1] = 1;
for (int p2=0; p2<14; ++p2) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x2=d2[p2];
if (used[x2]) continue;
if (!(((1LL * x2)) + (186LL) <= (362LL) && ((1LL * x2)) + (456LL) >= (362LL))) continue;
if (!(((1LL * x2)) + (138LL) <= (304LL) && ((1LL * x2)) + (330LL) >= (304LL))) continue;
used[x2] = 1;
for (int p3=0; p3<14; ++p3) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x3=d3[p3];
if (used[x3]) continue;
if (!(((1LL * x3) + (1LL * x2)) + (124LL) <= (362LL) && ((1LL * x3) + (1LL * x2)) + (304LL) >= (362LL))) continue;
if (!(((1LL * x0) + (1LL * x3)) + (184LL) <= (539LL) && ((1LL * x0) + (1LL * x3)) + (406LL) >= (539LL))) continue;
used[x3] = 1;
for (int p4=0; p4<15; ++p4) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x4=d4[p4];
if (used[x4]) continue;
if (!(((1LL * x4)) + (193LL) <= (483LL) && ((1LL * x4)) + (609LL) >= (483LL))) continue;
if (!(((1LL * x4) + (1LL * x2)) + (69LL) <= (304LL) && ((1LL * x4) + (1LL * x2)) + (165LL) >= (304LL))) continue;
used[x4] = 1;
for (int p5=0; p5<15; ++p5) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x5=d5[p5];
if (used[x5]) continue;
if (!(((1LL * x5)) + (193LL) <= (524LL) && ((1LL * x5)) + (609LL) >= (524LL))) continue;
if (!(((1LL * x4) + (1LL * x5) + (1LL * x2)) + (0LL) <= (304LL) && ((1LL * x4) + (1LL * x5) + (1LL * x2)) + (0LL) >= (304LL))) continue;
used[x5] = 1;
for (int p6=0; p6<16; ++p6) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x6=d6[p6];
if (used[x6]) continue;
if (!(((1LL * x3) + (1LL * x2) + (1LL * x6)) + (62LL) <= (362LL) && ((1LL * x3) + (1LL * x2) + (1LL * x6)) + (152LL) >= (362LL))) continue;
if (!(((1LL * x6)) + (186LL) <= (460LL) && ((1LL * x6)) + (609LL) >= (460LL))) continue;
used[x6] = 1;
for (int p7=0; p7<16; ++p7) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x7=d7[p7];
if (used[x7]) continue;
if (!(((1LL * x7)) + (193LL) <= (598LL) && ((1LL * x7)) + (609LL) >= (598LL))) continue;
if (!(((1LL * x7) + (1LL * x0) + (1LL * x3)) + (92LL) <= (539LL) && ((1LL * x7) + (1LL * x0) + (1LL * x3)) + (203LL) >= (539LL))) continue;
used[x7] = 1;
for (int p8=0; p8<16; ++p8) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x8=d8[p8];
if (used[x8]) continue;
if (!(((1LL * x8)) + (186LL) <= (619LL) && ((1LL * x8)) + (609LL) >= (619LL))) continue;
if (!(((1LL * x7) + (1LL * x8) + (1LL * x0) + (1LL * x3)) + (0LL) <= (539LL) && ((1LL * x7) + (1LL * x8) + (1LL * x0) + (1LL * x3)) + (0LL) >= (539LL))) continue;
used[x8] = 1;
for (int p9=0; p9<16; ++p9) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x9=d9[p9];
if (used[x9]) continue;
if (!(((1LL * x3) + (1LL * x9) + (1LL * x2) + (1LL * x6)) + (0LL) <= (362LL) && ((1LL * x3) + (1LL * x9) + (1LL * x2) + (1LL * x6)) + (0LL) >= (362LL))) continue;
if (!(((1LL * x9)) + (186LL) <= (533LL) && ((1LL * x9)) + (609LL) >= (533LL))) continue;
used[x9] = 1;
for (int p10=0; p10<20; ++p10) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x10=d10[p10];
if (used[x10]) continue;
if (!(((1LL * x8) + (1LL * x10)) + (124LL) <= (619LL) && ((1LL * x8) + (1LL * x10)) + (406LL) >= (619LL))) continue;
if (!(((1LL * x10) + (1LL * x9)) + (124LL) <= (533LL) && ((1LL * x10) + (1LL * x9)) + (406LL) >= (533LL))) continue;
used[x10] = 1;
for (int p11=0; p11<20; ++p11) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x11=d11[p11];
if (used[x11]) continue;
if (!(((1LL * x8) + (1LL * x10) + (1LL * x11)) + (62LL) <= (619LL) && ((1LL * x8) + (1LL * x10) + (1LL * x11)) + (203LL) >= (619LL))) continue;
if (!(((1LL * x11) + (1LL * x6)) + (124LL) <= (460LL) && ((1LL * x11) + (1LL * x6)) + (406LL) >= (460LL))) continue;
used[x11] = 1;
for (int p12=0; p12<20; ++p12) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x12=d12[p12];
if (used[x12]) continue;
if (!(((1LL * x8) + (1LL * x10) + (1LL * x12) + (1LL * x11)) + (0LL) <= (619LL) && ((1LL * x8) + (1LL * x10) + (1LL * x12) + (1LL * x11)) + (0LL) >= (619LL))) continue;
if (!(((1LL * x12) + (1LL * x1)) + (124LL) <= (475LL) && ((1LL * x12) + (1LL * x1)) + (406LL) >= (475LL))) continue;
used[x12] = 1;
for (int p13=0; p13<21; ++p13) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x13=d13[p13];
if (used[x13]) continue;
if (!(((1LL * x13) + (1LL * x5)) + (124LL) <= (524LL) && ((1LL * x13) + (1LL * x5)) + (406LL) >= (524LL))) continue;
if (!(((1LL * x13)) + (138LL) <= (429LL) && ((1LL * x13)) + (406LL) >= (429LL))) continue;
used[x13] = 1;
for (int p14=0; p14<21; ++p14) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x14=d14[p14];
if (used[x14]) continue;
if (!(((1LL * x7) + (1LL * x14)) + (124LL) <= (598LL) && ((1LL * x7) + (1LL * x14)) + (406LL) >= (598LL))) continue;
if (!(((1LL * x14) + (1LL * x13)) + (69LL) <= (429LL) && ((1LL * x14) + (1LL * x13)) + (203LL) >= (429LL))) continue;
used[x14] = 1;
for (int p15=0; p15<21; ++p15) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x15=d15[p15];
if (used[x15]) continue;
if (!(((1LL * x15) + (1LL * x4)) + (124LL) <= (483LL) && ((1LL * x15) + (1LL * x4)) + (406LL) >= (483LL))) continue;
if (!(((1LL * x14) + (1LL * x15) + (1LL * x13)) + (0LL) <= (429LL) && ((1LL * x14) + (1LL * x15) + (1LL * x13)) + (0LL) >= (429LL))) continue;
used[x15] = 1;
for (int p16=0; p16<22; ++p16) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x16=d16[p16];
if (used[x16]) continue;
if (!(((1LL * x13) + (1LL * x5) + (1LL * x16)) + (62LL) <= (524LL) && ((1LL * x13) + (1LL * x5) + (1LL * x16)) + (203LL) >= (524LL))) continue;
if (!(((1LL * x11) + (1LL * x16) + (1LL * x6)) + (62LL) <= (460LL) && ((1LL * x11) + (1LL * x16) + (1LL * x6)) + (203LL) >= (460LL))) continue;
used[x16] = 1;
for (int p17=0; p17<22; ++p17) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x17=d17[p17];
if (used[x17]) continue;
if (!(((1LL * x7) + (1LL * x14) + (1LL * x17)) + (62LL) <= (598LL) && ((1LL * x7) + (1LL * x14) + (1LL * x17)) + (203LL) >= (598LL))) continue;
if (!(((1LL * x17) + (1LL * x11) + (1LL * x16) + (1LL * x6)) + (0LL) <= (460LL) && ((1LL * x17) + (1LL * x11) + (1LL * x16) + (1LL * x6)) + (0LL) >= (460LL))) continue;
used[x17] = 1;
for (int p18=0; p18<22; ++p18) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x18=d18[p18];
if (used[x18]) continue;
if (!(((1LL * x7) + (1LL * x14) + (1LL * x18) + (1LL * x17)) + (0LL) <= (598LL) && ((1LL * x7) + (1LL * x14) + (1LL * x18) + (1LL * x17)) + (0LL) >= (598LL))) continue;
if (!(((1LL * x18) + (1LL * x12) + (1LL * x1)) + (62LL) <= (475LL) && ((1LL * x18) + (1LL * x12) + (1LL * x1)) + (203LL) >= (475LL))) continue;
used[x18] = 1;
for (int p19=0; p19<22; ++p19) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x19=d19[p19];
if (used[x19]) continue;
if (!(((1LL * x19) + (1LL * x15) + (1LL * x4)) + (62LL) <= (483LL) && ((1LL * x19) + (1LL * x15) + (1LL * x4)) + (203LL) >= (483LL))) continue;
if (!(((1LL * x19) + (1LL * x10) + (1LL * x9)) + (62LL) <= (533LL) && ((1LL * x19) + (1LL * x10) + (1LL * x9)) + (203LL) >= (533LL))) continue;
used[x19] = 1;
for (int p20=0; p20<22; ++p20) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x20=d20[p20];
if (used[x20]) continue;
if (!(((1LL * x19) + (1LL * x15) + (1LL * x4) + (1LL * x20)) + (0LL) <= (483LL) && ((1LL * x19) + (1LL * x15) + (1LL * x4) + (1LL * x20)) + (0LL) >= (483LL))) continue;
if (!(((1LL * x18) + (1LL * x20) + (1LL * x12) + (1LL * x1)) + (0LL) <= (475LL) && ((1LL * x18) + (1LL * x20) + (1LL * x12) + (1LL * x1)) + (0LL) >= (475LL))) continue;
used[x20] = 1;
for (int p21=0; p21<22; ++p21) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x21=d21[p21];
if (used[x21]) continue;
if (!(((1LL * x21) + (1LL * x13) + (1LL * x5) + (1LL * x16)) + (0LL) <= (524LL) && ((1LL * x21) + (1LL * x13) + (1LL * x5) + (1LL * x16)) + (0LL) >= (524LL))) continue;
if (!(((1LL * x19) + (1LL * x10) + (1LL * x21) + (1LL * x9)) + (0LL) <= (533LL) && ((1LL * x19) + (1LL * x10) + (1LL * x21) + (1LL * x9)) + (0LL) >= (533LL))) continue;
used[x21] = 1;
first[0]=x0;
first[1]=x1;
first[2]=x2;
first[3]=x3;
first[4]=x4;
first[5]=x5;
first[6]=x6;
first[7]=x7;
first[8]=x8;
first[9]=x9;
first[10]=x10;
first[11]=x11;
first[12]=x12;
first[13]=x13;
first[14]=x14;
first[15]=x15;
first[16]=x16;
first[17]=x17;
first[18]=x18;
first[19]=x19;
first[20]=x20;
first[21]=x21;
counts[0]=visits; counts[1]=counts[2]=1; return 1;
used[x21] = 0;
}
used[x20] = 0;
}
used[x19] = 0;
}
used[x18] = 0;
}
used[x17] = 0;
}
used[x16] = 0;
}
used[x15] = 0;
}
used[x14] = 0;
}
used[x13] = 0;
}
used[x12] = 0;
}
used[x11] = 0;
}
used[x10] = 0;
}
used[x9] = 0;
}
used[x8] = 0;
}
used[x7] = 0;
}
used[x6] = 0;
}
used[x5] = 0;
}
used[x4] = 0;
}
used[x3] = 0;
}
used[x2] = 0;
}
used[x1] = 0;
}
used[x0] = 0;
}
counts[0]=visits; return 0; }
