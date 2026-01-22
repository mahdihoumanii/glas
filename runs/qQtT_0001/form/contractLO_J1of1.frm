#-
#: IncDir procedures
Off Statistics;

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"
#include declarations.h
    .sort
PolyRatFun rat;

#do i = 1,1
#do j = 1,1

    .sort
#include Files/Amps/amp0l/d`i'.h
    .sort
#include Files/Amps/amp0l/d`j'.h

* Example: amp_i * (amp_j)^*
* You likely already have your own exact conventions:
Mul dC`j';
    .sort
#call color


repeat id D = 4-2*ep;
#call SymToRat
    .sort
repeat id D = 4-2*ep;

#call PolarizationSums(5)

repeat id D = 4-2*ep;

    .sort
#call SymToRat

format;
.sort
#write <Files/M0M0/d`i'x`j'.h> "l d`i'x`j' = (%E);\n" d`i'
.sort
format mathematica;
.sort
#write <../Mathematica/Files/M0M0/d`i'x`j'.m> "d[`i',`j'] = (%E);\n" d`i'
.sort
Drop;
#message `i'x`j'

#enddo
#enddo

.end
