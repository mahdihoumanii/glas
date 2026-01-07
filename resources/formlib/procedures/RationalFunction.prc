#procedure RationalFunction 
ab matubgv, topos, gs, PaVeFun , Log, Sqrt,PolyLog,EulerGamma,prop, FCFAD,SPD,GLI,C0,D0; 
    .sort 
PolyRatFun rat; 
Keep Brackets;
factarg den; 
#do r = {s12, s15, s34, s45, s23, mt, Epsilon,ep}
id `r'^pow? = rat(`r'^pow, 1);
#enddo 
    .sort 
#do i= 1,1
id once den(mt?, ?a) *rat(x1?,x2?) = rat(x1, x2*mt)*den(?a); 
id once rat(x1?,x2?)= rat(x1, 1)*prop(x2); 
id once den = 1; 
if (count(den,1)!= 0); 
    redefine i "0";
endif;
    .sort 
#enddo 
    .sort 
PolyRatFun;
    .sort 
id prop(mt?)= den(mt);

factarg den;
repeat;
  id once den(mt?, ?a) = prop(mt) * den(?a);
endrepeat;
id prop(mt?) = den(mt);
id den = 1;
.sort
splitarg den;

id den(mt?) = 1/mt;

repeat;
  id once den(x1?, x2?, ?a) = den(x1 + x2, ?a);
endrepeat;
.sort
id rat(x1?, 1) = x1;
.sort

#endprocedure