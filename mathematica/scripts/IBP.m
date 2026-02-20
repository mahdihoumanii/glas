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


(* -------- Load meta.json -------- *)
meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
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
Get["Files/mands.m"]

If[!DirectoryQ["Files/IBP"], CreateDirectory["Files/IBP"]];

<<Blade`

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

dimFromIndex[list_List] :=
  Total@Table[
    Which[list[[k]] > 0, -2*list[[k]],
          list[[k]] < 0,  2*Abs[list[[k]]],
          True, 0],
    {k, Length[list]}];

RestoreMass[res_, ints_] :=
 Module[{resList, intsList, masters, dimI, dimMI, resSub, restored},
  (* Normalize inputs to lists *)
  resList = If[ListQ[res], res, {res}];
  intsList = If[ListQ[ints], ints, {ints}];

  (* Get dimensions *)
  dimI = dimFromIndex /@ (intsList[[All, 2]]);
  masters = DeleteDuplicates@Cases[resList, BL[__], Infinity];
  dimMI = dimFromIndex /@ (masters[[All, 2]]);

  (* Replace s_ij -> s_ij/msq *)
  resSub = resList /. den[a_] :> 1/a /. {s12 -> s12/msq, s23 -> s23/msq, s34 -> s34/msq,
                       s45 -> s45/msq, s15 -> s15/msq, s13 -> s13/msq, s14 -> s14/msq};

  (* Restore dimensions per term - let Fermat/Singular handle all simplification *)
  restored = Table[
     Module[{expr = resSub[[i]], term},
       Total@Table[
         term = Coefficient[expr, masters[[j]]]*masters[[j]]*
           msq^((dimI[[i]] - dimMI[[j]])/2);
         term,
         {j, Length[masters]}
       ] // Collect[#, _BL,
            (MultivariateApart`MultivariatePassToSingular[
              FermatTools`FermatTogether[#]
            ]) &
          ] &
     ],
     {i, Length[resSub]}
  ];

  (* Return single expression if input wasn't a list *)
  If[ListQ[res], restored, First[restored]]
];

Get["Files/integrals.m"]

replacement = mands //. mt^2 -> msq;
dimension = 4 - 2 ep;
leg = moms;
conservation = momconservation;
loop = {l};
topsector = Table[1, {i, n}];
numeric = {msq -> 1};
BLNthreads = 4;

(* ===== Self-test: Verify function evaluation under wolframscript ===== *)
Print["====== Self-Test: Function Evaluation ======"];
testExpr = (mt^4*(s12^2/(3*mt^4) - (ep*s12^2)/(6*mt^4))) / (1 - (2*ep)/3);
Print["Test Input: ", testExpr];
testResult = MultivariateApart`MultivariatePassToSingular[FermatTools`FermatTogether[testExpr]];
Print["Test Output: ", testResult];
If[Head[testResult] === MultivariateApart`MultivariatePassToSingular,
  Print["ERROR: Function did not evaluate! Output remains unevaluated."];
  Print["This indicates Singular or path resolution failed."];
  Abort[]
];
Print["Self-test PASSED"];
Print["==========================================="];
Print[""];

Monitor[
  Do[
    Print["\nReducing integrals from topology ", topo, " out of ", Length[Topologies]];
    int[topo] = (Cases[glis, GLI[StringJoin["top", ToString[topo]], __], Infinity] // DeleteDuplicates);
    target[topo] = (Cases[glis, GLI[StringJoin["top", ToString[topo]], __], Infinity] // DeleteDuplicates) /. GLI[a_, b__] :> BL[ToExpression[a], b];
    family[topo] = ToExpression[StringJoin["top", ToString[topo]]];
    propagator[topo] = Topologies[[topo]][[2]] /. FeynAmpDenominator[StandardPropagatorDenominator[Momentum[p_, D], 0, -mt^2, {1, 1}]] :> {p^2 - msq} /. FeynAmpDenominator[StandardPropagatorDenominator[Momentum[p_, D], 0, 0, {1, 1}]] :> {p^2} // Flatten;
    BLFamilyDefine[family[topo], dimension, propagator[topo], loop, leg, conservation, replacement, topsector, numeric];
    res[topo] = BLReduce[target[topo], "BladeMode" -> Automatic, "DivideLevel" -> 1];
    (* For massless QCD, skip RestoreMass - no mass scale to restore *)
    If[modelId === "qcd_massless",
      Print["\n  [massless] Skipping RestoreMass"];
      evaluatedRes[topo] = Table[res[topo][[i]]// Collect[#, BL[__], MultivariateApart`MultivariatePassToSingular]&,{i, Length[res[topo]]}];
    ,
      Print["\n \n restoring mass"];
      restoredRes[topo] = RestoreMass[res[topo], int[topo]];
      (* Force full evaluation before writing to file *)
      evaluatedRes[topo] = restoredRes[topo] /. msq -> mt^2;
    ];
    finalRes[topo] = Thread[Rule[target[topo], evaluatedRes[topo]]];
    file = OpenWrite["Files/IBP/IBP" <> ToString[topo] <> ".m"];
    WriteString[file, "IBP[", ToString[topo], "] = ", ToString[finalRes[topo], InputForm], ";\n"];
    Close[file];
  , {topo, 1, Length[Topologies]}],
topo];


FormString[expr_] := 
 StringReplace[
  ToString[expr /. BL[a_, b_] :> GLI[a, Sequence @@ b], 
   InputForm], {"[" -> "(", "]" -> ")", WhitespaceCharacter -> ""}]
If[! DirectoryQ["../form/Files/IBP"], 
  CreateDirectory["../form/Files/IBP"]];


Do[
  Get["Files/IBP/IBP" <> ToString[i] <> ".m"];
  file = OpenWrite["../form/Files/IBP/IBP" <> ToString[i] <> ".h"];
  Do[If[IBP[i][[1]]==={},WriteString[file," "];,WriteString[file, "id ", FormString[IBP[i][[j]][[1]]], " = ", 
    FormString[IBP[i][[j]][[2]]], ";\n"]], {j, Length[IBP[i]]}];
  Close[file];
  Clear[IBP];
  , {i, Length[Topologies]}];
