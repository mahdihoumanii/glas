#procedure Together
    .sort 
PolyRatFun rat; 
    .sort 
ab GLI,gs,PolyLog, Log,Sqrt,Epsilon,MathCalLi2,C0,D0,EulerGamma, diracChain; 
    .sort 
keep brackets; 
#do r = {s12,s23,s34,s45,s15,mt, s, t, x, ktsq , kt3}
id `r'^pow? = rat(`r'^pow ,1);
#enddo 
id den(mt?) = rat(1, mt); 
    .sort 
keep brackets; 
    .sort 

#endprocedure