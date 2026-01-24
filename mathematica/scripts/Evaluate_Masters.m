(* ::Package:: *)

SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];


rGamma = Gamma[1-ep]^2Gamma[1+ep]/Gamma[1-2 ep];
betar[s_]:= Sqrt[1- 4 mt^2/s]
Fac = Exp[-EulerGamma ep]/rGamma;
xr[s_]:= ( betar[s]-1 )/(betar[s]+1)
x[s_]:= (1-betar[s])/(1+ betar[s])
MathCalLi2[x_, y_]:= PolyLog[2, 1- x y] + Log[1- x y ] (Log[x y] - Log[x] - Log[y])
lambdap[s_]:= 1/2 *(1 + betar[s])
lambdam[s_]:= 1/2 *(1- betar[s])
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



repD0= {
D0[0,0, mt^2, mt^2, s12_, s23_, 0,0,0,mt^2]:> (*rGamma*)- 1/s12/(mt^2-s23)*(Mu^2/mt^2)^ep*
ReplaceAll[
(2/ep^2- 
1/ep *(2 Log[(mt^2-s23)/mt^2] + Log[-s12/mt^2])+
 2 Log[(mt^2-s23)/mt^2]*Log[-s12/mt^2] - Pi^2/2

)
, {s12 -> s12+ I eps, s23-> s23+ I eps}], 

D0[0, mt^2, 0, mt^2, s12_, s23_, 0,0,mt^2, mt^2]:> 1/(mt^2-s23)/(mt^2-s12)(Mu^2/mt^2)^ep
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


Symmetries = {B0[mt^2, mt^2, 0]-> B0[mt^2, 0, mt^2],B0[0, mt^2, mt^2]-> Simplify[B0[mt^2, 0, mt^2]*(1-2 ep)],C0[0 , s_, 0, 0,0,0]:> C0[0, 0, s , 0,0,0], 
C0[mt^2, t_, 0,0, mt^2, 0]:> C0[0, mt^2, t, 0,0, mt^2], 
D0[0, mt^2, mt^2, 0, t_, s_, 0, 0, mt^2, 0]:> D0[0, 0, mt^2, mt^2, s, t, 0,0,0, mt^2], C0[mt^2, t_, 0, mt^2, 0, mt^2]:> C0[0, mt^2, t, mt^2, mt^2, 0], 
D0[0, mt^2, 0, mt^2, t_, s_, mt^2, mt^2, 0, 0]:> D0[0,mt^2, 0,mt^2, s, t, 0,0, mt^2, mt^2], 
D0[0, mt^2, mt^2, 0, t_, s_, mt^2, mt^2, 0, mt^2]:> D0[0,0, mt^2 , mt^2, s, t, mt^2, mt^2, mt^2, 0]
}; 


QCDLoopIntegrals[expr_] := expr /. Symmetries/. repA0/. repB0/. repC0/. repD0
