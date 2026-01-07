#procedure Conjugate(Amp, AmpC)
    .sort 
Skip; 

Local `AmpC' = `Amp'; 
id i_ = -i_ ; 
id I = -I; 

Mul replace_(matubgv, matvbgu, matvbgu, matubgv);
id matubgv?diracChain(p1?, s1?, ?a, p2?, s2?)= matubgv(p2, s2, reverse_(?a), p1, s1);


Multiply replace_(<bp1,bbp1>,...,<bp40,bbp40>, <ap1,aap1>,...,<ap40,aap40>, <c1,cc1>,...,<c10,cc10>);
Multiply replace_(<mu1,muu1>,...,<mu40,muu40>,<nu1,nuu1>,...,<nu20,nuu20>);
Multiply replace_(c, cc);
id T(?a,a2?,a3?) = T(reverse_(?a), a3, a2);
id Tr(?a) = Tr(reverse_(?a));
mul replace_(eps,epsC, epsC, eps);
mul replace_(E1,Es1, Es1, E1);
mul replace_(E2,Es2, Es2, E2);
mul replace_(E5,Es5, Es5, E5);


    .sort 


#endprocedure