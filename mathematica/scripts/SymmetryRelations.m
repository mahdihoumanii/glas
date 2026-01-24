SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];

<<FeynCalc`
Get["Files/integrals.m"]
(* -------- Load meta.json -------- *)
meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];

moms = ToExpression /@ parts[[All, "momentum"]];
incoming = ToExpression /@ (Select[parts, #["side"] == "in" &][[All, "momentum"]]);
outgoing = ToExpression /@ (Select[parts, #["side"] == "out" &][[All, "momentum"]]);
masses = (If[StringContainsQ[#["token"], "t"], mt, 0] &) /@ parts;

maxMom = ToExpression["p" <> ToString[n]];
If[MemberQ[outgoing, maxMom],
  momconservation = {maxMom -> Total[incoming] - Total[DeleteCases[outgoing, maxMom]]},
  momconservation = {maxMom -> Total[outgoing] - Total[DeleteCases[incoming, maxMom]]}
];


If[n == 4,
  SetMandelstam[s12, s13, s14, Sequence @@ Join[incoming, -outgoing], Sequence @@ masses];
  mandrep = {s14 -> 2*mt^2 - s12 - s13};
  mandRep[expr_]:= expr//. mandrep;
  ,
  If[n == 5,
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {mand[1,2] -> s12, mand[2,3] -> s23, mand[3,4] -> s34, mand[4,5] -> s45, mand[1,5] -> s15};
    mandRep[expr_]:= expr//. mandrep;
    ,
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {};
  ]
];


Monitor[Do[Get["Files/IBP/IBP"<>ToString[i]<>".m"],{i, Length[Topologies]}],i]

MastersBL = Table[
     If[IBP[i][[1]] === {}, {} // Cases[#, BL[__], Infinity] & // DeleteDuplicates,
      IBP[i][[All, 2]] // Cases[#, BL[__], Infinity] & // 
       DeleteDuplicates], {i, Length[Topologies]}] // Flatten // 
DeleteDuplicates;

PaVemis=Monitor[ Table[((MastersBL[[i]]/. BL[a_,{1,1,1,1,1}]:> GLI[a,{1,1,1,1,1}]/.  BL[a_,b_]:>TID[ FCLoopFromGLI[GLI[ToString[a],b],Topologies], {l},ToPaVe-> True]/I/Pi^2))/. mandrep, {i, Length[MastersBL]}],i];

PaVeRules = Thread[Rule[MastersBL, PaVemis]];

pents =(Cases[PaVemis, GLI[__], Infinity]);

pents =(Cases[PaVemis, GLI[__], Infinity]);
pentfam = Table[pents[[i]][[1]]// ToString,{i, Length[pents]}];
pentTops = Table[If[ MemberQ[pentfam,Topologies[[i]][[1]]],Topologies[[i]]],{i,Length[Topologies]}]// DeleteCases[#, Null]&;
pentRep = Table[GLI[pentTops[[i]][[1]]// ToExpression,{1,1,1,1,1}]-> (TID[FAD@@(pentTops[[i]][[2]]/. StandardPropagatorDenominator[Momentum[l_,D],0,0,{1,1}]->{l,0} /. FeynAmpDenominator[StandardPropagatorDenominator[Momentum[l_,D],0,-mt^2,{1,1}]] -> {l,mt}/. FeynAmpDenominator[a_]:> a), {l}]// NPointTo4Point[#, l]&// mandRep// TID[#/I/Pi^2, {l}, ToPaVe-> True]&// mandRep),{i,Length[pentTops]}];

file = OpenWrite["Files/SymmetryRelations.m"];
WriteString[file,"MastersPaVe = ", ToString[PaVemis// DeleteDuplicates, InputForm], ";\n"];
WriteString[file,"pentRep = ", ToString[pentRep, InputForm], ";\n"];
WriteString[file,"PaVeRules = ", ToString[PaVeRules, InputForm], ";\n"];
WriteString[file,"Masters = ", ToString[MastersBL, InputForm], ";\n"];
Close[file];


FormString[expr_] := 
  StringReplace[
    ToString[expr /. BL[a_, b_] :> GLI[a, Sequence @@ b]/. GLI[a_, {b__}] :> GLI[a, Sequence @@ {b}], 
      InputForm], {"[" -> "(", "]" -> ")", WhitespaceCharacter -> ""}]

If[! DirectoryQ["../form/Files"], 
  CreateDirectory["../form/Files"]];

file = OpenWrite["../form/Files/SymmetryRelations.h"];
Do[  WriteString[file, "id ", FormString[PaVeRules[[j]][[1]]], 
   " = ", 
       FormString[PaVeRules[[j]][[2]]], ";\n"], {j, Length[PaVeRules]}];
Close[file];

file = OpenWrite["Files/lenMasters.txt"];
WriteString[file, ToString[Length[PaVemis// DeleteDuplicates]]];
Close[file];

file = OpenWrite["../form/Files/MastersToSym.h"];
Do[  WriteString[file, "id ", FormString[DeleteDuplicates[PaVemis][[j]]], 
   " = ", 
       FormString[ToExpression["mis"<>ToString[j]]], ";\n"], {j, Length[DeleteDuplicates[PaVemis]]}];
Close[file];

file = OpenWrite["../form/Files/SymToMasters.h"];
Do[  WriteString[file, "id ", FormString[ToExpression["mis"<>ToString[j]]], 
   " = ", FormString[DeleteDuplicates[PaVemis][[j]]], ";\n"], {j, Length[DeleteDuplicates[PaVemis]]}];
Close[file];

Quit[]
