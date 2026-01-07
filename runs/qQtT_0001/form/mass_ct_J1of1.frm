#- 
#:IncDir procedures
Off Statistics;

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"

#include declarations.h
.sort

#do i = 1, 1

#include Files/qQtT0l
#call MassCT(mt, 4)
`mand'

.sort
L amp = d`i';
.sort
Drop d1,...,d1;

*  output for later DiracSimplify stage:
#write <Files/Amps/mct/d`i'.h> "l d`i' = (%E);\n" amp
.sort
Drop;

#message mct_raw `i'
#enddo

.end
