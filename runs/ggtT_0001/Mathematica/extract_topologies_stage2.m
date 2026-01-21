(* FeynCalc topology extraction stage 2 (uses Extended.m) *)

If[$FrontEnd === Null, $InputFileName, NotebookFileName[]] // DirectoryName // SetDirectory;

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


If[!FileExistsQ[FileNameJoin[{"Files", "topo_stage1.mx"}]],
  Print["[stage2] ERROR: Files/topo_stage1.mx not found."];
  Abort[];
];

Get[FileNameJoin[{"Files", "topo_stage1.mx"}]];

If[!FileExistsQ["Extended.m"],
  Print["[stage2] ERROR: Extended.m not found."];
  Abort[];
];

<< FeynCalc`;
Get["Extended.m"];

Print["[stage2] Remapping extended topologies..."];
intsExt = Table[FAD @@ Extended[[i]], {i, Length[Extended]}];
{intsExtra, toposExtra} = FCLoopFindTopologies[intsExt, {l}, Names -> "extra"];
subtoposExt = FCLoopFindSubtopologies[toposExtra];
mapExtra = FCLoopFindTopologyMappings[toposExtra, PreferredTopologies -> subtoposExt];
mapExt = FCLoopFindTopologyMappings[{toposExtra, topos3} // Flatten, PreferredTopologies -> subtoposExt];



If[n == 4,
  SetMandelstam[s12, s13, s14, Sequence @@ Join[incoming, -outgoing], Sequence @@ masses];
  mandrep = {s14 -> 2*mt^2 - s12 - s13};,
  If[n == 5,
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {mand[1,2] -> s12, mand[2,3] -> s23, mand[3,4] -> s34, mand[4,5] -> s45, mand[1,5] -> s15};
    ,
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {};
  ]
];



ints4 = FCLoopApplyTopologyMappings[ints3 /. momconservation, mapExt] /. mandrep;
topos4 = mapExt[[2]];

RenameTopologies = Table[topos4[[i]][[1]] -> "top" <> ToString[i], {i, Length[topos4]}];
topos5 = topos4 /. RenameTopologies;
ints5 = ints4 /. RenameTopologies;
intrule = Thread[Rule[integrals, ints5]];
glis = intrule // Cases[#, GLI[__], Infinity] & // DeleteDuplicates;

Print["[stage2] Writing Files/integrals.m..."];
outFile = OpenWrite[FileNameJoin[{"Files", "integrals.m"}]];
WriteString[outFile, "integrals = ", ToString[integrals, InputForm], ";\n"];
WriteString[outFile, "glis = ", ToString[glis, InputForm], ";\n"];
WriteString[outFile, "Topologies = ", ToString[topos5, InputForm], ";\n"];
WriteString[outFile, "intrule = ", ToString[intrule, InputForm], ";\n"];
Close[outFile];

FormString[expr_]:= StringReplace[ToString[expr/. GLI[a_,b_]:> GLI[ToExpression[a],Sequence@@b], InputForm],{"["-> "(","]"-> ")",WhitespaceCharacter-> ""}]
file = OpenWrite["../form/Files/intrule.h"];
Do[WriteString[file, "id ", FormString[intrule[[i]][[1]]], "=", FormString[intrule[[i]][[2]]],";\n"],{i,Length[intrule]}];
Close[file];

If[!DirectoryQ["../form/Files/M0M1top"], CreateDirectory["../form/Files/M0M1top"]];
If[!DirectoryQ["Files/M0M1top"], CreateDirectory["Files/M0M1top"]];



Print["[stage2] Done. Wrote Files/integrals.m"];
Print["[stage2] Done. Wrote ../form/Files/intrule.h"];
DeleteFile["Extended.m"];
DeleteFile["Files/Topologies.txt"];
DeleteFile["Files/topo_stage1.mx"];

