#-
#: IncDir /Users/mahdihoumani/Documents/Work/glas/glas/resources/formlib/procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define n1l "10"
#define n0l "1"

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"

#include declarations.h
.sort
PolyRatFun rat;
.sort


* ---- TREE ----
#do i = 1,1
#include Files/Amps/amp0l/d`i'.h
    .sort
l amp = d`i';
    .sort
Drop d1,...,d1;

#call SymToRat
#call DiracSimplify
#call SymToRat

b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp0l/d`i'.h> "l d`i' = (%E);\n" amp
    .sort
Drop;
#message dirac_tree `i'
#enddo


* ---- ONE-LOOP ----
#do i = 1,10
#include Files/Amps/amp1l/d`i'.h
    .sort
l amp = d`i';
    .sort
Drop d1,...,d10;

#call SymToRat
#call DiracSimplify
#call SymToRat

b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp1l/d`i'.h> "l d`i' = (%E);\n" amp
    .sort
Drop;
#message dirac_loop `i'
#enddo


.end
