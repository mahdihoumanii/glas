#procedure PolyRat 
    .sort 
PolyRatFun rat; 

#do r= {s12,s15,s34,s45, s23, mt, Epsilon, s, t , x, ktsq, kt3, nh, nl}
    b `r', rat; 
        .sort 
keep brackets; 
id `r'^pow? = rat(`r'^pow, 1);
#enddo 

    .sort 
id den(mt?) = rat(1, mt); 
*id den(?mt) = rat(1, ?mt); 
    .sort 
PolyRatFun;

.sort 
id rat(x1?,x2?)= x1*den(x2); 
id den(1) = 1; 

#endprocedure