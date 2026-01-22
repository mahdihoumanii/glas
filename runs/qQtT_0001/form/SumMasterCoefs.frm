#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;



#define n1l "10"
#define n0l "1"
#define nmis "8"



#include declarations.h
.sort
#do k = 1, `nmis'
#do i = 1, `n0l'
#do j = 1, `n1l'

#include Files/MasterCoefficients/mi`k'/d`i'x`j'.h
    .sort
id rat(?a) = Rat(?a);
    .sort
#enddo
l coef`k'x`i' = d`i'x1+...+d`i'x`n1l';
    .sort
Drop d`i'x1,...,d`i'x`n1l';
    .sort
#enddo
l coef`k' = coef`k'x1+...+coef`k'x`n0l';
    .sort
Drop coef`k'x1,...,coef`k'x`n0l';
    .sort
PolyratFun rat; 
#do i = 1,1
    .sort 
ab A0, B0, C0, D0,den,ep;
    .sort 
keep Brackets; 
id once, Rat(x1?,x2?) = rat(x1,x2); 
if (count(Rat,1)!= 0); 
    redefine i "0";
endif; 
    .sort
#enddo
PolyRatFun;
    .sort 
id i_ = I;
format mathematica;
b den,gs, ep, rat,PaVeFun,i_;
    .sort
#write <../Mathematica/Files/MasterCoefficients/mi`k'/MasterCoefficient`k'.m> "coef[`k'] = (%E ); \n" coef`k'
    .sort
Drop;
    .sort 
#enddo

Print;
    .end
