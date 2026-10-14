#include <stdint.h>
int specialized(uint64_t limit, int *first, uint64_t *counts) {
uint64_t visits = 0; unsigned char used[4096] = {0};
counts[0] = counts[1] = counts[2] = 0;
static const int d0[] = {22,90,72,40};
static const int d1[] = {40,72,22,90};
static const int d2[] = {106,102,107,101,83,125,90};
static const int d3[] = {83,74,102,125,90,40,69,107};
static const int d4[] = {40,22,90,83,102,74,69,107};
static const int d5[] = {77,117,69,99,93,90,106,109,127};
static const int d6[] = {74,90,69,109,93,106,22,40,72,77};
static const int d7[] = {102,99,93,74,90,109,127,77,72,106};
static const int d8[] = {109,127,90,93,22,40,117,106,69,77,99};
static const int d9[] = {117,127,93,109,69,77,99,22,40,106,90};
static const int d10[] = {74,72,109,40,77,69,102,90,127,93,106,99};
static const int d11[] = {117,90,109,83,77,93,102,88,101,125,107,72,106,127,99};
static const int d12[] = {93,125,83,106,107,99,102,117,77,127,72,88,101,90,109};
static const int d13[] = {117,88,107,77,102,83,93,127,74,125,106,90,69,99,101,109,72};
static const int d14[] = {77,83,99,101,125,72,69,117,93,102,88,74,127,107,109,106,90};
static const int d15[] = {127,88,93,90,72,109,69,101,77,99,106,74,102,83,125,117,40,107};
static const int d16[] = {88,127,106,83,74,69,117,93,102,109,90,125,107,99,72,77,40,101};
static const int d17[] = {109,107,83,99,77,106,127,69,90,88,40,101,93,74,125,117,102,72,22};
static const int d18[] = {40,106,127,102,107,101,93,74,109,99,69,72,90,117,77,83,88,22,125};
for (int p0=0; p0<4; ++p0) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x0=d0[p0];
if (used[x0]) continue;
if (!(((1LL * x0)) + (22LL) <= (112LL) && ((1LL * x0)) + (90LL) >= (112LL))) continue;
if (!(((1LL * x0)) + (279LL) <= (510LL) && ((1LL * x0)) + (508LL) >= (510LL))) continue;
used[x0] = 1;
for (int p1=0; p1<4; ++p1) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x1=d1[p1];
if (used[x1]) continue;
if (!(((1LL * x0) + (1LL * x1)) + (0LL) <= (112LL) && ((1LL * x0) + (1LL * x1)) + (0LL) >= (112LL))) continue;
if (!(((1LL * x1)) + (84LL) <= (309LL) && ((1LL * x1)) + (381LL) >= (309LL))) continue;
used[x1] = 1;
for (int p2=0; p2<7; ++p2) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x2=d2[p2];
if (used[x2]) continue;
if (!(((1LL * x2)) + (216LL) <= (431LL) && ((1LL * x2)) + (381LL) >= (431LL))) continue;
if (!(((1LL * x2)) + (62LL) <= (249LL) && ((1LL * x2)) + (232LL) >= (249LL))) continue;
used[x2] = 1;
for (int p3=0; p3<8; ++p3) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x3=d3[p3];
if (used[x3]) continue;
if (!(((1LL * x3)) + (189LL) <= (544LL) && ((1LL * x3)) + (508LL) >= (544LL))) continue;
if (!(((1LL * x2) + (1LL * x3)) + (22LL) <= (249LL) && ((1LL * x2) + (1LL * x3)) + (107LL) >= (249LL))) continue;
used[x3] = 1;
for (int p4=0; p4<8; ++p4) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x4=d4[p4];
if (used[x4]) continue;
if (!(((1LL * x4)) + (135LL) <= (406LL) && ((1LL * x4)) + (490LL) >= (406LL))) continue;
if (!(((1LL * x2) + (1LL * x3) + (1LL * x4)) + (0LL) <= (249LL) && ((1LL * x2) + (1LL * x3) + (1LL * x4)) + (0LL) >= (249LL))) continue;
used[x4] = 1;
for (int p5=0; p5<9; ++p5) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x5=d5[p5];
if (used[x5]) continue;
if (!(((1LL * x5)) + (44LL) <= (208LL) && ((1LL * x5)) + (254LL) >= (208LL))) continue;
if (!(((1LL * x0) + (1LL * x5)) + (210LL) <= (510LL) && ((1LL * x0) + (1LL * x5)) + (381LL) >= (510LL))) continue;
used[x5] = 1;
for (int p6=0; p6<10; ++p6) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x6=d6[p6];
if (used[x6]) continue;
if (!(((1LL * x4) + (1LL * x6)) + (113LL) <= (406LL) && ((1LL * x4) + (1LL * x6)) + (381LL) >= (406LL))) continue;
if (!(((1LL * x6)) + (112LL) <= (223LL) && ((1LL * x6)) + (254LL) >= (223LL))) continue;
used[x6] = 1;
for (int p7=0; p7<10; ++p7) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x7=d7[p7];
if (used[x7]) continue;
if (!(((1LL * x2) + (1LL * x7)) + (144LL) <= (431LL) && ((1LL * x2) + (1LL * x7)) + (254LL) >= (431LL))) continue;
if (!(((1LL * x7) + (1LL * x6)) + (40LL) <= (223LL) && ((1LL * x7) + (1LL * x6)) + (127LL) >= (223LL))) continue;
used[x7] = 1;
for (int p8=0; p8<11; ++p8) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x8=d8[p8];
if (used[x8]) continue;
if (!(((1LL * x5) + (1LL * x8)) + (22LL) <= (208LL) && ((1LL * x5) + (1LL * x8)) + (127LL) >= (208LL))) continue;
if (!(((1LL * x1) + (1LL * x8)) + (62LL) <= (309LL) && ((1LL * x1) + (1LL * x8)) + (254LL) >= (309LL))) continue;
used[x8] = 1;
for (int p9=0; p9<11; ++p9) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x9=d9[p9];
if (used[x9]) continue;
if (!(((1LL * x5) + (1LL * x9) + (1LL * x8)) + (0LL) <= (208LL) && ((1LL * x5) + (1LL * x9) + (1LL * x8)) + (0LL) >= (208LL))) continue;
if (!(((1LL * x9)) + (134LL) <= (410LL) && ((1LL * x9)) + (381LL) >= (410LL))) continue;
used[x9] = 1;
for (int p10=0; p10<12; ++p10) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x10=d10[p10];
if (used[x10]) continue;
if (!(((1LL * x3) + (1LL * x10)) + (149LL) <= (544LL) && ((1LL * x3) + (1LL * x10)) + (381LL) >= (544LL))) continue;
if (!(((1LL * x7) + (1LL * x10) + (1LL * x6)) + (0LL) <= (223LL) && ((1LL * x7) + (1LL * x10) + (1LL * x6)) + (0LL) >= (223LL))) continue;
used[x10] = 1;
for (int p11=0; p11<15; ++p11) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x11=d11[p11];
if (used[x11]) continue;
if (!(((1LL * x2) + (1LL * x7) + (1LL * x11)) + (72LL) <= (431LL) && ((1LL * x2) + (1LL * x7) + (1LL * x11)) + (127LL) >= (431LL))) continue;
if (!(((1LL * x11) + (1LL * x9)) + (62LL) <= (410LL) && ((1LL * x11) + (1LL * x9)) + (254LL) >= (410LL))) continue;
used[x11] = 1;
for (int p12=0; p12<15; ++p12) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x12=d12[p12];
if (used[x12]) continue;
if (!(((1LL * x12) + (1LL * x2) + (1LL * x7) + (1LL * x11)) + (0LL) <= (431LL) && ((1LL * x12) + (1LL * x2) + (1LL * x7) + (1LL * x11)) + (0LL) >= (431LL))) continue;
if (!(((1LL * x12) + (1LL * x0) + (1LL * x5)) + (138LL) <= (510LL) && ((1LL * x12) + (1LL * x0) + (1LL * x5)) + (254LL) >= (510LL))) continue;
used[x12] = 1;
for (int p13=0; p13<17; ++p13) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x13=d13[p13];
if (used[x13]) continue;
if (!(((1LL * x13) + (1LL * x4) + (1LL * x6)) + (44LL) <= (406LL) && ((1LL * x13) + (1LL * x4) + (1LL * x6)) + (254LL) >= (406LL))) continue;
if (!(((1LL * x12) + (1LL * x0) + (1LL * x5) + (1LL * x13)) + (69LL) <= (510LL) && ((1LL * x12) + (1LL * x0) + (1LL * x5) + (1LL * x13)) + (127LL) >= (510LL))) continue;
used[x13] = 1;
for (int p14=0; p14<17; ++p14) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x14=d14[p14];
if (used[x14]) continue;
if (!(((1LL * x14) + (1LL * x3) + (1LL * x10)) + (80LL) <= (544LL) && ((1LL * x14) + (1LL * x3) + (1LL * x10)) + (254LL) >= (544LL))) continue;
if (!(((1LL * x12) + (1LL * x14) + (1LL * x0) + (1LL * x5) + (1LL * x13)) + (0LL) <= (510LL) && ((1LL * x12) + (1LL * x14) + (1LL * x0) + (1LL * x5) + (1LL * x13)) + (0LL) >= (510LL))) continue;
used[x14] = 1;
for (int p15=0; p15<18; ++p15) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x15=d15[p15];
if (used[x15]) continue;
if (!(((1LL * x14) + (1LL * x3) + (1LL * x10) + (1LL * x15)) + (40LL) <= (544LL) && ((1LL * x14) + (1LL * x3) + (1LL * x10) + (1LL * x15)) + (127LL) >= (544LL))) continue;
if (!(((1LL * x11) + (1LL * x15) + (1LL * x9)) + (22LL) <= (410LL) && ((1LL * x11) + (1LL * x15) + (1LL * x9)) + (127LL) >= (410LL))) continue;
used[x15] = 1;
for (int p16=0; p16<18; ++p16) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x16=d16[p16];
if (used[x16]) continue;
if (!(((1LL * x14) + (1LL * x3) + (1LL * x10) + (1LL * x15) + (1LL * x16)) + (0LL) <= (544LL) && ((1LL * x14) + (1LL * x3) + (1LL * x10) + (1LL * x15) + (1LL * x16)) + (0LL) >= (544LL))) continue;
if (!(((1LL * x16) + (1LL * x1) + (1LL * x8)) + (22LL) <= (309LL) && ((1LL * x16) + (1LL * x1) + (1LL * x8)) + (127LL) >= (309LL))) continue;
used[x16] = 1;
for (int p17=0; p17<19; ++p17) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x17=d17[p17];
if (used[x17]) continue;
if (!(((1LL * x13) + (1LL * x4) + (1LL * x6) + (1LL * x17)) + (22LL) <= (406LL) && ((1LL * x13) + (1LL * x4) + (1LL * x6) + (1LL * x17)) + (127LL) >= (406LL))) continue;
if (!(((1LL * x11) + (1LL * x15) + (1LL * x9) + (1LL * x17)) + (0LL) <= (410LL) && ((1LL * x11) + (1LL * x15) + (1LL * x9) + (1LL * x17)) + (0LL) >= (410LL))) continue;
used[x17] = 1;
for (int p18=0; p18<19; ++p18) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x18=d18[p18];
if (used[x18]) continue;
if (!(((1LL * x13) + (1LL * x4) + (1LL * x6) + (1LL * x17) + (1LL * x18)) + (0LL) <= (406LL) && ((1LL * x13) + (1LL * x4) + (1LL * x6) + (1LL * x17) + (1LL * x18)) + (0LL) >= (406LL))) continue;
if (!(((1LL * x16) + (1LL * x1) + (1LL * x8) + (1LL * x18)) + (0LL) <= (309LL) && ((1LL * x16) + (1LL * x1) + (1LL * x8) + (1LL * x18)) + (0LL) >= (309LL))) continue;
used[x18] = 1;
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
counts[0]=visits; counts[1]=counts[2]=1; return 1;
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
