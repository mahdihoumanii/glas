(* FeynCalc topology extraction stage 1 (meta.json driven) *)

SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];

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

If[!DirectoryQ["Files"], CreateDirectory["Files"]];

<< FeynCalc`;


Print["[stage1] n0l=", n0l, " n1l=", n1l, " n=", n];

(* -------- Load integrals -------- *)
Print["[stage1] Loading M0M1 d[i,j] files..."];
ClearAll[d, integrals];
integrals = {};

Do[
  Do[
    file = FileNameJoin[{"Files", "M0M1", "d" <> ToString[i] <> "x" <> ToString[j] <> ".m"}];
    If[FileExistsQ[file],
      Get[file];
      If[ValueQ[d[i, j]],
        integrals = Join[integrals, Cases[d[i, j], LoopInt[__], Infinity]];
      ];
    ];
  , {j, 1, n1l}]
, {i, 1, n0l}];

integrals = DeleteDuplicates[Flatten[integrals]];
Print["[stage1] integrals: ", Length[integrals]];

ints1 = integrals //. {
    lm1 -> l,
    FAD[a_, b_] :> FAD[{a, b}],
    LoopInt[a__] :> a
}//.momconservation;

(* -------- Topology finding -------- *)
Print["[stage1] FCLoopFindTopologies..."];
{ints2, topos2} = FCLoopFindTopologies[ints1, {l}];
sub2 = FCLoopFindSubtopologies[topos2];
map2 = FCLoopFindTopologyMappings[topos2, PreferredTopologies -> sub2];
topos3 = map2[[2]];
ints3 = FCLoopApplyTopologyMappings[ints2, map2, FCLoopCreateRulesToGLI -> False];
Print["[stage1] topologies: ", Length[topos3]];

(* -------- Export incomplete topologies -------- *)
Print["[stage1] Exporting incomplete topologies..."];
ToFix = Select[topos3[[All, 2]], Length[#] < n &] /. 
  FeynAmpDenominator[StandardPropagatorDenominator[Momentum[l_, D], 0, x_, {1, 1}]] :>
    {l, Sqrt[-x] /. Sqrt[m_^2] :> m};

PyStr[expr_] := StringReplace[ToString[expr, InputForm], {"{" -> "[", "}" -> "]"}];

topFile = OpenWrite[FileNameJoin[{"Files", "Topologies.txt"}]];
Do[
  WriteString[topFile, "top" <> ToString[i] <> ":" <> PyStr[ToFix[[i]]] <> "\n"];
, {i, 1, Length[ToFix]}];
Close[topFile];
Print["[stage1] Topologies.txt written (", Length[ToFix], " entries)."];

(* -------- Save intermediate state -------- *)
DumpSave[FileNameJoin[{"Files", "topo_stage1.mx"}], {integrals, ints3, topos3, momconservation, mandrep, n}];
Print["[stage1] Wrote Files/topo_stage1.mx"];
