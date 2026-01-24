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
  Print["Evaluating rational functions over finite fields"];
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


Do[
  Get["Files/MasterCoefficients/mi" <> ToString[i] <> "/MasterCoefficient" <> ToString[i] <> ".m"];
  rats[i] = DeleteDuplicates[Cases[coef[i] //. rat[a_, b_] :> rat[a, b], rat[__], Infinity]];
  Print["Number of rational functions for mi" <> ToString[i] <> ": " <> ToString[Length[rats[i]]]];
  linRats[i] = FindLinearRelations[rats[i]] /. f[a_] -> f[i, a];
  Print["Number of linear relations for mi" <> ToString[i] <> ": " <> ToString[Length[linRats[i][[3]]]]];
  MICoef[i] = coef[i] //. linRats[i][[4]] /. linRats[i][[3]];
  file  = OpenWrite["Files/MasterCoefficients/mi" <> ToString[i] <> "/MasterCoefficient" <> ToString[i] <> ".m"];
  WriteString[file, "MICoef[", ToString[i], "] = ", ToString[MICoef[i], InputForm], ";\n"];
  WriteString[file, "indepRules[", ToString[i], "] = ", ToString[linRats[i][[5]], InputForm], ";\n"];
  Close[file];
, {i, 1,nmis}];