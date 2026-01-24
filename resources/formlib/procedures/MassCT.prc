#procedure MassCT(mct,gspow)

    .sort 
id gin(s1?, p1?) = eps(s1, p1);
id gout(s1?, p1?) = epsC(s1, p1);

id qin?{qin, topin}(s1?,p1?) = u(p1,s1);
id qout?{qout, topout}(s1?,p1?) = ub(p1,s1);

id qBin?{qBin, topBin}(s1?, p1?) = vb(p1,s1);
id qBout?{qBout, topBout}(s1?, p1?) = v(p1,s1);


id vx(topB?{qB, topB}(s1?,p3?),top?{q, top}(s2?,p2?),g(s3?,p1?)) = i_*gs*T(s3, s1, s2)*g(s1,s2,s3) ;
id vx(ghB(s1?, p1?), gh(s2?, p2?), g(s3?, p3?))= gs*fsub(s1,s2,s3)*pair(p2,s3); 
id vx(g(s1?,p1?),g(s2?,p2?),g(s3?,p3?))= gs*fsub(s1, s2, s3)*gv(s1,s2,s3, p1,p2,p3);
id vx(g(s1?,p1?),g(s2?,p2?),g(s3?,p3?),g(s4?, p4?))= -i_* gs^2 *( 
                                                        fsub(s1,s2,c1)*fsub(s3, s4, c1)*(fgv(s1, s3,s2, s4)- fgv(s1, s4, s2, s3)) + 
                                                        fsub(s1, s3, c1)*fsub(s2, s4, c1)*(fgv(s1, s2, s3, s4) - fgv(s1, s4,s2, s3))+ 
                                                        fsub(s1, s4, c1)*fsub(s2,s3,c1)*(fgv(s1, s2, s3, s4) - fgv(s1, s3, s2, s4))  
                                                        );
id fgv(s1?, s2?, s3?, s4?) = Gmn(s1, s2)*Gmn(s3, s4);


id,once fprop(s1?, s2?, p?, `mct') =fprop(s1,s2,p,`mct')-fprop(s1,1000, p, `mct') * (-i_*dM) * fprop(1000, s2, p, `mct');


id dM = -((gs^2*`mct')/(3*Pi^2) + (gs^2*`mct')/(4*ep*Pi^2) + (gs^2*`mct'*Log(Mu^2/`mct'^2))/(4*Pi^2) + ep*((gs^2*`mct'*Log(Mu^2/`mct'^2))/(3*Pi^2) + (gs^2*`mct'*Log(Mu^2/`mct'^2)^2)/(8*Pi^2)));

id fprop(s1?, s2?, p?, m?) = i_* SUNFD(s1, s2)  *  prop(p, m)  *  (g(s1, s2, p) + deltas(s1, s2)* m);
repeat id SUNFD(s1?,s2?)*SUNFD(s2?,s3?) = SUNFD(s1,s3);
repeat id deltas(s1?,s2?)*deltas(s2?,s3?) = deltas(s1,s3);

id gprop(s1?, s2?, p?, m?) = i_*SUND(s1, s2)* prop(p, m)*(- Gmn(s1, s2));
id ghprop(s1?, s2?, p?, m?) = i_*SUND(s1, s2)*prop(p, m);
id gv(s1?,s2?,s3?, p1?,p2?,p3?) = (pair(p1,s3)- pair(p2,s3))*Gmn(s1,s2) + (pair(p2,s1)-pair(p3,s1))*Gmn(s2,s3) +(pair(p3,s2) - pair(p1,s2))*Gmn(s3,s1);
repeat;

id deltas(s1?,s2?)*g(s1?, s3?, ?a) = g(s2,s3, ?a);
id deltas(s2?,s1?)*g(s1?, s3?, ?a) = g(s2,s3, ?a);
id deltas(s1?,s2?)*g(s3?, s1?, ?a) = g(s3,s2, ?a);
id deltas(s2?,s1?)*g(s3?, s1?, ?a) = g(s3,s2, ?a);


id deltas(s1?, s2?)*u?{ub, v, vb, u}(p?, s1) = u(p, s2);
id deltas(s2?, s1?)*u?{ub, v, vb, u}(p?, s1) = u(p, s2);

id SUNFD(s1?, s2?)*T(mu?, s2?,s3?) = T(mu, s1, s3);
id SUNFD(s2?, s1?)*T(mu?, s2?,s3?) = T(mu, s1, s3);
id SUNFD(s1?, s2?)*T(mu?, s3?,s2?) = T(mu, s3, s1);
id SUNFD(s2?, s1?)*T(mu?, s3?,s2?) = T(mu, s3, s1);

repeat id Gmn(s1?, s2?)*Gmn(s2?, s3?)  = Gmn(s1, s3);
repeat id Gmn(s2?, s1?)*Gmn(s2?, s3?)  = Gmn(s1, s3);

id Gmn(s1?, s2?)*eps?{eps, epsC}(s1?, p?) = eps(s2, p);
id Gmn(s2?, s1?)*eps?{eps, epsC}(s1?, p?) = eps(s2, p);


id Gmn(s1?, s2?)*g(?a, s2?) = g(?a, s1);
id Gmn(s2?, s1?)*g(?a, s2?) = g(?a, s1);

id Gmn(s1?, s2?)*Gmn(s2?, s3?) = Gmn(s1, s3); 
id Gmn(s2?, s1?)*Gmn(s2?, s3?) = Gmn(s1, s3); 

id Gmn(s1?, s2?)*pair(?a, s2?) = pair(?a, s1);
id Gmn(s2?, s1?)*pair(?a, s2?) = pair(?a, s1);


id SUND(s1?, s2?)*T(s1?, ?a) = T(s2, ?a); 
id SUND(s2?, s1?)*T(s1?, ?a) = T(s2, ?a); 

id SUND(s1?, s2?)*fsub(?b, s1?, ?a) = fsub(?b,s2, ?a); 
id SUND(s2?, s1?)*fsub(?b, s1?, ?a) = fsub(?b,s2, ?a); 
endrepeat;


splitarg g, pair; 
repeat id g(s1?, s2?, p1?, p2?, ?a) = g(s1, s2, p1)+ g(s1, s2, p2, ?a);
repeat id pair(p1?, p2?, ?a, s1?) = pair(p1, s1)+ pair(p2,?a, s1);
id pair(-p?{p1,...,p10, lm1,...,lm10}, s1?) = -pair(p, s1);
repeat id g(s1?, s2?, ?a, -p?{p1,..., p10,lm1,...,lm5}, ?b) = -g(s1, s2, ?a, p, ?b);
    .sort 
repeat id g(s1?, s2?, ?a)*g(s2?, s3?, ?b) = g(s1, s3, ?a, ?b);



id ub(p1?, s1?)*g(s1?,s2?, ?a)*v(p2?, s2?) = matubgv(p1, ?a, p2);
id ub(p1?, s1?)*g(s1?,s2?, ?a)*u(p2?, s2?) = matubgu(p1, ?a, p2);
id vb(p1?, s1?)*g(s1?,s2?, ?a)*v(p2?, s2?) = matvbgv(p1, ?a, p2);
id vb(p1?, s1?)*g(s1?,s2?, ?a)*u(p2?, s2?) = matvbgu(p1, ?a, p2);
id pair(p1?, s1?)*eps?{eps, epsC}(s1?, p?) = eps(p1, p);
id pair(p1?, s1?)*matubgv?diracChain(?a, s1?, ?b) = matubgv(?a, p1, ?b);




#do i= 1, 10

repeat; 
id T(`i', ?a) = T(bp`i', ?a); 
id T(-`i', ?a) = T(b`i', ?a); 

id pair(p?, `i') = pair(p, nu`i');
id pair(p?, -`i') = pair(p, mu`i');

id Gmn(?a, `i', ?b) = Gmn(?a, nu`i', ?b);
id Gmn(?a, -`i', ?b) = Gmn(?a, mu`i', ?b);

id matubgv?diracChain(?a, `i', ?b) = matubgv(?a, nu`i', ?b);
id matubgv?diracChain(?a, -`i', ?b) = matubgv(?a, mu`i', ?b);

id g(s1?,s2?, ?a, -`i', ?b) = g(s1, s2, ?a, mu`i', ?b); 
id g(s1?,s2?, ?a, `i', ?b) = g(s1, s2, ?a, nu`i', ?b); 

id eps?{eps, epsC}(`i', ?b) = eps(nu`i', ?b);
id eps?{eps, epsC}(-`i', ?b) = eps(mu`i', ?b);

id fsub(?a, `i', ?b) = fsub(?a , bp`i', ?b);
id fsub(?a, -`i', ?b) = fsub(?a , b`i', ?b);

endrepeat; 
#enddo 


id pair(p?,mu1?) = p(mu1);

#do i= 1, 10
id T(?a, `i', ?c) = T(?a,ap`i', ?c );
id T(?a, -`i', ?c) = T(?a,a`i', ?c );
id matubgv?diracChain(p`i', ?a) = matubgv(p`i', s`i', ?a);
id matubgv?diracChain(?b, p`i') = matubgv(?b, p`i', s`i');
#enddo 
id Gmn(?a) = d_(?a);
id fsub(?a) = f(?a);

    .sort 
splitarg prop; 
id prop(?a, p?{lm1, -lm1}, ?b) = FAD(?a,p, ?b);
id once FAD(?a, 0)*g(s1?, s1?, ?b) = nl*FAD(?a, 0)*g(s1,s1, ?b);
id once FAD(?a, mt)*g(s1?, s1?, ?b) = nh*FAD(?a, mt)*g(s1,s1, ?b);
repeat id FAD(p1?,p2?, ?a,m?)=  FAD(p1+p2,?a, m);
repeat id prop(p1?,p2?, ?a,m?)=  prop(p1+p2,?a, m);
id prop(p?, m?) =  den(p.p- m^2);
    .sort 
id gs^pow? = Pole(gs, pow);
    .sort 

id Pole(gs,`gspow') = gs^`gspow';

    .sort 
id Pole(?a) = 0; 

#do i=1,3
id once g(s1?, s1?, ?a) = g_(`i', ?a); 
Tracen,`i';
#enddo 

    .sort 





#endprocedure