(* ::Package:: *)

CloseKernels[];
SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];
If[!DirectoryQ["Files"], CreateDirectory["Files"]];

Needs["FiniteFlow`"];
Needs["FFUtils`"];

Get["../../../mathematica/scripts/MultivariateApart.wl"];


FindLinearRelations[rats_] := Module[
  {
    vars, in, out,
    coefficients, functions, degrees, complexity,
    sortedFunctions, sortedCoefficients,
    zero, fiteq, sorted, graphFit, fitLearn, fitRec, fitSol, fit,
    linrels, symbolicOut, independentFuncs, indep, rec, indepRules,
    ruleMap, graph, Rats
  },
  
  Rats = rats /. rat[a_, b_] :> a/b;
  vars = Variables[Rats];
  FFNewGraph[graph, in, vars];
  Print["Evaluating ",Length[Rats], " rational functions over finite fields"];
  FFAlgRatFunEval[graph, out, {in}, vars, Rats];
  Print["Done Evaluating"];  
  FFGraphOutput[graph, out];
  FFNParsOut[graph, out];

  coefficients = c @ Range[FFNParsOut[graph, out]];
  functions = f /@ Range[FFNParsOut[graph, out]];
  
  degrees = FFTotalDegrees[graph];
  complexity = FFNSamplePoints[graph][[2]];
  Print["Max Complexity ", Max[complexity]];
  sortedFunctions = SortBy[functions, complexity[[#[[1]]]] &];
  sortedCoefficients = c @@ # & /@ sortedFunctions;

  FFAlgTake[graph, sorted, {out}, {functions} -> sortedFunctions];
  FFAlgRatNumEval[graph, zero, {0}];
  FFAlgChain[graph, fiteq, {sorted, zero}];
  FFGraphOutput[graph, fiteq];

  FFNewGraph[graphFit];
  FFAlgSubgraphFit[graphFit, fit, {}, graph, vars, sortedCoefficients];
  FFGraphOutput[graphFit, fit];
  Print["Solving Linear System of equations"]; 
  fitLearn = FFDenseSolverLearn[graphFit, sortedCoefficients];
  fitRec = FFReconstructNumeric[graphFit];
  fitSol = FFDenseSolverSol[fitRec, fitLearn];
  Print["Finding linear relations"]; 
  linrels = FFLinearRelationsFromFit[sortedFunctions, sortedCoefficients, fitSol];

  FFDeleteGraph[graphFit];

  independentFuncs = Complement[functions, First /@ linrels];
  symbolicOut = Collect[Sum[e[i] f[i], {i, Length[functions]}] /. linrels, _f, Together];
  Print["Found ", Length[independentFuncs], " independent rational functions out of ",Length[rats],"."]; 
  FFGraphOutput[graph, out];
  FFGraphPrune[graph];

  FFAlgTake[graph, indep, {out}, {functions} -> independentFuncs];
  FFGraphOutput[graph, indep];
  Print["Reconstucting linear relations"]; 
  rec = FFReconstructFunction[graph, vars];
  indepRules = Inner[Rule, independentFuncs, rec, List];

  ruleMap = Thread[Rule[rats, functions]];

  FFDeleteGraph[graph];

  <|
    "functions" -> functions,
    "independentFunctions" -> independentFuncs,
    "linearRelations" -> linrels,
    "ruleMap" -> ruleMap,
    "independentRules" -> indepRules,
    "symbolicOutput" -> symbolicOut,
    "basis" -> Array[e, Length[functions]]
  |>
];


meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];
nmis = meta["nmis"];
name = meta["loop_main"];


Print["Combining all linear relations..."];
Do[Get["Files/MasterCoefficients/mi"<>ToString[i]<>"/MasterCoefficient"<>ToString[i]<>".m"],{i, nmis}]
indepFun = (Table[indepRules[i], {i,nmis}] // Flatten)[[All, 2]];
FinalFun = FindLinearRelations[indepFun];
indepF = (Table[indepRules[i], {i, nmis}] // Flatten)[[All, 1]];
indepToFinal = Thread[Rule[indepF, FinalFun[[1]] /. FinalFun[[3]]]];

SymbolicOut = Thread[Rule[FinalFun[[5]][[All, 1]], FinalFun[[5]][[All, 2]] // MultivariatePassToSingular]];

Do[
  FinalMiCoef[i] = MICoef[i] //. indepToFinal /. den[a_] :> 1/a //
    CollectFlat[#, {gs, A0[__], B0[__], C0[__], D0[__], nh, nl, f[_]}, MultivariatePassToSingular] &;
, {i, nmis}];
Print["Done."];
Result = Table[FinalMiCoef[i], {i, nmis}] // Flatten;

file = OpenWrite["Files/MasterCoefficients.m"];
WriteString[file, name, "= ", ToString[Result //. den[a_] :> 1/a, InputForm], ";\n"];
WriteString[file, "RatFun", "= ", ToString[SymbolicOut //. den[a_] :> 1/a, InputForm], ";\n"];
Close[file];




Print["\n******************\n******************\nTotal Number of Initial rational functions: ", Length[indepFun]," was reduced to ",Length[symbolicOut]," in the first step."];
Print["******************\n******************\n"];