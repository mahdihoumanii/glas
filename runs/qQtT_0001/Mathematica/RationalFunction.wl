(* ::Package:: *)

Quit[]


Needs["FiniteFlow`"];
Needs["FFUtils`"];
If[$FrontEnd === Null, $InputFileName, NotebookFileName[]] // DirectoryName // SetDirectory;


meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];
nmis = meta["nmis"];


Get["../../../mathematica/scripts/MultivariateApart.wl"]


FindLinearRelations[rats_] := Module[
  {
     vars, in, out,
    coefficients, functions, degrees, complexity,
    sortedFunctions, sortedCoefficients,
    zero, fiteq, sorted, graphFit, fitLearn, fitRec, fitSol, fit,
    linrels, symbolicOut, independentFuncs, indep, rec, indepRules,
    ruleMap,graph,Rats
  },
  
  (* Initialize FiniteFlow graph and variables *)
  Rats = rats /. rat[a_,b_]:> a/b;
  vars = Variables[Rats];
  FFNewGraph[graph, in, vars];
  
  (* Evaluate rational functions numerically *)
  FFAlgRatFunEval[graph, out, {in}, vars, Rats];
  FFGraphOutput[graph, out];
  FFNParsOut[graph, out];
  
  coefficients = c @ Range[FFNParsOut[graph, out]];
  functions = f /@ Range[FFNParsOut[graph, out]];
  
  (* Analyze complexity and sort by efficiency *)
  degrees = FFTotalDegrees[graph];
  complexity = FFNSamplePoints[graph][[2]];
  
  sortedFunctions = SortBy[functions, complexity[[#[[1]]]] &];
  sortedCoefficients = c @@ # & /@ sortedFunctions;
  
  (* Build fitting equation *)
  FFAlgTake[graph, sorted, {out}, {functions} -> sortedFunctions];
  FFAlgRatNumEval[graph, zero, {0}];
  FFAlgChain[graph, fiteq, {sorted, zero}];
  FFGraphOutput[graph, fiteq];
  
  (* Learn and reconstruct fit *)
  FFNewGraph[graphFit];
  FFAlgSubgraphFit[graphFit, fit, {}, graph, vars, sortedCoefficients];
  FFGraphOutput[graphFit, fit];
  
  fitLearn = FFDenseSolverLearn[graphFit, sortedCoefficients];
  fitRec = FFReconstructNumeric[graphFit];
  fitSol = FFDenseSolverSol[fitRec, fitLearn];
  
  (* Extract linear relations *)
  linrels = FFLinearRelationsFromFit[sortedFunctions, sortedCoefficients, fitSol];
  
  (* Cleanup intermediate graphs *)
  FFDeleteGraph[graphFit];
  
  (* Extract independent functions and symbolic output *)
  independentFuncs = Complement[functions, First /@ linrels];
  symbolicOut = Collect[
    Sum[e[i] f[i], {i, Length[functions]}] /. linrels,
    _f,
    Together
  ];
  
  (* Prune and reconstruct *)
  FFGraphOutput[graph, out];
  FFGraphPrune[graph];
  
  FFAlgTake[graph, indep, {out}, {functions} -> independentFuncs];
  FFGraphOutput[graph, indep];
  rec = FFReconstructFunction[graph, vars];
  indepRules = Inner[Rule, independentFuncs, rec, List];
  
  (* Build output rules *)
  ruleMap = Thread[Rule[rats, functions]];
  
  (* Cleanup *)
  FFDeleteGraph[graph];
  
  (* Return results *)
  <|
    "functions" -> functions,
    "independentFunctions" -> independentFuncs,
    "linearRelations" -> linrels,
    "ruleMap" -> ruleMap,
    "independentRules" -> indepRules,
    "symbolicOutput" -> symbolicOut,
    "basis" -> Array[e, Length[functions]]
  |>
]


Do[
Get["Files/MasterCoefficients/mi"<>ToString[i]<>"/MasterCoefficient"<>ToString[i]<>".m"];
rats[i] = DeleteDuplicates[Cases[coef[i]//. rat[a_,b_]:> rat[a,b],rat[__], Infinity]];
linRats[i]= FindLinearRelations[rats[i]]/.f[a_]-> f[i, a];
MICoef[i] = coef[i]//. linRats[i][[4]]/.linRats[i][[3]];
,{i,nmis}]


indepFun = ((Table[linRats[i][[5]],{i, nmis}]// Flatten))[[All,2]];
FinalFun = FindLinearRelations[indepFun];
indepF = ((Table[linRats[i][[5]],{i, nmis}]// Flatten))[[All,1]];
indepToFinal = Thread[Rule[indepF,FinalFun[[1]]/. FinalFun[[3]]]];


SymbolicOut= Thread[Rule[FinalFun[[5]][[All,1]],FinalFun[[5]][[All,2]]// MultivariatePassToSingular]];


Do[
FinalMiCoef[i] = MICoef[i] //. indepToFinal/. den[a_]:> 1/a//CollectFlat[#, {gs,A0[__],B0[__],C0[__],D0[__],nh,nl,f[_]}, MultivariatePassToSingular]&;
,{i,nmis}]
