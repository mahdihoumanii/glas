#-
#: IncDir /Users/mahdihoumani/Documents/Work/glas/glas/runs/qQtT_0001/form/procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#define n0l "1"
#define in1 "3"
#define in2 "4"

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"
#include declarations.h
    .sort 

#do i =1, `n0l'

#include Files/Amps/amp0l/d`i'.h
    .sort
#enddo
    .sort 

L amp = d1+...+d`n0l';
L ampC = dC1+...+dC`n0l';
    .sort 
Drop d1,...,d`n0l',dC1,...,dC`n0l';

Mul replace_(a6,a5,b6,b5,b3,b2,a3,a2,a2,a3,b2,b3);
id rat(x1?,x2?) = x1*den(x2);
#call RationalFunction

    .sort 
#call color
    .sort 
Skip ampC;

Mul replace_(a`in1',c`in1');
Mul replace_(a`in2',c`in2');
Mul replace_(b`in1',c`in1');
Mul replace_(b`in2',c`in2');

Mul T(`in1')*T(`in2'); 
id T(1) = - T(c, c1, a1);
id T(2) =  T(c, a2, c2);
id T(3) =  T(c, a3, c3);
id T(4) = - T(c, c4, a4);

    .sort 

Mul ampC;
    .sort 

Drop ampC;

#call color


`mand'
#call PolarizationSums(5)
`mand'
    .sort 
repeat id D = 4 -2 *ep;

    .sort 

#call RationalFunction
#call toden
.sort 
Format mathematica;
    .sort 

#write <../mathematica/Files/Ioperator/I3x4.m> "I[`in1',`in2'] = (%E);\n" amp
    .sort
Format;
    .sort
#write <Files/Ioperator/I3x4.h> "l I`in1'x`in2' = (%E);\n" amp

    .end
