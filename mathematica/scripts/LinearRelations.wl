(* ::Package:: *)

(* LinearRelations - Find linear relations between rational functions *)
(* Uses FiniteFlow for efficient numerical fit-based relation discovery *)

Needs["FiniteFlow`"]
Needs["FFUtils`"]

BeginPackage["LinearRelations`"]

(* Public Interface *)
e::usage = "e[i] represents the i-th basis element in linear relations."
c::usage = "c[i] represents the i-th coefficient in the linear system."
f::usage = "f[i] represents the i-th rational function."

FindLinearRelations::usage = 
  "FindLinearRelations[rats] finds linear relations among rational functions using FiniteFlow.\n\
Returns {ruleMap, linearRelations, independentRules} where:\n\
  - ruleMap: Maps input functions to e[i] basis\n\
  - linearRelations: Linear dependencies among functions\n\
  - independentRules: Basis functions in terms of original variables"

Begin["`Private`"]

(* Main implementation *)
FindLinearRelations[rats_] := Module[
  {
    graph, vars=Variables[rats], in, out,
    coefficients, functions, degrees, complexity,
    sortedFunctions, sortedCoefficients,
    zero, fiteq, sorted, graphFit, fitLearn, fitRec, fitSol, fit,
    linrels, symbolicOut, independentFuncs, indep, rec, indepRules,
    ruleMap
  },
  
  (* Initialize FiniteFlow graph and variables *)
 
  FFNewGraph[graph, in, vars];
  
  (* Evaluate rational functions numerically *)
  FFAlgRatFunEval[graph, out, {in}, vars, rats];
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

End[]

EndPackage[]
