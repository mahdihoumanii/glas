#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"
#include declarations.h
    .sort 
PolyRatFun rat;

#do i = 1,1
#do j = 1,33

    .sort 
#include Files/Amps/amp0l/d`i'.h
    .sort
Drop d`i';
#include Files/Amps/amp1l/d`j'.h
    .sort 
Mul dC`i';
    .sort 
Drop dC`i';
#call color

b epseps, eps,epsC; 
    .sort 
keep brackets;

repeat id eps(mu1?,p?) *epsC(mu2?,p?) = epseps(mu1 , mu2, p);

id epseps(mu1?, mu2?, p1) = -d_(mu1, mu2) +(p1(mu1)*p2(mu2) + p1(mu2)*p2(mu1) )*den(p1.p2);
`mand'
#call SymToRat
    .sort 

b epseps; 
    .sort 
keep brackets;

id epseps(mu1?, mu2?, p2) = -d_(mu1, mu2) +(p2(mu1)*p1(mu2) + p2(mu2)*p1(mu1) )*den(p2.p1);
`mand'
#call SymToRat
    .sort 

repeat id D = 4-2*ep; 
#call SymToRat
    .sort
repeat id D = 4-2*ep;

#call PolarizationSums(5)

    .sort 
repeat id D = 4-2*ep; 

#call SymToRat
id p1?.p2? = SPD(p1,p2);
    .sort 
repeat id D = 4-2*ep; 

Mul LoopInt(1);
    .sort 
repeat id LoopInt(?a)*SPD(p1?,p2?) = LoopInt(?a,SPD(p1,p2));
repeat id LoopInt(?a)*FAD(?b) = LoopInt(?a,FAD(?b));
repeat id LoopInt(x1?,x2?,?a) = LoopInt(x1*x2,?a);
format;
.sort 
b LoopInt, gs, i_; 
    .sort 
#write <Files/M0M1/d`i'x`j'.h> "l d`i'x`j' = (%E); \n" d`j'
    .sort 
id i_=I; 
format mathematica;
b LoopInt, gs, i_; 
    .sort 
#write <../Mathematica/Files/M0M1/d`i'x`j'.m> " d[`i',`j'] = (%E); \n" d`j'
    .sort 
Drop;
    .sort 
#message `i'x`j'
#enddo
#enddo

.end.
