#-
#: IncDir /Users/mahdihoumani/Documents/Work/glas/glas/runs/qQtT_0001/form/procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h 


#define np "4"
#define n0l "1"
#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"


#define massless "1,2"
#define massive "3,4"
#define incoming "1,2"
#define outgoing "3,4"
#include Files/TotalLO/TotalLO.h


#do i = 1, `np'
#do j = `i'+ 1 , `np'

#include Files/Ioperator/I`i'x`j'.h

#enddo
#enddo
l const = gs^2/4/Pi/4/Pi * 1/ep ;
l sumcmassless =     
#do i = {`massless'}
    +casimir(`i')
#enddo 
;
l sumgam =
#do i = 1,`np'
    +aGamma(`i')
#enddo 
;
l m0m0 =
#do i = {`massless'}
#do j = {`massless'}
#if (`i' != `j' && `i'<`j')
    +Log(ScaleMu^2*den(SPD(`i',`j')))*I`i'x`j'
#elseif `i' > `j'
    +Log(ScaleMu^2*den(SPD(`i',`j')))*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;

l mm =
#do i = {`massive'}
#do j = {`massive'}
#if (`i' != `j' && `i'<`j')
    +den(Vel(`i',`j')) *Log(Vel,`i',`j')*I`i'x`j'
#elseif `i' > `j'
    +den(Vel(`i',`j')) *Log(Vel,`i',`j')*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;


    .sort 


l m0m=
#do i = {`massive'}
#do j = {`massless'}
#if (`i' != `j' && `i'<`j')
    +Log(mass(p`i')*ScaleMu*den(SPD(`i',`j')))*I`i'x`j'
#elseif `i' > `j'
    +Log(mass(p`i')*ScaleMu*den(SPD(`i',`j')))*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;
    .sort 
#do i = {`incoming'}
#do j = {`incoming'}
argument Log;
argument den;
id SPD(`i',`j') = 2*p`i'.p`j';
id SPD(`j',`i') = 2*p`i'.p`j';
`mand'
endargument;
endargument;
#enddo
#enddo

#do i = {`incoming'}
#do j = {`outgoing'}
argument Log;
argument den;
id SPD(`i',`j') = -2*p`i'.p`j';
id SPD(`j',`i') = -2*p`i'.p`j';
`mand'
endargument;
`mand'
endargument;
#enddo
#enddo

argument Log;
id den(mt?) = 1/mt;
endargument;

`mand'
    .sort 
#do i = {`massive'}
#do j = {`massive'}

id Log(Vel,`i',`j') = Log((1- Vel(`i',`j'))*den(1+ Vel(`i',`j')));

#enddo 
#enddo
    .sort 
#do i =  1,`np';
Drop I`i'x1,...,I`i'x`np';
#enddo 
    .sort 
Local Ioperator = const*(
    ((-2/ep)*sumcmassless + sumgam)*TotalLO
    +   2* m0m0

    - mm

    + 4 * m0m

    );
    .sort 
Drop TotalLO, const, sumcmassless,sumgam, m0m0,m0m, mm;
id aGamma?{aGamma,casimir}(1) = aGamma(q);
id aGamma?{aGamma,casimir}(2) = aGamma(q);
id aGamma?{aGamma,casimir}(3) = aGamma(top);
id aGamma?{aGamma,casimir}(4) = aGamma(top);

id casimir(q?{q,top}) = 4/3;
id casimir(g) = 3;
id aGamma(top) = -2 *4/3;
id aGamma(q)= -3 *4/3;
id aGamma(g) = - 11/3 * 3 + 4/3* 1/2*nl; 


    .sort 
repeat id D = 4-2 *ep;

    .sort 
id ep^pow  = Pole(ep, pow);
id Pole(ep, 0) = 1;
id Pole(ep, -1) = 1/ep;
id Pole(ep, -2) = 1/ep^2;
    .sort 
id Pole(?a) = 0;
    .sort 
#call RationalFunction
#call toden
Format mathematica;
b Log, Vel,ep,Pi,den;
    .sort
#write <../mathematica/Files/Ioperator.m> "Ioperator = (%E);\n" Ioperator
    .sort
Format;
    .sort

b ep;
Print; 
    .end 
