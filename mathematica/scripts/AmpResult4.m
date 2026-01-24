(* ::Package:: *)

SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];
meta = Import["../meta.json", "RawJSON"];
Get["../../../mathematica/scripts/MultivariateApart.wl"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];
nmis = meta["nmis"];
name = meta["loop_main"];
amp = ToExpression[name];

Get/@FileNames["Files/M0M0/d*"];
ampTree = Sum[d[i,j]/. rat[a_,b_]:> a/b,{i, n0l},{j, n0l}];
Born = ampTree/. ep-> 0;
Sca[p_, q_] := N[p[[1]]*q[[1]] - p[[2]]*q[[2]] - p[[3]]*q[[3]] - p[[4]]*q[[4]], 16]
Sca[p_]:= N[Sca[p,p], 16]

(*MadGraph Generation Data for numerical comparison*)
If[(name === "qQtT1l")||(name === "ggtT1l"),

p1={5.0000000000000000*10^(02),0.0000000000000000*10^(00),0.0000000000000000*10^(00),5.0000000000000000*10^(02)};
p2={5.0000000000000000*10^(02),0.0000000000000000*10^(00),0.0000000000000000*10^(00),-5.0000000000000000*10^(02)};
p3={4.9999999999999989*10^(02),1.0407299191319960*10^(02),4.1735559881462342*10^(02),-1.8722744588420289*10^(02)};
p4={4.9999999999999989*10^(02),-1.0407299191319960*10^(02),-4.1735559881462342*10^(02),1.8722744588420281*10^(02)};
num = {ieps-> I * eps, s12-> Sca[p1+p2], s13-> Sca[p1-p3],s14-> Sca[p1-p4],mt-> Sqrt[Sca[p3,p3]], Mu-> 91188/1000, gs-> N[Sqrt[4 Pi *118/1000], 16], as-> 118/1000, eps-> 10^-12,nh->1, nl-> 5};
Clear[p1,p2,p3,p4];
Cons= Born*as/2/Pi/. as-> gs^2/4/Pi; 

If[name==="qQtT1l",

BornMG=6.1562818665255281*10^(-01);
FiniteMG =-3.7461123495145287*10;
SinglePoleMG=1.2181362611948710*10;
DoublePoleMG=-2.6666666666666661;
norm= 1/2/2/3/3;

, If[name ==="ggtT1l",

BornMG = 0.59262610090352241;
Cons = Born*as/2/Pi /. as -> gs^2/4/Pi; 
SinglePoleMG = 2.2317663363200069*10;
DoublePoleMG = -5.9999999999999991;
FiniteMG = -45.799703332980677; 
norm= 1/2/2/8/8;
]
]

];


1-Born/BornMG


Num[expr_]:= (expr/. nh-> 1/. nl-> 5/. ieps-> 10^-12)/.num;

Get["Files/Ioperator.m"]
Get/@FileNames["Files/Vas/d*"];
Vas = Sum[d[i, j]/. rat[a_,b_]:> a/b,{i, n0l},{j, n0l}];
Clear[d];
Get/@FileNames["Files/Vm/d*"];
Vm = Sum[d[i, j]/. rat[a_,b_]:> a/b,{i, n0l},{j, n0l}];
Clear[d];
Get/@FileNames["Files/Vg/d*"];
Vg = Sum[d[i, j]/. rat[a_,b_]:> a/b,{i, n0l},{j, n0l}];
Clear[d];
Get/@FileNames["Files/Vzt/d*"];
Vzt = Sum[d[i, j]/. rat[a_,b_]:> a/b,{i, n0l},{j, n0l}];
Clear[d];


IR = -Ioperator//. den[a_]:> 1/a/. Log[x_]:> Log[x/. den[a_]:> 1/a];
UV = Vas+Vzt+Vg+Vm;


rGamma = Gamma[1-ep]^2 Gamma[1+ep]/Gamma[1-2 ep];
betar[s_]:= Sqrt[1- 4 mt^2/s];
Fac = Exp[-EulerGamma ep]/rGamma;
xr[s_]:= ( betar[s]-1 )/(betar[s]+1);
x[s_]:= (1-betar[s])/(1+ betar[s]);
MathCalLi2[x_, y_]:= PolyLog[2, 1- x y] + Log[1- x y ] (Log[x y] - Log[x] - Log[y]);
lambdap[s_]:= 1/2 *(1 + betar[s]);
lambdam[s_]:= 1/2 *(1- betar[s]);

repA0 = {A0[mt^2]-> - Mu^(2 ep) Gamma[-1+ ep]/rGamma (mt^2 - I eps)^(1- ep)};
CzakonB0[s_,mt^2,mt^2]:= Module[{x},
x = (Sqrt[1- 4 mt^2/s]-1)/(Sqrt[1- 4 mt^2/s]+1); 

(1/ ep + 
2 - Log[mt^2/Mu^2] + (1+x)/(1-x) Log[x] + 
ep*( 
4- 2 Log[mt^2/Mu^2]+ 1/2 Log[mt^2/Mu^2]^2 + Zeta[2]/2 + (1+x)/(1-x) ((2- Log[mt^2/Mu^2] + 1/2 Log[x] - 2 Log[1+x])Log[x] - 2 PolyLog[2,-x] - Zeta[2])
)
)
]
repB0 = {
B0[s_, 0,0]:> (Mu^2/(-s- I eps))^ep(1/ep/(1-2 ep)),
B0[mt^2, 0, mt^2]:> Gamma[1+ ep]/rGamma (Mu^2/mt^2)^ep (1/ep/(1-2 ep)), 
B0[s_, 0, mt^2]:> ReplaceAll[
                (Mu^2/mt^2)^ep (
                1/ ep 	
				+ 2+ (mt^2-s)/s Log[(mt^2-s)/mt^2]
				+ ep (Pi^2/6 + 4 +(mt^2-s)/2/s ( 4 Log[(mt^2-s)/mt^2]- Log[(mt^2-s)/mt^2]^2 + 2 PolyLog[2, -s/(mt^2-s)]))
											), s-> s+ I eps], 
B0[s_, mt^2, mt^2]:> Fac * CzakonB0[s,mt^2,mt^2]

};

repD0= {
D0[0,0, mt^2, mt^2, s12_, s23_, 0,0,0,mt^2]:> (*rGamma*)- 1/s12/(mt^2-s23)*(Mu^2/mt^2)^ep*
ReplaceAll[
(2/ep^2- 
1/ep *(2 Log[(mt^2-s23)/mt^2] + Log[-s12/mt^2])+
 2 Log[(mt^2-s23)/mt^2]*Log[-s12/mt^2] - Pi^2/2

)
, {s12 -> s12+ I eps, s23-> s23+ I eps}], 

D0[0, mt^2, 0, mt^2, s12_, s23_, 0,0,mt^2, mt^2]:> 1/(mt^2-s23)/(mt^2-s12)(Mu^2/mt^2)^ep*
ReplaceAll[(
1/ep^2
- 1/ep (Log[(mt^2-s23)/mt^2] + Log[(mt^2-s12)/mt^2])
+ 2 Log[(mt^2-s23)/mt^2]Log[(mt^2-s12)/mt^2]- Pi^2/2
)
, {s12-> s12+ I eps, s23 -> s23 + I eps}], 

D0[0,0,mt^2, mt^2,s_, t_ , mt^2, mt^2, mt^2, 0]:> (1/s/(t- mt^2)/betar[s]*(Mu^2/mt^2)^ep*
ReplaceAll[(
1/ep * Log[(betar[s]-1)/(betar[s]+1)] - Log[(betar[s]-1)/(betar[s]+1)]*(
2 Log[(mt^2-t)/mt^2]- Log[-s/mt^2])
+ 2 PolyLog[2, -lambdam[s]/lambdap[s]]+ 2 PolyLog[2, -lambdam[s]/betar[s]]+ Log[-betar[s]/lambdam[s]]^2 - Pi^2/2

), {s-> s+ I eps, t-> t+ I eps, mt^2-> mt^2-I eps}])


};

repC0 = {
C0[0,0, s_, 0,0,0]:> Mu^(2 ep)/ep^2 *((-s-I eps)^(- ep)/s), 
C0[0, mt^2, p2sq_, 0,0, mt^2]:> (Mu^2/mt^2)^ep/(p2sq - mt^2)*(
1/2/ep^2 +

1/ep Log[mt^2/(mt^2- p2sq)] + Pi^2/12 + 1/2 Log[mt^2/(mt^2-p2sq)]^2 
- PolyLog[2, -p2sq/(mt^2 - p2sq)]
),


C0[mt^2,mt^2,s_,mt^2,0,mt^2]:> (1- 2 ep)/ep (B0[s, mt^2, mt^2]- B0[mt^2, 0, mt^2])/(s- 4 mt^2)/. repB0, 


C0[mt^2, mt^2, s_, 0, mt^2, 0]:> 1/s/betar[s] (2 Pi^2/3 + 2 PolyLog[2, -lambdam[s]/lambdap[s]]+ 1/2 Log[-lambdam[s]/lambdap[s]]^2),

C0[0, mt^2, s_, mt^2, mt^2, 0]:> (-1/6*(Pi^2 + 3*Log[mt^2/(mt^2 - s)]^2 + 6*PolyLog[2, -(s/(mt^2 - s))])/
  (mt^2 - s)),
  
  C0[0,s_,0,mt^2,mt^2,mt^2]:> (Log[(2*mt^2 - s + Sqrt[s*(-4*mt^2 + s)])/(2*mt^2)]^2/(2*s))

};
Symmetries = {B0[mt^2, mt^2, 0]-> B0[mt^2, 0, mt^2],B0[0, mt^2, mt^2]-> Simplify[B0[mt^2, 0, mt^2]*(1-2 ep)],C0[0 , s_, 0, 0,0,0]:> C0[0, 0, s , 0,0,0], 
C0[mt^2, t_, 0,0, mt^2, 0]:> C0[0, mt^2, t, 0,0, mt^2], C0[mt^2,s12_,mt^2,mt^2,0,0]:> C0[mt^2, mt^2, s12, 0, mt^2, 0],
D0[0, mt^2, mt^2, 0, t_, s_, 0, 0, mt^2, 0]:> D0[0, 0, mt^2, mt^2, s, t, 0,0,0, mt^2], C0[mt^2, t_, 0, mt^2, 0, mt^2]:> C0[0, mt^2, t, mt^2, mt^2, 0], 
D0[0, mt^2, 0, mt^2, t_, s_, mt^2, mt^2, 0, 0]:> D0[0,mt^2, 0,mt^2, s, t, 0,0, mt^2, mt^2], 
D0[0, mt^2, mt^2, 0, t_, s_, mt^2, mt^2, 0, mt^2]:> D0[0,0, mt^2 , mt^2, s, t, mt^2, mt^2, mt^2, 0],C0[0,s13_,mt^2,mt^2,mt^2,0]:>  C0[0, mt^2, s13, mt^2, mt^2, 0],
C0[0,0,s12_,mt^2,mt^2,mt^2]:>  C0[0,s12,0,mt^2,mt^2,mt^2]
}; 




Get["Files/MasterCoefficients.m"]


Poles[-2] = (amp*I/16/Pi^2*2/. RatFun/. (h:A0|B0|D0)[x__]:> (h[x]/. Symmetries/. repA0/. repB0/.repD0// Series[#/. eps-> 0,{ep, 0,0}]&// Normal)// SeriesCoefficient[#, {ep, 0,-2}]&// Normal// Total// MultivariatePassToSingular)/ep^2/. den[a_]:> 1/a;


Poles[-1] = ((amp*I/16/Pi^2*2/. RatFun/. (h:A0|B0|D0)[x__]:> (h[x]/. Symmetries/. repA0/. repB0/.repD0// Series[#/. eps-> 0,{ep, 0,0}]&// Normal)// SeriesCoefficient[#, {ep, 0,-1}]&// Normal)/. Log[a_]:> Log[a// Together]/. Log[a_]:> If[(a/.num)> 0, Log[a], Log[-a]]/. Log[Mu]-> Log[Mu^2]/2/. Log[Mu^2/s12_]->Log[Mu^2]- Log[s12] /. Log[Mu^2/s12_^2]->Log[Mu^2]- Log[s12^2] /. Log[a_/mt^2]:> Log[a]-Log[mt^2]/. Log[mt^2/Mu^2]-> Log[mt^2]-Log[Mu^2]/. Log[a_]:> Log[a/mt^2]+ Log[mt^2]// Total)/ep;


1-(Born*norm)/BornMG/.num


(Poles[-2]/. den[a_]:> 1/a// Together)+ Coefficient[IR, ep,-2]/ep^2// Together


1- ((Total[amp]*I*2/16/Pi^2+IR+UV/.Symmetries/. repA0/.repB0/. repC0/. repD0/. RatFun/.num// Series[#, {ep, 0,0}]&// Normal//Collect[#, {ep},Re]&)/Cons/.num// Expand)/FiniteMG// Expand
