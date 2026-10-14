#include <stdint.h>
int specialized(uint64_t limit, int *first, uint64_t *counts) {
uint64_t visits = 0; unsigned char used[4096] = {0};
counts[0] = counts[1] = counts[2] = 0;
static const int d0[] = {13,12,11,10,76,77};
static const int d1[] = {13,12,11,10,76,77};
static const int d2[] = {13,12,11,10,76,77};
static const int d3[] = {65,66,71,72,73,4,3};
static const int d4[] = {65,66,71,72,73,74,4,3};
static const int d5[] = {66,71,10,72,73,74,76,4,3};
static const int d6[] = {13,12,11,71,10,72,6,76,77,4};
static const int d7[] = {13,12,11,71,10,72,6,76,77,4};
static const int d8[] = {11,71,10,72,73,74,6,76,77,4,3};
static const int d9[] = {11,71,10,72,73,74,6,76,77,4,3};
static const int d10[] = {13,12,71,72,73,74,6,76,77,4,3};
static const int d11[] = {65,66,71,72,73,74,6,76,77,4,3};
static const int d12[] = {65,66,71,72,73,74,6,76,77,4,3};
static const int d13[] = {65,66,11,71,10,72,73,74,6,76,77,4,3};
static const int d14[] = {13,12,11,71,10,72,73,74,6,76,77,4,3};
for (int p0=0; p0<6; ++p0) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x0=d0[p0];
if (used[x0]) continue;
if (!(((1LL * x0)) + (20LL) <= (102LL) && ((1LL * x0)) + (154LL) >= (102LL))) continue;
if (!(((1LL * x0)) + (6LL) <= (157LL) && ((1LL * x0)) + (154LL) >= (157LL))) continue;
used[x0] = 1;
for (int p1=0; p1<6; ++p1) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x1=d1[p1];
if (used[x1]) continue;
if (!(((1LL * x0) + (1LL * x1)) + (10LL) <= (102LL) && ((1LL * x0) + (1LL * x1)) + (77LL) >= (102LL))) continue;
if (!(((1LL * x1)) + (6LL) <= (151LL) && ((1LL * x1)) + (150LL) >= (151LL))) continue;
used[x1] = 1;
for (int p2=0; p2<6; ++p2) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x2=d2[p2];
if (used[x2]) continue;
if (!(((1LL * x0) + (1LL * x1) + (1LL * x2)) + (0LL) <= (102LL) && ((1LL * x0) + (1LL * x1) + (1LL * x2)) + (0LL) >= (102LL))) continue;
if (!(((1LL * x2)) + (9LL) <= (160LL) && ((1LL * x2)) + (231LL) >= (160LL))) continue;
used[x2] = 1;
for (int p3=0; p3<7; ++p3) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x3=d3[p3];
if (used[x3]) continue;
if (!(((1LL * x3)) + (9LL) <= (210LL) && ((1LL * x3)) + (231LL) >= (210LL))) continue;
if (!(((1LL * x3)) + (3LL) <= (71LL) && ((1LL * x3)) + (77LL) >= (71LL))) continue;
used[x3] = 1;
for (int p4=0; p4<8; ++p4) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x4=d4[p4];
if (used[x4]) continue;
if (!(((1LL * x4)) + (10LL) <= (150LL) && ((1LL * x4)) + (231LL) >= (150LL))) continue;
if (!(((1LL * x4) + (1LL * x1)) + (3LL) <= (151LL) && ((1LL * x4) + (1LL * x1)) + (76LL) >= (151LL))) continue;
used[x4] = 1;
for (int p5=0; p5<9; ++p5) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x5=d5[p5];
if (used[x5]) continue;
if (!(((1LL * x5)) + (10LL) <= (171LL) && ((1LL * x5)) + (231LL) >= (171LL))) continue;
if (!(((1LL * x4) + (1LL * x1) + (1LL * x5)) + (0LL) <= (151LL) && ((1LL * x4) + (1LL * x1) + (1LL * x5)) + (0LL) >= (151LL))) continue;
used[x5] = 1;
for (int p6=0; p6<10; ++p6) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x6=d6[p6];
if (used[x6]) continue;
if (!(((1LL * x6) + (1LL * x4)) + (6LL) <= (150LL) && ((1LL * x6) + (1LL * x4)) + (154LL) >= (150LL))) continue;
if (!(((1LL * x6)) + (7LL) <= (94LL) && ((1LL * x6)) + (154LL) >= (94LL))) continue;
used[x6] = 1;
for (int p7=0; p7<10; ++p7) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x7=d7[p7];
if (used[x7]) continue;
if (!(((1LL * x7) + (1LL * x5)) + (6LL) <= (171LL) && ((1LL * x7) + (1LL * x5)) + (154LL) >= (171LL))) continue;
if (!(((1LL * x6) + (1LL * x7)) + (3LL) <= (94LL) && ((1LL * x6) + (1LL * x7)) + (77LL) >= (94LL))) continue;
used[x7] = 1;
for (int p8=0; p8<11; ++p8) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x8=d8[p8];
if (used[x8]) continue;
if (!(((1LL * x6) + (1LL * x8) + (1LL * x4)) + (3LL) <= (150LL) && ((1LL * x6) + (1LL * x8) + (1LL * x4)) + (77LL) >= (150LL))) continue;
if (!(((1LL * x8) + (1LL * x0)) + (3LL) <= (157LL) && ((1LL * x8) + (1LL * x0)) + (77LL) >= (157LL))) continue;
used[x8] = 1;
for (int p9=0; p9<11; ++p9) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x9=d9[p9];
if (used[x9]) continue;
if (!(((1LL * x9) + (1LL * x7) + (1LL * x5)) + (3LL) <= (171LL) && ((1LL * x9) + (1LL * x7) + (1LL * x5)) + (77LL) >= (171LL))) continue;
if (!(((1LL * x9) + (1LL * x3)) + (0LL) <= (71LL) && ((1LL * x9) + (1LL * x3)) + (0LL) >= (71LL))) continue;
used[x9] = 1;
for (int p10=0; p10<11; ++p10) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x10=d10[p10];
if (used[x10]) continue;
if (!(((1LL * x3) + (1LL * x10)) + (6LL) <= (210LL) && ((1LL * x3) + (1LL * x10)) + (154LL) >= (210LL))) continue;
if (!(((1LL * x6) + (1LL * x7) + (1LL * x10)) + (0LL) <= (94LL) && ((1LL * x6) + (1LL * x7) + (1LL * x10)) + (0LL) >= (94LL))) continue;
used[x10] = 1;
for (int p11=0; p11<11; ++p11) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x11=d11[p11];
if (used[x11]) continue;
if (!(((1LL * x3) + (1LL * x10) + (1LL * x11)) + (3LL) <= (210LL) && ((1LL * x3) + (1LL * x10) + (1LL * x11)) + (77LL) >= (210LL))) continue;
if (!(((1LL * x8) + (1LL * x0) + (1LL * x11)) + (0LL) <= (157LL) && ((1LL * x8) + (1LL * x0) + (1LL * x11)) + (0LL) >= (157LL))) continue;
used[x11] = 1;
for (int p12=0; p12<11; ++p12) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x12=d12[p12];
if (used[x12]) continue;
if (!(((1LL * x3) + (1LL * x10) + (1LL * x11) + (1LL * x12)) + (0LL) <= (210LL) && ((1LL * x3) + (1LL * x10) + (1LL * x11) + (1LL * x12)) + (0LL) >= (210LL))) continue;
if (!(((1LL * x2) + (1LL * x12)) + (6LL) <= (160LL) && ((1LL * x2) + (1LL * x12)) + (154LL) >= (160LL))) continue;
used[x12] = 1;
for (int p13=0; p13<13; ++p13) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x13=d13[p13];
if (used[x13]) continue;
if (!(((1LL * x6) + (1LL * x8) + (1LL * x4) + (1LL * x13)) + (0LL) <= (150LL) && ((1LL * x6) + (1LL * x8) + (1LL * x4) + (1LL * x13)) + (0LL) >= (150LL))) continue;
if (!(((1LL * x13) + (1LL * x2) + (1LL * x12)) + (3LL) <= (160LL) && ((1LL * x13) + (1LL * x2) + (1LL * x12)) + (77LL) >= (160LL))) continue;
used[x13] = 1;
for (int p14=0; p14<13; ++p14) {
if (visits >= limit) { counts[0]=visits; return 2; }
++visits;
int x14=d14[p14];
if (used[x14]) continue;
if (!(((1LL * x9) + (1LL * x7) + (1LL * x5) + (1LL * x14)) + (0LL) <= (171LL) && ((1LL * x9) + (1LL * x7) + (1LL * x5) + (1LL * x14)) + (0LL) >= (171LL))) continue;
if (!(((1LL * x13) + (1LL * x2) + (1LL * x14) + (1LL * x12)) + (0LL) <= (160LL) && ((1LL * x13) + (1LL * x2) + (1LL * x14) + (1LL * x12)) + (0LL) >= (160LL))) continue;
used[x14] = 1;
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
counts[0]=visits; counts[1]=counts[2]=1; return 1;
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
