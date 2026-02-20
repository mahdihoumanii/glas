(* ::Package:: *)

<<FeynCalc`


SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];

(* -------- Load meta.json -------- *)
meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
nout = meta["n_out"];
n = meta["n_in"] + meta["n_out"];
modelId = Lookup[meta, "model_id", "qcd_massive"];
moms = ToExpression /@ parts[[All, "momentum"]];
incoming = ToExpression /@ (Select[parts, #["side"] == "in" &][[All, "momentum"]]);
outgoing = ToExpression /@ (Select[parts, #["side"] == "out" &][[All, "momentum"]]);
masses = If[modelId === "qcd_massless",
  ConstantArray[0, Length[parts]],
  (If[StringContainsQ[#["token"], "t"], mt, 0] &) /@ parts
];

maxMom = ToExpression["p" <> ToString[n]];
If[MemberQ[outgoing, maxMom],
  momconservation = {maxMom -> Total[incoming] - Total[DeleteCases[outgoing, maxMom]]},
  momconservation = {maxMom -> Total[outgoing] - Total[DeleteCases[incoming, maxMom]]}
];


FCClearScalarProducts[];
P[mu_]:= FVD[p, mu];
P2[mu_]:= FVD[p2, mu];
P3[mu_]:= FVD[p3, mu];
KT[mu_]:=  lambda* FVD[kt, mu];
SPD[kt, kt] = ktsq; 
SPD[p, kt]= 0; 
SPD[p2, kt] = 0; 
SPD[p,p]=0;
SPD[p2,p2]=0;
P1[mu_]:=x*P[mu]+ KT[mu] - Contract[KT[mu]^2]/(x)/2/(SPD[p, p2]) *P2[mu];
P5[mu_]:=-((1-x)*P[mu]- KT[mu] - Contract[KT[mu]^2]/(1-x)/2/(SPD[p, p2]) *P2[mu]);
 P4[mu_]:= P1[mu]+P2[mu]-P3[mu]-P5[mu];
SPD[kt, p3]= kt3;
SetMandelstam[s,t, u, p,p2,-p3,-p4,0,0,masses[[3]],masses[[4]]];
mandrep = {s14 -> 2*mt^2 - s12 - s13};
Sudakov15 = ReplaceAll[{s15->Together[Contract[(P1[mu]-P5[mu])^2]],s12->Together[Contract[(P1[mu]+P2[mu])^2]],s23->Together[Contract[(P2[mu]-P3[mu])^2]],s34->Together[Contract[(P3[mu]+P4[mu])^2]], s45->Together[Contract[(P4[mu]+P5[mu])^2]]},{u-> 2mt^2-s-t}]// Together// FullSimplify;


FCClearScalarProducts[];
P[mu_]:= FVD[p, mu];
P1[mu_]:= FVD[p1, mu];
P3[mu_]:= FVD[p3, mu];
KT[mu_]:=  lambda* FVD[kt, mu];
SPD[kt, kt] = ktsq; 
SPD[p, kt]= 0; 
SPD[p1, kt] = 0; 
SPD[p,p]=0;
SPD[p1,p1]=0;
P2[mu_]:=x*P[mu]+ KT[mu] - Contract[KT[mu]^2]/(x)/2/(SPD[p, p1]) *P1[mu];
P5[mu_]:=-((1-x)*P[mu]- KT[mu] - Contract[KT[mu]^2]/(1-x)/2/(SPD[p, p1]) *P1[mu]);
 P4[mu_]:= P1[mu]+P2[mu]-P3[mu]-P5[mu];
SPD[kt, p3]= kt3;
SetMandelstam[s,t, u, p,p2,-p3,-p4,0,0,masses[[3]],masses[[4]]];
Sudakov25 = ReplaceAll[{s15->Together[Contract[(P1[mu]-P5[mu])^2]],s12->Together[Contract[(P1[mu]+P2[mu])^2]],s23->Together[Contract[(P2[mu]-P3[mu])^2]],s34->Together[Contract[(P3[mu]+P4[mu])^2]], s45->Together[Contract[(P4[mu]+P5[mu])^2]]},{u-> 2mt^2-s-t}]// Together// FullSimplify;


file = OpenWrite["Files/Sudakov.m"];
WriteString[file, "Sudakov[1,5] = " , ToString[Sudakov15,InputForm],";\n"];
WriteString[file, "Sudakov[2,5] = " , ToString[Sudakov25,InputForm],";\n"];
Close[file];
