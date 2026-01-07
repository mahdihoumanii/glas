#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"
#define b "2"
#define nhext "2"
#define ng "0"

#include declarations.h
    .sort 
PolyRatFun rat;

#do i =1, 1
#do j =1, 1

#include Files/M0M0/d`i'x`j'.h
    .sort

Mul (-1/3*(gs^2*`nhext')/Pi^2 - (gs^2*`nhext')/(4*ep*Pi^2) - (gs^2*`nhext'*Log(ScaleMu^2/mt^2))/(4*Pi^2));
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

#write <../Mathematica/Files/Vzt/d`i'x`j'.m> "d[`i',`j'] = (%E );" d`i'x`j'

    .sort 
Drop;
    .sort 
#message `i'x`j'

#enddo
#enddo

b nl,nh,ep,gs,Pi;
Print; 
    .end
