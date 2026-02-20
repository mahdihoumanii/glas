(* ::Package:: *)

(* ::Package:: *)

CloseKernels[];

(* Set working directory - wolframscript provides $InputFileName *)
(* When run from runs/{run}/Mathematica/, script is in this directory *)
SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];
(* ===== Normalize environment + PATH ===== *)
fermatPath = Environment["FERMATPATH"] /. $Failed -> "";
singularPath = Environment["SINGULARPATH"] /. $Failed -> "";

If[fermatPath =!= "", SetEnvironment["FERMATPATH" -> fermatPath]];
If[singularPath =!= "", SetEnvironment["SINGULARPATH" -> singularPath]];
SetEnvironment["PATH" ->
  StringRiffle[
    DeleteDuplicates@Join[
      StringSplit[Environment["PATH"], ":"],
      Select[{fermatPath, singularPath}, # =!= "" &]
    ],
    ":"
  ]
];



(* Load MultivariateApart and FermatTools from scripts directory *)
(* Path: runs/{run}/Mathematica -> runs/{run} -> runs -> project_root -> mathematica/scripts *)
scriptsDir = FileNameJoin[{Directory[], "..", "..", "..", "mathematica", "scripts"}];

(* Add to search path *)
If[!MemberQ[$Path, scriptsDir], AppendTo[$Path, scriptsDir]];

multivariateApartPath = FileNameJoin[{scriptsDir, "MultivariateApart.wl"}];
If[FileExistsQ[multivariateApartPath],
  Get[multivariateApartPath],
  Print["ERROR: MultivariateApart.wl not found at ", multivariateApartPath];
  Abort[]
];

fermatToolsPath = FileNameJoin[{scriptsDir, "FermatTools.wl"}];
If[FileExistsQ[fermatToolsPath],
  Get[fermatToolsPath],
  Print["ERROR: FermatTools.wl not found at ", fermatToolsPath];
  Abort[]
];

<<FiniteFlow`


Get["Files/Sudakov.m"]
sud[1,5] = Sudakov[1,5]/. mt-> 1// Together;
sud[2,5] = Sudakov[2,5]/. mt-> 1// Together;


meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n = meta["n_in"] + meta["n_out"];
massdim = 2*(4- n);


RestoreMass[expr_, massdim_]:= (expr/.{s-> s/mt^2, t-> t/mt^2, ktsq-> ktsq/mt^2, kt3-> kt3/mt^2})*mt^massdim;


FFDeleteGraph[g1];
FFNewGraph[g1,in1,{lambda,ep,s,t,x,ktsq,kt3}];
FFAlgRatFunEval[g1,map1,{in1},{lambda,ep,s,t,x,ktsq,kt3},Join[{ep},sud[1,5][[All,2]]]];
Monitor[Do[
Get/@FileNames["Files/M0M0/d*x"<>ToString[j]<>".m"];
diag[j] = Sum[d[i,j]/. mt-> 1/. gs-> 1,{i, 1,n0l}]/. rat[a_,b_]:> a/b// FermatTogether;
FFAlgRatFunEval[g1,di[j],{map1},Flatten[{ep,sud[1,5][[All,1]]}],{diag[j]}];
FFGraphOutput[g1, di[j]];
,{j, 1,n0l}],j]
FFAlgAdd[g1, sum, Table[di[i],{i, n0l}]];
FFGraphOutput[g1, sum]


FFNewGraph[gexpansion,in,{ep,s,t,x,ktsq,kt3}];
FFAlgLaurent[gexpansion,laurent,{in},g1,0];
FFGraphOutput[gexpansion,laurent];



explearn = FFLaurentLearn[gexpansion];
Print["Expansion From: ", explearn// Min, " to " ,explearn//Max];

rec = FFReconstructFunction[gexpansion,{ep,s,t,x,ktsq,kt3}];
Print["Reconstructing done"];
sol=FermatTogether[RestoreMass[((Normal/@FFLaurentSol[Factor[rec],lambda,explearn])), massdim]];
pfdSol = Collect[sol,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular[#/. msq-> mt^2// FermatTogether]&]/. den[a_]:> 1/a;


FFDeleteGraph[g1]


LP0l15 = Coefficient[pfdSol, lambda, -2]// First;
NLP0l15 = Coefficient[pfdSol, lambda, -1]// First;
NNLP0l15 = Coefficient[pfdSol, lambda, 0]// First;


LP0lAVG15 = LP0l15/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, Factor]&;
NLP0lAVG15 = NLP0l15/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, Factor]&;
NNLP0lAVG15 = NNLP0l15/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, Factor]&;


FFDeleteGraph[g1];
FFNewGraph[g1,in1,{lambda,ep,s,t,x,ktsq,kt3}];
FFAlgRatFunEval[g1,map1,{in1},{lambda,ep,s,t,x,ktsq,kt3},Join[{ep},sud[1,5][[All,2]]]];
Monitor[Do[
Get/@FileNames["Files/M0M0/d*x"<>ToString[j]<>".m"];
diag[j] = Sum[d[i,j]/. mt-> 1/. gs-> 1,{i, 1,n0l}]/. rat[a_,b_]:> a/b// FermatTogether;
FFAlgRatFunEval[g1,di[j],{map1},Flatten[{ep,sud[2,5][[All,1]]}],{diag[j]}];
FFGraphOutput[g1, di[j]];
Clear[d, diag]
,{j, 1,n0l}],j]
FFAlgAdd[g1, sum, Table[di[i],{i, n0l}]];
FFGraphOutput[g1, sum]


FFNewGraph[gexpansion,in,{ep,s,t,x,ktsq,kt3}];
FFAlgLaurent[gexpansion,laurent,{in},g1,0];
FFGraphOutput[gexpansion,laurent];



explearn = FFLaurentLearn[gexpansion];
Print["Expansion From: ", explearn// Min, " to " ,explearn//Max];

rec = FFReconstructFunction[gexpansion,{ep,s,t,x,ktsq,kt3}];
Print["Reconstructing done"];
sol=FermatTogether[RestoreMass[((Normal/@FFLaurentSol[Factor[rec],lambda,explearn])), massdim]];
pfdSol25 = Collect[sol,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular[#/. msq-> mt^2// FermatTogether]&]/. den[a_]:> 1/a;

FFDeleteGraph[g1]


LP0l25 = Coefficient[pfdSol25, lambda, -2]// First//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;
NLP0l25 = Coefficient[pfdSol25, lambda, -1]// First//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;
NNLP0l25 = Coefficient[pfdSol25, lambda, 0]// First//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;


LP0lAVG25 = LP0l25/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;
NLP0lAVG25 = NLP0l25/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;
NNLP0lAVG25 = NNLP0l25/. kt3^2-> kT3/. kt3^4-> kT3^2/. kt3^6-> kT3^3/. kT3-> (mt^4-2*mt^2*t+s*t+t^2)*ktsq/(2*s-2*ep*s)/. kt3-> 0//Collect[#,{lambda, ktsq, kt3, ep}, MultivariatePassToSingular]&// ReplaceAll[#, den[a_]:> 1/a]&;


file = OpenWrite["Files/Expansion0l.m"];
WriteString[file ,"LP0l15 = ", ToString[{LP0l15,LP0lAVG15}, InputForm], ";\n"];
WriteString[file ,"NLP0l15 = ", ToString[{NLP0l15,NLP0lAVG15}, InputForm], ";\n"];
WriteString[file ,"NNLP0l15 = ", ToString[{NNLP0l15,NNLP0lAVG15}, InputForm], ";\n"];

WriteString[file ,"LP0l25 = ", ToString[{LP0l25,LP0lAVG25}, InputForm], ";\n"];
WriteString[file ,"NLP0l25 = ", ToString[{NLP0l25,NLP0lAVG25}, InputForm], ";\n"];
WriteString[file ,"NNLP0l25 = ", ToString[{NNLP0l25,NNLP0lAVG25}, InputForm], ";\n"];
Close[file];
