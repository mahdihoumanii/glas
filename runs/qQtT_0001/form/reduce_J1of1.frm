#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h
#define n0l "1"
#define n1l "10"
#define ntop "3"
.sort
#do i =1,1
#do j =1,`n1l'

#include Files/M0M1top/d`i'x`j'.h

#do k = 1, `ntop'
if (match(GLI(top`k',?a)));
#include Files/IBP/IBP`k'.h
endif;
    .sort 
#enddo 

#include Files/SymmetryRelations.h
    .sort 
id rat(x1?,x2?) = x1*den(x2);
    .sort
#call RationalFunction
repeat id s12?{s12,s23,s34,s45,s15,s13,s14,mt}^-1 = den(s12);
    .sort
Format;
b GLI, ep,gs,PaVeFun, den;
    .sort 
#write <Files/M0M1Reduced/d`i'x`j'.h> "l d`i'x`j' = (%E ); \n" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs,PaVeFun, den;
    .sort
#write <../Mathematica/Files/M0M1Reduced/d`i'x`j'.m> "d[`i',`j'] = (%E ); \n" d`i'x`j'

    .sort 
Drop; 
    .sort 
#message Reduced d`i'x`j' saved.
#enddo 
#enddo 
.end
