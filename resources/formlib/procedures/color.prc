#procedure color
repeat;
	id,once,Tr(?a) = T(?a,l1,l1)*nf;
	sum l1;
	repeat;
		id,once,T(m1?,m2?,?a,l1?,l2?) = T(m1,l1,l3)*T(m2,?a,l3,l2);
		sum l3;
	endrepeat;
endrepeat;
b T, f; 
	.sort 
keep brackets; 
#do i = 1,1
if ( count(f,1) || match(T(m1?,l1?,l2?)*T(m1?,l3?,l4?)) )
		redefine i "0";
id,once,f(m1?,m2?,m3?) = 1/a/i_*T(m1,l1,l2)*T(m2,l2,l3)*T(m3,l3,l1)
			-1/a/i_*T(m3,l1,l2)*T(m2,l2,l3)*T(m1,l3,l1);
sum l1,l2,l3;
id	T(m1?,l1?,l2?)*T(m1?,l3?,l4?) = Tp(l1,l2,l3,l4);
#do j = 1,1
if ( count(Tp,1) ) redefine j "0";
.sort
id,once,Tp(l1?,l2?,l3?,l4?) =
			a*(SUND(l1,l4)*SUND(l2,l3)-SUND(l1,l2)*SUND(l3,l4)/NF);
repeat; 
id SUND(mu1?,mu2?)*SUND(mu2?,mu3?) = SUND(mu1,mu3);
id SUND(mu1?, mu2?)*T(b1?, a1?,mu2?)= T(b1, a1, mu1); 
id SUND(mu1?, mu2?)*T(b1?,mu2? ,a1?)= T(b1,  mu1,a1); 
id SUND(mu1?,mu1?)=3; 
id SUND(mu1?,mu2?)*SUND(mu1?,mu2?) = 3; 
endrepeat;
*renumber;
#enddo
#enddo
repeat;
	id	T(m1?,?a,l1?,l2?)*T(m2?,?b,l2?,l3?) = T(m1,?a,m2,?b,l1,l3);
endrepeat;
id	T(?a,l1?,l1?) = Tr(?a)/nf;
id	Tr(m1?) = 0;
id	Tr(m1?,m2?) = a*SUND(m1,m2)*nf;
.sort


repeat; 
id SUND(mu1?,mu2?)*SUND(mu2?,mu3?) = SUND(mu1,mu3);
id SUND(mu1?, mu2?)*T(b1?, a1?,mu2?)= T(b1, a1, mu1); 
id SUND(mu1?, mu2?)*T(b1?,mu2? ,a1?)= T(b1,  mu1,a1); 
id SUND(mu1?,mu1?)=NF; 
id SUND(mu1?,mu2?)*SUND(mu1?,mu2?) = NF; 
endrepeat;



id	cF = a*(NF^2-1)/NF;
id	cA = 2*a*NF;
id a^pow? = 1/2^pow;
id a^pow? = TF^pow;
id	[cF-cA/6] = Tf*(2*NF/3-1/NF);
id NF = 3; 
id 1/NF = 1/3;
id Tf = 1/2; 
id 1/TF = 2; 

.sort

#endprocedure