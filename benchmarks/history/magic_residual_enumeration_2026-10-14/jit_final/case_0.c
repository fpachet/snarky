#include <stdint.h>
int specialized(uint64_t limit, int *first, uint64_t *counts) {
uint64_t visits = 0; unsigned char used[4096] = {0};
counts[0] = counts[1] = counts[2] = 0;
static const int d0[] = {7,6,5,4,3,63,64};
static const int d1[] = {7,6,5,4,3,63,64};
static const int d2[] = {50,51,52,54,55,56,57,4,3,2,1};
static const int d3[] = {50,51,52,54,55,56,57,4,3,2,1};
static const int d4[] = {50,51,52,54,55,56,57,4,3,2,1};
static const int d5[] = {50,51,52,54,55,56,57,6,5,4,3,2,1};
static const int d6[] = {52,54,55,56,57,8,7,6,5,4,3,2,1};
static const int d7[] = {52,54,55,56,57,8,7,6,5,4,3,2,1};
static const int d8[] = {50,51,52,54,55,56,57,6,5,4,3,2,1};
static const int d9[] = {51,52,54,55,56,57,8,7,6,5,4,3,2,1};
static const int d10[] = {50,51,52,54,55,56,57,8,7,6,5,4,3,2,1};
static const int d11[] = {52,54,55,56,57,8,7,6,5,4,3,63,2,64,1};
static const int d12[] = {52,54,55,56,57,8,7,6,5,4,3,63,2,64,1};
static const int d13[] = {50,51,52,54,55,56,57,8,7,6,5,4,3,2,1};
static const int d14[] = {50,51,52,54,55,56,57,8,7,6,5,4,3,63,2,64,1};
static const int d15[] = {50,51,52,54,55,56,57,8,7,6,5,4,3,63,2,64,1};
static const int d16[] = {50,51,52,54,55,56,57,8,7,6,5,4,3,63,2,64,1};
for (int p0=0; p0<7; ++p0) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x0=d0[p0];
if (used[x0]) continue;
if (!(((1LL * x0)) + (4LL) <= (173LL) && ((1LL * x0)) + (235LL) >= (173LL))) continue;
if (!(((1LL * x0)) + (3LL) <= (70LL) && ((1LL * x0)) + (64LL) >= (70LL))) continue;
used[x0] = 1;
for (int p1=0; p1<7; ++p1) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x1=d1[p1];
if (used[x1]) continue;
if (!(((1LL * x1)) + (4LL) <= (129LL) && ((1LL * x1)) + (242LL) >= (129LL))) continue;
if (!(((1LL * x0) + (1LL * x1)) + (0LL) <= (70LL) && ((1LL * x0) + (1LL * x1)) + (0LL) >= (70LL))) continue;
used[x1] = 1;
for (int p2=0; p2<11; ++p2) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x2=d2[p2];
if (used[x2]) continue;
if (!(((1LL * x2)) + (2LL) <= (104LL) && ((1LL * x2)) + (114LL) >= (104LL))) continue;
if (!(((1LL * x2)) + (2LL) <= (62LL) && ((1LL * x2)) + (114LL) >= (62LL))) continue;
used[x2] = 1;
for (int p3=0; p3<11; ++p3) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x3=d3[p3];
if (used[x3]) continue;
if (!(((1LL * x2) + (1LL * x3)) + (1LL) <= (104LL) && ((1LL * x2) + (1LL * x3)) + (57LL) >= (104LL))) continue;
if (!(((1LL * x3)) + (2LL) <= (118LL) && ((1LL * x3)) + (128LL) >= (118LL))) continue;
used[x3] = 1;
for (int p4=0; p4<11; ++p4) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x4=d4[p4];
if (used[x4]) continue;
if (!(((1LL * x2) + (1LL * x3) + (1LL * x4)) + (0LL) <= (104LL) && ((1LL * x2) + (1LL * x3) + (1LL * x4)) + (0LL) >= (104LL))) continue;
if (!(((1LL * x4)) + (2LL) <= (63LL) && ((1LL * x4)) + (114LL) >= (63LL))) continue;
used[x4] = 1;
for (int p5=0; p5<13; ++p5) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x5=d5[p5];
if (used[x5]) continue;
if (!(((1LL * x5) + (1LL * x0)) + (3LL) <= (173LL) && ((1LL * x5) + (1LL * x0)) + (178LL) >= (173LL))) continue;
if (!(((1LL * x5)) + (2LL) <= (108LL) && ((1LL * x5)) + (114LL) >= (108LL))) continue;
used[x5] = 1;
for (int p6=0; p6<13; ++p6) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x6=d6[p6];
if (used[x6]) continue;
if (!(((1LL * x6)) + (3LL) <= (132LL) && ((1LL * x6)) + (185LL) >= (132LL))) continue;
if (!(((1LL * x5) + (1LL * x6)) + (1LL) <= (108LL) && ((1LL * x5) + (1LL * x6)) + (57LL) >= (108LL))) continue;
used[x6] = 1;
for (int p7=0; p7<13; ++p7) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x7=d7[p7];
if (used[x7]) continue;
if (!(((1LL * x6) + (1LL * x7)) + (2LL) <= (132LL) && ((1LL * x6) + (1LL * x7)) + (128LL) >= (132LL))) continue;
if (!(((1LL * x4) + (1LL * x7)) + (1LL) <= (63LL) && ((1LL * x4) + (1LL * x7)) + (57LL) >= (63LL))) continue;
used[x7] = 1;
for (int p8=0; p8<13; ++p8) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x8=d8[p8];
if (used[x8]) continue;
if (!(((1LL * x8) + (1LL * x1)) + (3LL) <= (129LL) && ((1LL * x8) + (1LL * x1)) + (185LL) >= (129LL))) continue;
if (!(((1LL * x5) + (1LL * x6) + (1LL * x8)) + (0LL) <= (108LL) && ((1LL * x5) + (1LL * x6) + (1LL * x8)) + (0LL) >= (108LL))) continue;
used[x8] = 1;
for (int p9=0; p9<14; ++p9) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x9=d9[p9];
if (used[x9]) continue;
if (!(((1LL * x5) + (1LL * x0) + (1LL * x9)) + (2LL) <= (173LL) && ((1LL * x5) + (1LL * x0) + (1LL * x9)) + (121LL) >= (173LL))) continue;
if (!(((1LL * x4) + (1LL * x9) + (1LL * x7)) + (0LL) <= (63LL) && ((1LL * x4) + (1LL * x9) + (1LL * x7)) + (0LL) >= (63LL))) continue;
used[x9] = 1;
for (int p10=0; p10<15; ++p10) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x10=d10[p10];
if (used[x10]) continue;
if (!(((1LL * x10) + (1LL * x5) + (1LL * x0) + (1LL * x9)) + (1LL) <= (173LL) && ((1LL * x10) + (1LL * x5) + (1LL * x0) + (1LL * x9)) + (64LL) >= (173LL))) continue;
if (!(((1LL * x2) + (1LL * x10)) + (1LL) <= (62LL) && ((1LL * x2) + (1LL * x10)) + (57LL) >= (62LL))) continue;
used[x10] = 1;
for (int p11=0; p11<15; ++p11) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x11=d11[p11];
if (used[x11]) continue;
if (!(((1LL * x11) + (1LL * x6) + (1LL * x7)) + (1LL) <= (132LL) && ((1LL * x11) + (1LL * x6) + (1LL * x7)) + (64LL) >= (132LL))) continue;
if (!(((1LL * x3) + (1LL * x11)) + (1LL) <= (118LL) && ((1LL * x3) + (1LL * x11)) + (64LL) >= (118LL))) continue;
used[x11] = 1;
for (int p12=0; p12<15; ++p12) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x12=d12[p12];
if (used[x12]) continue;
if (!(((1LL * x11) + (1LL * x6) + (1LL * x12) + (1LL * x7)) + (0LL) <= (132LL) && ((1LL * x11) + (1LL * x6) + (1LL * x12) + (1LL * x7)) + (0LL) >= (132LL))) continue;
if (!(((1LL * x12)) + (2LL) <= (117LL) && ((1LL * x12)) + (128LL) >= (117LL))) continue;
used[x12] = 1;
for (int p13=0; p13<15; ++p13) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x13=d13[p13];
if (used[x13]) continue;
if (!(((1LL * x13) + (1LL * x8) + (1LL * x1)) + (2LL) <= (129LL) && ((1LL * x13) + (1LL * x8) + (1LL * x1)) + (128LL) >= (129LL))) continue;
if (!(((1LL * x2) + (1LL * x10) + (1LL * x13)) + (0LL) <= (62LL) && ((1LL * x2) + (1LL * x10) + (1LL * x13)) + (0LL) >= (62LL))) continue;
used[x13] = 1;
for (int p14=0; p14<17; ++p14) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x14=d14[p14];
if (used[x14]) continue;
if (!(((1LL * x10) + (1LL * x5) + (1LL * x14) + (1LL * x0) + (1LL * x9)) + (0LL) <= (173LL) && ((1LL * x10) + (1LL * x5) + (1LL * x14) + (1LL * x0) + (1LL * x9)) + (0LL) >= (173LL))) continue;
if (!(((1LL * x14) + (1LL * x12)) + (1LL) <= (117LL) && ((1LL * x14) + (1LL * x12)) + (64LL) >= (117LL))) continue;
used[x14] = 1;
for (int p15=0; p15<17; ++p15) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x15=d15[p15];
if (used[x15]) continue;
if (!(((1LL * x13) + (1LL * x15) + (1LL * x8) + (1LL * x1)) + (1LL) <= (129LL) && ((1LL * x13) + (1LL * x15) + (1LL * x8) + (1LL * x1)) + (64LL) >= (129LL))) continue;
if (!(((1LL * x3) + (1LL * x11) + (1LL * x15)) + (0LL) <= (118LL) && ((1LL * x3) + (1LL * x11) + (1LL * x15)) + (0LL) >= (118LL))) continue;
used[x15] = 1;
for (int p16=0; p16<17; ++p16) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x16=d16[p16];
if (used[x16]) continue;
if (!(((1LL * x13) + (1LL * x15) + (1LL * x8) + (1LL * x16) + (1LL * x1)) + (0LL) <= (129LL) && ((1LL * x13) + (1LL * x15) + (1LL * x8) + (1LL * x16) + (1LL * x1)) + (0LL) >= (129LL))) continue;
if (!(((1LL * x14) + (1LL * x12) + (1LL * x16)) + (0LL) <= (117LL) && ((1LL * x14) + (1LL * x12) + (1LL * x16)) + (0LL) >= (117LL))) continue;
used[x16] = 1;
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
counts[0]=visits; counts[1]=counts[2]=1; return 1;
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
