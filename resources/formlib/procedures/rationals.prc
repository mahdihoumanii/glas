#procedure rationals

    .sort 
repeat id den(?a) = tempden(?a,1);
repeat id tempden(?a,x1?)*tempden(?a,x2?) = tempden(?a,x1+x2);
id tempden(?a, x1?) = den(?a)*tempden(?a, x1-1);
id tempden(?a, pow?) = tempden(?a)^pow; 
    .sort 
ab den; 
    .sort 
repeat id tempden(mt?) = Rat(1, mt);
    .sort 
repeat id x1?{s12,s23,s34,s45,s15,mt,s13,s14} = Rat(x1,1);
    .sort 
PolyratFun rat; 
#do i = 1,1
    .sort 
ab A0, B0, C0, D0;
    .sort 
keep Brackets; 
id once, Rat(x1?,x2?) = rat(x1,x2); 
if (count(Rat,1)!= 0); 
    redefine i "0";
endif; 
    .sort
#enddo
PolyRatFun;
    .sort 

#endprocedure