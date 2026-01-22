Needs["FiniteFlow`"];
Needs["FFUtils`"];
If[$FrontEnd === Null, $InputFileName, NotebookFileName[]] // DirectoryName // SetDirectory;

If[!DirectoryQ["Files"], CreateDirectory["Files"]];

meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];
nmis = meta["nmis"];
name = meta["loop_main"];

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

  FFAlgRatFunEval[graph, out, {in}, vars, Rats];
  FFGraphOutput[graph, out];
  FFNParsOut[graph, out];

  coefficients = c @ Range[FFNParsOut[graph, out]];
  functions = f /@ Range[FFNParsOut[graph, out]];

  degrees = FFTotalDegrees[graph];
  complexity = FFNSamplePoints[graph][[2]];

  sortedFunctions = SortBy[functions, complexity[[#[[1]]]] &];
  sortedCoefficients = c @@ # & /@ sortedFunctions;

  FFAlgTake[graph, sorted, {out}, {functions} -> sortedFunctions];
  FFAlgRatNumEval[graph, zero, {0}];
  FFAlgChain[graph, fiteq, {sorted, zero}];
  FFGraphOutput[graph, fiteq];

  FFNewGraph[graphFit];
  FFAlgSubgraphFit[graphFit, fit, {}, graph, vars, sortedCoefficients];
  FFGraphOutput[graphFit, fit];

  fitLearn = FFDenseSolverLearn[graphFit, sortedCoefficients];
  fitRec = FFReconstructNumeric[graphFit];
  fitSol = FFDenseSolverSol[fitRec, fitLearn];

  linrels = FFLinearRelationsFromFit[sortedFunctions, sortedCoefficients, fitSol];

  FFDeleteGraph[graphFit];

  independentFuncs = Complement[functions, First /@ linrels];
  symbolicOut = Collect[Sum[e[i] f[i], {i, Length[functions]}] /. linrels, _f, Together];

  FFGraphOutput[graph, out];
  FFGraphPrune[graph];

  FFAlgTake[graph, indep, {out}, {functions} -> independentFuncs];
  FFGraphOutput[graph, indep];
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

Do[
  Get["Files/MasterCoefficients/mi" <> ToString[i] <> "/MasterCoefficient" <> ToString[i] <> ".m"];
  rats[i] = DeleteDuplicates[Cases[coef[i] //. rat[a_, b_] :> rat[a, b], rat[__], Infinity]];
  linRats[i] = FindLinearRelations[rats[i]] /. f[a_] -> f[i, a];
  MICoef[i] = coef[i] //. linRats[i][[4]] /. linRats[i][[3]];
, {i, nmis}];

indepFun = (Table[linRats[i][[5]], {i, nmis}] // Flatten)[[All, 2]];
FinalFun = FindLinearRelations[indepFun];
indepF = (Table[linRats[i][[5]], {i, nmis}] // Flatten)[[All, 1]];
indepToFinal = Thread[Rule[indepF, FinalFun[[1]] /. FinalFun[[3]]]];

SymbolicOut = Thread[Rule[FinalFun[[5]][[All, 1]], FinalFun[[5]][[All, 2]] // MultivariatePassToSingular]];

Do[
  FinalMiCoef[i] = MICoef[i] //. indepToFinal /. den[a_] :> 1/a //
    CollectFlat[#, {gs, A0[__], B0[__], C0[__], D0[__], nh, nl, f[_]}, MultivariatePassToSingular] &;
, {i, nmis}];

Result = Table[FinalMiCoef[i], {i, nmis}] // Flatten;

file = OpenWrite["Files/MasterCoefficients.m"];
WriteString[file, name, "= ", ToString[Result //. den[a_] :> 1/a, InputForm], ";\n"];
WriteString[file, "RationalFunctions", "= ", ToString[SymbolicOut //. den[a_] :> 1/a, InputForm], ";\n"];
Close[file];
