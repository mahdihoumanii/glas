#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h
.sort
PolyRatFun rat;
.sort
Cfun SPD(symmetric);
.sort
#define n1l "33"
#define n0l "3"


#do i=3,3
#do j=1,`n1l'

#include Files/M0M1/d`i'x`j'.h
    .sort
#include Files/intrule.h
    .sort

if((occurs(LoopInt) == 1)||(occurs(SPD) == 1)||(occurs(lm1) == 1));
exit "Loop integrals still present in raw form in d`i'xd`j'";

else;
#message all integrals reduced to scalar integrals for `i'x`j'
endif;
    .sort 
#call SymToRat
    .sort 
Format;
b GLI, ep,gs;
    .sort 
#write <Files/M0M1top/d`i'x`j'.h> "l d`i'x`j' = (%E ); \n" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs;
    .sort
#write <../Mathematica/Files/M0M1top/d`i'x`j'.m> "d[`i',`j'] = (%E ); \n" d`i'x`j'

    .sort 
#enddo
#enddo
.end
