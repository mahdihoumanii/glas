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

#do i  = 1,`n0l'
#do j  = 1,`n1l'
#do k  = 1,`nmis'
#include Files/M0M1Reduced/d`i'x`j'.h
#include Files/MastersToSym.h 
id mis`k' = 1;
.sort 
id mis?{mis1,...,mis`nmis'} = 0;
    .sort 
Mul mis`k'; 
    .sort
#include Files/SymToMasters.h
    .sort
#call rationals
Format;
b GLI, ep,gs,PaVeFun,den,rat;
    .sort 
#write <Files/MasterCoefficients/mi`k'/d`i'x`j'.h> "l d`i'x`j' = (%E ); \n" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs,PaVeFun,den,rat;
    .sort
#write <../Mathematica/Files/MasterCoefficients/mi`k'/d`i'x`j'.m> "d[`i',`j'] = (%E ); \n" d`i'x`j'

    .sort 
Drop; 
    .sort 

#enddo
#enddo
#enddo


b PaVeFun,ep,gs; 
Print; 
    .end
