SetDirectory[DirectoryName[If[$FrontEnd === Null, $InputFileName, NotebookFileName[]]]];

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
sym[x_, i_] := ToExpression[ToString[x] <> ToString[i]]

<< FeynCalc`

If[n == 4,
  FCClearScalarProducts[];
  SetMandelstam[s12, s13, s14, Sequence @@ Join[incoming, -outgoing], Sequence @@ masses];
  mandrep = {s14 -> 2*mt^2 - s12 - s13};,
  If[n == 5,
    FCClearScalarProducts[];
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {mand[1,2] -> s12, mand[2,3] -> s23, mand[3,4] -> s34, mand[4,5] -> s45, mand[1,5] -> s15};
    ,
    SetMandelstam[mand, Join[incoming, -outgoing], masses];
    mandrep = {};
  ]
];

mands = Table[
  sym[p, i]*sym[p, j] -> (SPD[sym[p, i], sym[p, j]] /. mandrep // Together),
  {i, n - 1},
  {j, i, n - 1}
] // Flatten;

If[!DirectoryQ["Files"], CreateDirectory["Files"]];
file = OpenWrite["Files/mands.m"];
WriteString[file, "mands = ", ToString[mands, InputForm], ";\n"];
Close[file];

Quit[]
