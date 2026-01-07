#procedure DiracSimplify
    .sort 
b diracChain, eps, epsC;
    .sort
keep brackets;
**** Simplifying Lorentz Indices in Dirac Gammas 
    .sort
id matubgv(p1?, s1?, ?a, p2?, s2?) = UB(p1,s1)*Gamma(?a)*V(p2,s2);
repeat id Gamma(mu1? ,mu2?, ?b) = Gamma(mu1)*Gamma(mu2)*Gamma(?b);
id Gamma = 1; 

#do i=1 ,10
id eps(mu1?, p`i') = E`i'(mu1);
id epsC(mu1?,p`i') = Es`i'(mu1);
#enddo


id p5 = p1+p2-p3-p4; 
    .sort 

argument Gamma, den, prop, FAD;
id p5 = p1+p2-p3-p4;
endargument; 
    .sort 
splitarg Gamma;
repeat id Gamma(p1?,p2?,?a) =Gamma(p1)+ Gamma(p2)+ Gamma(?a);
id Gamma = 0;
id Gamma(-p?{p1,p2,p3,p4,p5,lm1}) = -Gamma(p);




#do i =1, 10
repeat;
id Gamma(mu1?)*Gamma(nu`i') = 2*d_(mu1, nu`i')- Gamma(nu`i')*Gamma(mu1); 
id Gamma(nu`i')*Gamma(nu`i') =D;
`mand'
endrepeat;
#enddo


#do i =1, 10
repeat;
id Gamma(nu1?)*Gamma(mu`i') = 2*d_(nu1, mu`i')- Gamma(mu`i')*Gamma(nu1); 
id Gamma(mu`i')*Gamma(mu`i') =D;
`mand'
endrepeat;
#enddo


#do i =1, 5
repeat;
id Gamma(mu1?)*Gamma(p`i') = 2*p`i'(mu1)- Gamma(p`i')*Gamma(mu1); 
id Gamma(p`i')*Gamma(p`i') = p`i'.p`i'; 
id UB(p3,s3)*Gamma(p3) = mt*UB(p3,s3);

`mand'
endrepeat;
#enddo

repeat;
id Gamma(p4)*Gamma(mu1?) = 2*p4(mu1)- Gamma(mu1)*Gamma(p4); 
id Gamma(p4)*V(p4,s4) = -mt*V(p4,s4);
endrepeat;


#do i =1,10
repeat;
id Gamma(mu1?)*Gamma(E`i') = 2*E`i'(mu1)- Gamma(E`i')*Gamma(mu1); 
id Gamma(E`i')*Gamma(E`i') = E`i'.E`i'; 
`mand'
endrepeat;
#enddo

#do i =1,10
repeat;
id Gamma(mu1?)*Gamma(Es`i') = 2*Es`i'(mu1) - Gamma(Es`i')*Gamma(mu1); 
id Gamma(Es`i')*Gamma(Es`i') = Es`i'.Es`i';
`mand'
endrepeat;
id p`i'.E`i'=0;
#enddo

repeat;
id Gamma(mu1?)*Gamma(lm1) = 2*lm1(mu1)- Gamma(lm1)*Gamma(mu1); 
id Gamma(lm1)*Gamma(lm1) = lm1.lm1; 
`mand'
endrepeat;



repeat id Gamma(?a)*Gamma(?b) = Gamma(?a,?b);
id UB(p1?,s1?)*Gamma(?a)*V(p2?,s2?) = matubgv(p1,s1, ?a, p2,s2);
id UB(p1?,s1?)*V(p2?,s2?) = matubgv(p1,s1, p2,s2);
    .sort
#do i=1, 10
id E`i'.p?!{Es5, E1,E2,Es1,Es2,E5} = eps(p, p`i');
id Es`i'.p?!{Es5, E1,E2,Es1,Es2,E5} = epsC(p, p`i');
id matubgv(?a,E`i', ?b) = matubgv(?a, mu`i', ?b)*eps(mu`i', p`i');
id matubgv(?a,Es`i', ?b) = matubgv(?a, mu`i', ?b)*epsC(mu`i', p`i');
id matvbgu(?a,E`i', ?b) = matvbgu(?a, mu`i', ?b)*eps(mu`i', p`i');
id matvbgu(?a,Es`i', ?b) = matvbgu(?a, mu`i', ?b)*epsC(mu`i', p`i');
#enddo

    .sort 
#do i=1, 10
#do j=1, 10
id E`i'.E`j' = eps(mu`i',p`i')*eps(mu`i', p`j');
id Es`i'.Es`j' = epsC(mu`i',p`i')*epsC(mu`i', p`j');
id Es`i'.E`j' = epsC(mu`i',p`i')*eps(mu`i', p`j');
#enddo
#enddo
    .sort 

#endprocedure
