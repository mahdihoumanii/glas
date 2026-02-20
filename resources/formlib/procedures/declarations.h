s Tf, mu, md, mt, mc, ms, mb, m, mq, gs, me, mMu, ge, D, Epsilon, ScaleMu,Mu, I, nl, nh,top1, im,ep,Mu;
Dimension D; 
AutoDeclare v p, lm, Eps; 
AutoDeclare s s , x, t, u,ktsq, kt3; 
s z, lambda,dM; 
CFun A0, B0, C0, D0, E0,mprop; 
AutoDeclare Cfun topo; 
Cfun rat,Rat; 
S Pi, Nf; 
Cfun aGamma,Vel;
AutoDeclare s col;
AutoDeclare i mu, nu, rho, sigma, alpha, beta, gamma, eta, a, ap ,b,bp, i, j, k, m, l,c, cc;
Cfun eps,epsC,fpol, u, ub, v, vb,bos, ferB, fer, dTens, chain, epseps; 
Fun U,UB,V,VB, Gamma;
Cfun den, Gmn, deltas(symmetric), T,f(antisymmetric), SUND(symmetric), SUNFD(symmetric) , pair, fsub , SUNDsub,tempden;
Cfun Log, Sqrt, Li2, PolyLog , HeavisideTheta, Abs,Sign ; 
******** QGraf Needed ********
Cfun q, qin, qout, qB, qBin, qBout, top , topin, topout, topB, topBin, topBout, g, gin, gout, gh, ghB, Power; 
Cfun gprop, fprop, vx,ghprop, prop, gv,fgv,Pole; 
******** Higgs fields (for Higgs+QCD model) ********
Cfun h, hin, hout, hprop;
S lambdaGGH, mH, vev, yt, neps;
******** QGraf Needed ********

Cfun matubgv, matvbgu, matubgu, matvbgv, mass;
Set diracChain:  matubgv, matvbgu, matubgu, matvbgv; 
******** These are for color.prc   ********
Cfun Tr, Tp,MathCalLi2, Pent, ColorChain, casimir; 
S, TF, cA, cF, [cF- cA/6], NF, nf, a, pow, EulerGamma,[D-1],[D-2],[D-3],[D-4],[D-5],[D-6], I; 
******** These are for color.prc   ********

******* FeynCalc Conversion *******
Cfun SPD, FAD, FVD, FCFAD, Pair,LoopInt,GLI;
AutoDeclare v epsp, epsp1, epsp2;  
AutoDeclare S top;
******* FeynCalc Conversion *******
Set PaVeFun : A0, B0, C0, D0, E0;
Set RatFun : Log, Sqrt, Li2, PolyLog , HeavisideTheta, Abs,Sign;
Set Color : Tr,T,f,SUND,Tp;
********* Dirac Simplify 

*Fun Gamma, U, UB, V, VB,Commute;
AutoDeclare V E,Es;  
