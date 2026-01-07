#-
#: IncDir /Users/mahdihoumani/Documents/Work/glas/glas/runs/qQtT_0001/form/procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#define n0l "1"

#include declarations.h
    .sort
* load all M0M0 pieces
#do i=1,`n0l'
#do j=1,`n0l'
  #include Files/M0M0/d`i'x`j'.h
    .sort
#enddo
#enddo

L TotalLO =
#do i=1,`n0l'
#do j=1,`n0l'
 + d`i'x`j'
#enddo
#enddo
;
.sort
#call RationalFunction
#call toden
.sort
Format mathematica;
    .sort
#write <../mathematica/Files/M0M0/TotalLO.m> "TotalLO = (%E);\n" TotalLO
    .sort
Format;
    .sort
#write <Files/TotalLO/TotalLO.h> "l TotalLO = (%E);\n" TotalLO

    .end
