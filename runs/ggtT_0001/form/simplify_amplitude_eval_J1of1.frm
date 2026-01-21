#-
#: IncDir /Users/mahdihoumani/Documents/Work/glas/resources/formlib/procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define n1l "33"
#define n0l "3"

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"

#include declarations.h
.sort
PolyRatFun rat;
.sort

* ---- TREE (this chunk) ----

#do i=1,3
#include Files/ggtT0l
    .sort
l amp = d`i';
    .sort
Drop d1,...,d3;
#call FeynmanRules
`mand'
#call SymToRat
#call Conjugate(amp,ampC)
    .sort
b diracChain,Color,i_,gs,eps,epsC;
    .sort
#write <Files/Amps/amp0l/d`i'.h> "l d`i' = (%E);\n" amp
#write <Files/Amps/amp0l/d`i'.h> "l dC`i' = (%E);\n" ampC
    .sort
Drop;
#enddo


#message done with tree-level chunk

* ---- ONE-LOOP (this chunk) ----

#do i=1,33
#include Files/ggtT1l
    .sort
l amp = d`i';
    .sort
Drop d1,...,d33;
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
