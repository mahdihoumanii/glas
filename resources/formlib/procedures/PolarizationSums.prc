#procedure PolarizationSums(n)
b diracChain, chain,g_;
    .sort 
keep brackets;
#do i=1,`n'
id once matubgv(p1?,s1?,?a, p2?,s2?)*matvbgu(p2?,s2?, ?b, p1?,s1?) = chain(`i', p1,s1,?a,p2,?b, p1,s1)-mass(p2)*chain(`i', p1,s1,?a, ?b,p1,s1);
id chain(`i', p1?,s1?, ?A, p1?,s1?) = chain(`i', p1, ?A) + mass(p1)*chain(`i', ?A); 
id chain(`i', ?a) = g_(`i', ?a);
    .sort 
`mand'
*#call SymToRat
b g_;
    .sort 
Keep brackets;
Tracen,`i';
`mand'
    .sort 
#enddo


*#do i=1,`n'
*id once matubgu(p1?,s1?,?a, p2?,s2?)*matubgu(p2?,s2?, ?b, p1?,s1?) = chain(`i', p1,s1,?a,p2,?b, p1,s1)+mass(p2)*chain(`i', p1,s1,?a, ?b,p1,s1);
*id chain(`i', p1?,s1?, ?A, p1?,s1?) = chain(`i', p1, ?A) + mass(p1)*chain(`i', ?A); 
*id chain(`i', ?a) = g_(`i', ?a);
*    .sort
*Tracen,`i';
*    .sort
*
*#enddo

#endprocedure
