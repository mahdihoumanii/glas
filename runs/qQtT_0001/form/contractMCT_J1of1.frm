#- 
#: IncDir procedures
Off Statistics;

#include declarations.h

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"

#do i = 1, 1
#do j = 1, 1
    .sort 
#include Files/Amps/mct/d`i'.h
    .sort 
l amp = d`i'; 
    .sort 
Drop d`i'; 
    .sort
#include Files/Amps/amp0l/d`j'.h
Local ampC = 2* dC`j';
    .sort 

Mul ampC; 
    .sort 

Drop d`j',dC`j', ampC;
    .sort 

#call color

b epseps, eps,epsC;
    .sort
keep brackets;

repeat id eps(mu1?,p?) *epsC(mu2?,p?) = epseps(mu1 , mu2, p);
id epseps(mu1?,mu2?,p?) = -d_(mu1,mu2);


repeat id D = 4-2*ep; 
#call RationalFunction
#call PolyRat

#call PolarizationSums(5)
id D = 4-2 *ep;
`mand'
    .sort 

id ep^pow? = Pole(ep, pow);

id Pole(ep, 0) = 1;
id Pole(ep, -1) = 1/ep;
    .sort 
id Pole(?a) = 0;
    .sort 

#call Together
Format Mathematica; 
    .sort 
Format Mathematica; 
    .sort 

#write <../Mathematica/Files/Vm/d`i'x`j'.m> "d[`i',`j'] = (%E );" amp

    .sort 
Drop;

#message `i'x`j'
#enddo
#enddo
    .end
