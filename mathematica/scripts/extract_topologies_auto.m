(* FeynCalc topology extraction pipeline driven by meta.json *)

SetDirectory[NotebookDirectory[]];

(* -------- Helpers -------- *)
MassFromToken[t_] := If[StringContainsQ[t, "t"], mt, 0];

FindExtendPy[start_] := Module[{dir = start, root, cand},
  While[True,
    cand = FileNameJoin[{dir, "extend.py"}];
    If[FileExistsQ[cand], Return[cand]];
    root = DirectoryName[dir];
    If[root === dir, Break[]];
    dir = root;
  ];
  $Failed
];


(* -------- Load meta.json -------- *)
meta = Import["../meta.json", "RawJSON"];
n0l = meta["n0l"];
n1l = meta["n1l"];
parts = meta["particles"];
n = meta["n_in"] + meta["n_out"];
mandDefine = If[KeyExistsQ[meta, "mand_define"], meta["mand_define"], ""];

If[!DirectoryQ["Files"], CreateDirectory["Files"]];

moms = ToExpression /@ parts[[All, "momentum"]];
incoming = ToExpression /@ (Select[parts, #["side"] == "in" &][[All, "momentum"]]);
outgoing = ToExpression /@ (Select[parts, #["side"] == "out" &][[All, "momentum"]]);
masses = MassFromToken /@ parts[[All, "token"]];

maxMom = ToExpression["p" <> ToString[n]];
If[MemberQ[outgoing, maxMom],
  momconservation = {maxMom -> Total[incoming] - Total[DeleteCases[outgoing, maxMom]]},
  momconservation = {maxMom -> Total[outgoing] - Total[DeleteCases[incoming, maxMom]]}
];

<< FeynCalc`;

Print["[extract] n0l=", n0l, " n1l=", n1l, " n=", n];





(* -------- Load integrals -------- *)
Print["[extract] Loading M0M1 d[i,j] files..."];
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
Print["[extract] integrals: ", Length[integrals]];

ints1 = integrals //. {
    lm1 -> l,
    FAD[a_, b_] :> FAD[{a, b}],
    LoopInt[a__] :> a
};

(* -------- Topology finding -------- *)
Print["[extract] FCLoopFindTopologies..."];
{ints2, topos2} = FCLoopFindTopologies[ints1, {l}];
sub2 = FCLoopFindSubtopologies[topos2];
map2 = FCLoopFindTopologyMappings[topos2, PreferredTopologies -> sub2];
topos3 = map2[[2]];
ints3 = FCLoopApplyTopologyMappings[ints2, map2, FCLoopCreateRulesToGLI -> False];
Print["[extract] topologies: ", Length[topos3]];

(* -------- Export incomplete topologies -------- *)
Print["[extract] Exporting incomplete topologies..."];
ToFix = Select[topos3[[All, 2]], Length[#] < n &] /. 
  FeynAmpDenominator[StandardPropagatorDenominator[Momentum[l_, D], 0, x_, {1, 1}]] :>
    {l, Sqrt[-x] /. Sqrt[m_^2] :> m};

PyStr[expr_] := StringReplace[ToString[expr, InputForm], {"{" -> "[", "}" -> "]"}];

topFile = OpenWrite[FileNameJoin[{"Files", "Topologies.txt"}]];
Do[
  WriteString[topFile, "top" <> ToString[i] <> ":" <> PyStr[ToFix[[i]]] <> "\n"];
, {i, 1, Length[ToFix]}];
Close[topFile];
Print["[extract] Topologies.txt written (", Length[ToFix], " entries)."];

(* -------- Run extend.py -------- *)
Print["[extract] Running extend.py..."];
pyExe = Environment["GLAS_PYTHON"];
If[pyExe == "" || pyExe === $Failed, pyExe = "python3"];
extPath = FileNameJoin[{NotebookDirectory[], "extend.py"}];
If[!FileExistsQ[extPath],
  Print["[extract] ERROR: extend.py not found in run directory."];
  Abort[];
];
Print["[extract] python: ", pyExe];
Print["[extract] extend.py path: ", extPath];
extRes = RunProcess[{pyExe, extPath}, ProcessDirectory -> NotebookDirectory[]];
If[extRes["ExitCode"] != 0,
  Print["[extract] ERROR: extend.py failed."];
  Print["[extract] stdout: ", extRes["StandardOutput"]];
  Print["[extract] stderr: ", extRes["StandardError"]];
  Abort[];
];
If[!FileExistsQ["Extended.m"],
  Print["[extract] ERROR: Extended.m not found."];
  Abort[];
];

(* -------- Remap extended topologies -------- *)
Print["[extract] Loading Extended.m..."];
Get["Extended.m"];
intsExt = Table[FAD @@ Extended[[i]], {i, Length[Extended]}];
{intsExtra, toposExtra} = FCLoopFindTopologies[intsExt, {l}, Names -> "extra"];
subtoposExt = FCLoopFindSubtopologies[toposExtra];
mapExtra = FCLoopFindTopologyMappings[toposExtra, PreferredTopologies -> subtoposExt];
mapExt = FCLoopFindTopologyMappings[{toposExtra, topos3} // Flatten, PreferredTopologies -> subtoposExt];

(* -------- Apply mappings + kinematics -------- *)
Print["[extract] Applying mappings + kinematics..."];

If[n == 4,
  SetMandelstam[s12, s13, s14, Sequence @@ Join[incoming, -outgoing], Sequence @@ masses];
  mandrep = {s14-> 2*mt^2- s12 -s13};,
  If[ n==5,
  SetMandelstam[mand, Join[incoming, -outgoing], masses];
  mandrep = {mand[1,2]-> s12,mand[2,3]-> s13, mand[3,4]-> s34, mand[4,5]-> s45, mand[1,5]-> s15};
  ]
];

ints4 = FCLoopApplyTopologyMappings[ints3 /. momconservation, mapExt] /. mandrep;
topos4 = mapExt[[2]];

RenameTopologies = Table[topos4[[i]][[1]] -> "top" <> ToString[i], {i, Length[topos4]}];
topos5 = topos4 /. RenameTopologies;
ints5 = ints4 /. RenameTopologies;
intrule = Thread[Rule[integrals, ints5]];
glis = intrule // Cases[#, GLI[__], Infinity] & // DeleteDuplicates;

(* -------- Write output -------- *)
Print["[extract] Writing Files/integrals.m..."];
outFile = OpenWrite[FileNameJoin[{"Files", "integrals.m"}]];
WriteString[outFile, "integrals = ", ToString[integrals, InputForm], ";\n"];
WriteString[outFile, "glis = ", ToString[glis, InputForm], ";\n"];
WriteString[outFile, "Topologies = ", ToString[topos5, InputForm], ";\n"];
WriteString[outFile, "intrule = ", ToString[intrule, InputForm], ";\n"];
Close[outFile];

Print["[extract] Done. Wrote Files/integrals.m"];
