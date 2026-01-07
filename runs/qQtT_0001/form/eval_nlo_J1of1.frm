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

* ---- TREE (this chunk) ----

* (tree skipped)


* ---- ONE-LOOP (this chunk) ----

#do i=1,10
#include Files/qQtT1l
    .sort
l amp = d`i';
    .sort
Drop d1,...,d10;
#call FeynmanRules
`mand'
#call SymToRat
    .sort
b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp1l/d`i'.h> "l d`i' = (%E);\n" amp
    .sort
Drop;
#message loop `i' done
#enddo


.end
