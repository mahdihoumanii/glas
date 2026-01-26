(* ::Package:: *)

SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];
meta = Import["../meta.json", "RawJSON"];
Get["../../../mathematica/scripts/MultivariateApart.wl"];
Get["Files/SymmetryRelations.m"]
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
If[(name === "qQtTg1l")||(name === "ggtTg1l"),

p1={5.0000000000000000*10^(02),0.0000000000000000*10^(00),0.0000000000000000*10^(00),5.0000000000000000*10^(02)};
p2={5.0000000000000000*10^(02),0.0000000000000000*10^(00),0.0000000000000000*10^(00),-5.0000000000000000*10^(02)};
p3={4.5775889887874399*10^(02),1.5660521144032271*10^(02),3.5086817420874218*10^(02),-1.7883104199169600*10^(02)};
p4={3.7833360363100792*10^(02),-1.6940091495976191*10^(01),-3.2134122637100819*10^(02),9.8286139261388087*10^(01)};
p5={1.6390749749024820*10^(02),-1.3966511994434649*10^(02),-2.9526947837733989*10^(01),8.0544902730307925*10^(01)};
num = {ieps-> I * eps, s12-> Sca[p1+p2], s23-> Sca[p2-p3],s34-> Sca[p3+p4], s45-> Sca[p4+p5], s15-> Sca[p1-p5] ,mt-> Sqrt[Sca[p3,p3]], Mu-> 91188/1000, gs-> N[Sqrt[4 Pi *118/1000], 16], as-> 118/1000, eps-> 10^-12};
Clear[p1,p2,p3,p4,p5];
Cons= Born*as/2/Pi/. as-> gs^2/4/Pi; 

If[name==="qQtTg1l",

BornMG=2.3024810939795129*10^(-04);
FiniteMG = -2.8098922527558599*10^(+01);
SinglePoleMG=1.1956188459326690*10^(+01);
DoublePoleMG=-5.6666666666666510;
norm= 1/2/2/3/3;

, If[name ==="ggtTg1l",

BornMG = 0.59262610090352241;
Cons = Born*as/2/Pi /. as -> gs^2/4/Pi; 
SinglePoleMG = 2.2317663363200069*10;
DoublePoleMG = -5.9999999999999991;
FiniteMG = -45.799703332980677; 
norm= 1/2/2/8/8;
]
]

];


1-Born/BornMG*norm/.num


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
(*MathCalLi2[x_, y_]:= PolyLog[2, 1- x y] + Log[1- x y ] (Log[x y] - Log[x] - Log[y])*)
ContinuedDiLogReplace[expr_]:= expr /. MathCalLi2[x_,y_]:>  PolyLog[2, 1- x y] + Log[1- x y ] (Log[x y] - Log[x] - Log[y])
KallenExpand[expr_]:= expr /. Kallen[a_,b_,c_] :>  a^2-2 a b+b^2-2 a c-2 b c+c^2


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



Symmetries = {B0[mt^2, mt^2, 0]-> B0[mt^2, 0, mt^2],B0[0, mt^2, mt^2]-> Simplify[B0[mt^2, 0, mt^2]*(1-2 ep)],C0[0 , s_, 0, 0,0,0]:> C0[0, 0, s , 0,0,0], 
C0[mt^2, t_, 0,0, mt^2, 0]:> C0[0, mt^2, t, 0,0, mt^2], C0[mt^2,s12_,mt^2,mt^2,0,0]:> C0[mt^2, mt^2, s12, 0, mt^2, 0],
D0[0, mt^2, mt^2, 0, t_, s_, 0, 0, mt^2, 0]:> D0[0, 0, mt^2, mt^2, s, t, 0,0,0, mt^2], C0[mt^2, t_, 0, mt^2, 0, mt^2]:> C0[0, mt^2, t, mt^2, mt^2, 0], 
D0[0, mt^2, 0, mt^2, t_, s_, mt^2, mt^2, 0, 0]:> D0[0,mt^2, 0,mt^2, s, t, 0,0, mt^2, mt^2], 
D0[0, mt^2, mt^2, 0, t_, s_, mt^2, mt^2, 0, mt^2]:> D0[0,0, mt^2 , mt^2, s, t, mt^2, mt^2, mt^2, 0],C0[0,s13_,mt^2,mt^2,mt^2,0]:>  C0[0, mt^2, s13, mt^2, mt^2, 0],
C0[0,0,s12_,mt^2,mt^2,mt^2]:>  C0[0,s12,0,mt^2,mt^2,mt^2]
}; 


Symmetries = {C0[0 , s_, 0, 0,0,0]:> C0[0, 0, s , 0,0,0],D0[0, mt^2, mt^2, p3sq_, s12_, s23_, 0,0,mt^2, 0]:>  D0[0, p3sq, mt^2, mt^2, s23, s12, 0,0,0,mt^2], 
D0[0, mt^2, mt^2, psq_, s12_, s23_, mt^2, mt^2, 0, mt^2]:>  D0[mt^2, 0, psq, mt^2,s12,s23, 0, mt^2, mt^2, mt^2],  
D0[0, mt^2, 0, s_, s12_, s23_, mt^2, mt^2, 0,0]:> D0[0, mt^2, 0, s, s23, s12, 0, 0, mt^2, mt^2], C0[mt^2,s_, 0, 0, mt^2, 0] :> C0[0, mt^2, s, 0,0,mt^2],C0[0,s_, mt^2,0,0,mt^2] :>  C0[0,mt^2,s,0,0,mt^2] , 
C0[mt^2,mt^2,s_,mt^2,0,mt^2] :> C0[mt^2,s, mt^2, 0, mt^2, mt^2]
}; 


repD0 = { 
D0[0,0,0,0, s12_, s23_, 0,0,0,0]:> (*rGamma*) Mu^(2 ep) /s12/s23 ( 2/ ep^2 (( -s12 - I eps)^(- ep) + (-s23 - I eps)^(- ep))
																		- Log[(-s12 - I eps)/(-s23 - I eps)]^2 - Pi^2 ), 




D0[0,0,0, p4sq_, s12_, s23_, 0,0,0,0]:> (*rGamma*) Mu^(2 ep)/s12/s23  * ( 
2/ep^2 ((-s12- I eps)^(- ep) + (-s23- I eps)^(- ep) - (-p4sq - I eps)^(- ep))
- 2 PolyLog[2, 1- (p4sq+ I eps)/(s12+ I eps)] - 2 PolyLog[2, 1- (p4sq+ I eps)/(s23+ I eps)] - Log[(-s12- I eps)/(-s23- I eps)]^2- Pi^2/3 
),




D0[0,0,mt^2, p4sq_, s12_, s23_, 0,0,0, mt^2]:> (Mu^2/mt^2)^ep * (*rGamma*)1 /s12/(s23- mt^2) *(

3/2 1/ep^2 - 
1/ep ( 2 Log[1- (s23+I eps)/mt^2] + Log[-(s12+ I eps)/ mt^2] - Log[1- (p4sq+ I eps)/ mt^2])- 
2 PolyLog[2, (s23 - p4sq)/ (s23+ I eps- mt^2)] + 2 Log[-(s12+ I eps)/mt^2] Log[1- (s23+ I eps)/mt^2] - Log[1- (p4sq+ I eps)/mt^2]^2 - 5 Pi^2/12

)
, 




D0[0, mt^2, p3sq_, mt^2, s12_, s23_, 0,0, mt^2, mt^2]:> 
(Mu^2/mt^2)^ep /(s12- mt^2)/(s23- mt^2)* 
(
1/ep^2 - 

1/ep ( Log[1- (s23+ I eps)/mt^2] + Log[1-(+I eps+ s12)/mt^2])- Log[xr[p3sq+ I eps]]^2 + 

2 Log[1- (s12+ I eps)/mt^2] Log[1- (s23+I eps)/mt^2] - Pi^2/2
)

,
D0[0, p2sq_, p3sq_, mt^2, s12_, s23_, 0, 0, 0, mt^2] :> 
  (*rGamma*)1/(s12 (s23 - mt^2)) * (
    1/(2 ep^2)
    - (1/ep) * Log[((s12+ I eps)/(p2sq+ I eps)) * ((mt^2 - (s23+ I eps))/(Mu mt))]
    + PolyLog[2, 1 + ((mt^2 - (p3sq+ I eps)) (mt^2 - (s23+ I eps)))/(mt^2 (p2sq+ I eps))]
    + 2 PolyLog[2, 1 - (s12+ I eps)/(p2sq+ I eps)]
    + Pi^2/12
    + Log[((s12+ I eps)/(p2sq+ I eps)) * ((mt^2 - s23- I eps)/(Mu mt))]^2  
  ), 
 
 
  D0[0, mt^2, 0, p4sq_, s12_, s23_, 0, 0, mt^2, mt^2] :> 

  (Mu^2/mt^2)^ep * (1/((s12 - mt^2) (s23 - mt^2))) * (
    1/(2 ep^2)
    - (1/ep) * (
      Log[1 - (s12+ I eps)/mt^2]
      + Log[1 - (s23+ I eps)/mt^2]
      - Log[1 - (p4sq+I eps)/mt^2]
    )
    - 2 PolyLog[2, (s23 - p4sq)/(s23+ I eps - mt^2)]
    - 2 PolyLog[2, (s12 - p4sq)/(s12 + I eps- mt^2)]
    + 2 Log[1 - (s12+ I eps)/mt^2] * Log[1 - (s23+ I eps)/mt^2]
    - Log[1 - (p4sq+ I eps)/mt^2]^2
    - Pi^2/12
  )
 , 
 
 
 
 D0[mt^2, 0, p3sq_, mt^2, s12_, s23_, 0, mt^2, mt^2, mt^2] :> 

 ( (Mu^2/mt^2)^ep/ (s12- mt^2)/s23 /betar[s23+ I eps] * 
  
  ( 1/ep Log[xr[s23+ I eps]] 
  
  - 2 Sum[MathCalLi2[xr[s23+ I eps], xr[p3sq+ I eps]^rho], {rho, {-1,1}}]
  
  - PolyLog[2, xr[s23+ I eps]^2] -  2 Log[xr[s23+ I eps]] Log[1- xr[s23+ I eps]^2]
  
  - 2 Log[xr[s23+ I eps]]Log[1- (s12+ I eps)/mt^2] - Log[xr[p3sq+ I eps]]^2 + Pi^2/6
  
  
  )/. eps-> 0)

 
 

};
repC0 = {
C0[0,0, s_, 0,0,0]:> Mu^(2 ep)/ep^2 ((-s-I eps)^(- ep)/s)

,
 C0[mt^2,s_, mt^2, 0, mt^2, mt^2]:> ReplaceAll[-((Sqrt[-((4*mt^2 - s)*s)]*Log[(2*mt^2 - s + Sqrt[s*(-4*mt^2 + s)])/(2*mt^2)])/(ep*(4*mt^2 - s)*s)) + 
 (Sqrt[-((4*mt^2 - s)*s)]*(Pi^2 - 3*Log[(2*mt^2 - s + Sqrt[s*(-4*mt^2 + s)])/(2*mt^2)]*Log[-1/2*(mt^2*(-2*mt^2 + s + Sqrt[s*(-4*mt^2 + s)]))/(-4*mt^2 + s)^2] - 
    6*Log[(2*mt^2 - s + Sqrt[s*(-4*mt^2 + s)])/(2*mt^2)]*Log[Mu^2/mt^2] + 12*PolyLog[2, (-2*mt^2 + s - Sqrt[s*(-4*mt^2 + s)])/(2*mt^2)]))/(6*(4*mt^2 - s)*s), s-> s + I eps]
,
C0[0, mt^2, p2sq_, 0,0,mt^2]:> ReplaceAll[
(Mu^2/mt^2)^ep /(p2sq - mt^2) * (
1/2/ep^2 + 

1/ep Log[mt^2/(mt^2-p2sq)] + 

Pi^2/12 + 1/2 Log[mt^2/(mt^2 -p2sq)]^2 - PolyLog[2, -p2sq/(mt^2-p2sq)]

)

, {p2sq ->  p2sq + I eps}]


};
repScalarIntegrals= {

C0[mt^2, mt^2, s12_, 0, mt^2, 0]:> ReplaceAll[(4*Pi^2 + 3*Log[1 + ((-1 + Sqrt[1 - (4*mt^2)/s12])*s12)/(2*mt^2)]^2 + 12*PolyLog[2, 1 + ((-1 + Sqrt[1 - (4*mt^2)/s12])*s12)/(2*mt^2)])/(6*s12*Sqrt[(-4*mt^2 + s12)/s12]), {s12-> s12+ I eps}],

C0[0, s12_,s23_, mt^2, mt^2, 0] :> ReplaceAll[((Log[-(mt^2/s12)]^2 - Log[-(mt^2/s23)]^2 + 2*PolyLog[2, mt^2/s12] - 2*PolyLog[2, mt^2/s23])/(2*(s12 - s23))), {s12-> s12+ I eps, s23 -> s23 + I eps }], 

 C0[0, s12_, s23_, mt^2, mt^2, mt^2]:> ReplaceAll[((Log[(2*mt^2 - s12 + Sqrt[s12*(-4*mt^2 + s12)])/(2*mt^2)] - Log[(2*mt^2 - s23 + Sqrt[s23*(-4*mt^2 + s23)])/(2*mt^2)])*
  (Log[(2*mt^2 - s12 + Sqrt[s12*(-4*mt^2 + s12)])/(2*mt^2)] + Log[(2*mt^2 - s23 + Sqrt[s23*(-4*mt^2 + s23)])/(2*mt^2)]))/(2*(s12 - s23)), {s12-> s12+ I eps, s23 -> s23 + I eps }],

  D0[0, mt^2, p3sq_, mt^2, s12_, s23_, mt^2, mt^2, 0, 0]:> 1/2 (-((-2 Log[(-mt^2+s12)/p3sq] Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23+Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]+2 Log[mt^2/(mt^2-s23)] Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23+Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]-Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23+Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]^2-4 PolyLog[2,-((mt^4+s12 s23-mt^2 (s12+s23)+Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq))])/(Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+4 mt^2 p3sq-mt^2 s12-mt^2 s23+s12 s23]))+(-2 Log[(-mt^2+s12)/p3sq] Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23-Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]+2 Log[mt^2/(mt^2-s23)] Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23-Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]-Log[(mt^4+mt^2 (2 p3sq-s12-s23)+s12 s23-Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)]^2-4 PolyLog[2,(-mt^4-s12 s23+mt^2 (s12+s23)+Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+mt^2 (4 p3sq-s12-s23)+s12 s23])/(2 mt^2 p3sq)])/(Sqrt[mt^2-s12] Sqrt[mt^2-s23] Sqrt[mt^4+4 mt^2 p3sq-mt^2 s12-mt^2 s23+s12 s23]))
 ,
C0[mt^2, s12_, s23_, 0, mt^2, mt^2]  :> -(\[Pi]^2/(6 Sqrt[Kallen[mt^2,s12,s23]]))-Log[(mt^2-s23)/Sqrt[Kallen[mt^2,s12,s23]]]^2/(2 Sqrt[Kallen[mt^2,s12,s23]])+PolyLog[2,-((-2 mt^2 (mt^2-s23)+2 mt^2 Sqrt[Kallen[mt^2,s12,s23]])/(2 mt^2 (mt^2-s23)))]/Sqrt[Kallen[mt^2,s12,s23]]-PolyLog[2,(-s12 (-3 mt^2+s12-s23)-s12 Sqrt[Kallen[mt^2,s12,s23]])/(s12 (3 mt^2-s12+s23)-Sqrt[s12 (-4 mt^2+s12)] Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]+PolyLog[2,(-s12 (-3 mt^2+s12-s23)+s12 Sqrt[Kallen[mt^2,s12,s23]])/(s12 (3 mt^2-s12+s23)-Sqrt[s12 (-4 mt^2+s12)] Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]-PolyLog[2,(-s12 (-3 mt^2+s12-s23)-s12 Sqrt[Kallen[mt^2,s12,s23]])/(s12 (3 mt^2-s12+s23)+Sqrt[s12 (-4 mt^2+s12)] Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]+PolyLog[2,(-s12 (-3 mt^2+s12-s23)+s12 Sqrt[Kallen[mt^2,s12,s23]])/(s12 (3 mt^2-s12+s23)+Sqrt[s12 (-4 mt^2+s12)] Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]-PolyLog[2,((mt^2-s23) (mt^2-s12+s23)+(-mt^2-s23) Sqrt[Kallen[mt^2,s12,s23]])/((mt^2-s23) (mt^2-s12+s23)+(mt^2-s23) Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]-PolyLog[2,((mt^2-s23) (mt^2-s12+s23)+(-mt^2-s23) Sqrt[Kallen[mt^2,s12,s23]])/((mt^2-s23) (mt^2-s12+s23)+(-mt^2+s23) Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]+PolyLog[2,((mt^2-s23) (mt^2-s12+s23)+(-mt^2+s23) Sqrt[Kallen[mt^2,s12,s23]])/((mt^2-s23) (mt^2-s12+s23)+(mt^2-s23) Sqrt[Kallen[mt^2,s12,s23]])]/Sqrt[Kallen[mt^2,s12,s23]]-PolyLog[2,(-mt^2+s23+Sqrt[Kallen[mt^2,s12,s23]])/Sqrt[Kallen[mt^2,s12,s23]]]/Sqrt[Kallen[mt^2,s12,s23]],
  C0[mt^2,s12_,s45_,mt^2,0,0]:> (\[Pi]^2/(6 Sqrt[Kallen[mt^2,s12,s45]])+Log[s12/Sqrt[Kallen[mt^2,s12,s45]]]^2/(2 Sqrt[Kallen[mt^2,s12,s45]])-PolyLog[2,(2 mt^2 s12-2 mt^2 Sqrt[Kallen[mt^2,s12,s45]])/(2 mt^2 s12)]/Sqrt[Kallen[mt^2,s12,s45]]-PolyLog[2,(-s12 (mt^2+s12-s45)-s12 Sqrt[Kallen[mt^2,s12,s45]])/(-s12 (mt^2+s12-s45)+s12 Sqrt[Kallen[mt^2,s12,s45]])]/Sqrt[Kallen[mt^2,s12,s45]]+PolyLog[2,(-s12 (mt^2+s12-s45)+s12 Sqrt[Kallen[mt^2,s12,s45]])/(-s12 (mt^2+s12-s45)-s12 Sqrt[Kallen[mt^2,s12,s45]])]/Sqrt[Kallen[mt^2,s12,s45]]-PolyLog[2,(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(mt^2-s45) Sqrt[Kallen[mt^2,s12,s45]])/(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(-mt^2+s45) Sqrt[Kallen[mt^2,s12,s45]])]/Sqrt[Kallen[mt^2,s12,s45]]+PolyLog[2,(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(mt^2+s45) Sqrt[Kallen[mt^2,s12,s45]])/(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(mt^2-s45) Sqrt[Kallen[mt^2,s12,s45]])]/Sqrt[Kallen[mt^2,s12,s45]]+PolyLog[2,(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(mt^2+s45) Sqrt[Kallen[mt^2,s12,s45]])/(-mt^4+mt^2 s12+2 mt^2 s45+s12 s45-s45^2+(-mt^2+s45) Sqrt[Kallen[mt^2,s12,s45]])]/Sqrt[Kallen[mt^2,s12,s45]]+PolyLog[2,(-s12+Sqrt[Kallen[mt^2,s12,s45]])/Sqrt[Kallen[mt^2,s12,s45]]]/Sqrt[Kallen[mt^2,s12,s45]])
 
  };


MasterNum = Thread[Rule[MastersPaVe, MastersPaVe/. (h:A0|B0)[x__]:> Normal[Series[h[x]/. Symmetries/. repA0/. repB0/.num,{ep, 0,1}]]/. PaVeRules/. pentRep/. (h:C0|D0)[x__]:> Normal[Series[h[x]/. PaVeRules/. pentRep/. repD0/. Symmetries/. repScalarIntegrals/. repC0/. repD0/. num// KallenExpand// ContinuedDiLogReplace, {ep, 0,0}]]/.num]];


Monitor[Do[
Get["Files/MasterCoefficients/mi"<>ToString[i]<>"/MasterCoefficient"<>ToString[i]<>".m"];
Coefnum[i] = coef[i]*2*I/16/Pi^2/. GLI[a_,b__]:> GLI[a,{b}]/. MasterNum/.num/. den[a_]:> 1/a/. rat[a_,b_]:> a/b/. nl-> 5/. nh->1// Expand// Series[#, {ep, 0,0}]&// Normal;
,{i, 1,nmis}],i]


1-((Sum[Coefnum[i],{i,  nmis}]+IR+UV)/Cons/.num/.nl->5/. nh-> 1// Expand// Series[#, {ep, 0,0}]&// Normal// Collect[#, {ep},Re]&)/FiniteMG// Expand
