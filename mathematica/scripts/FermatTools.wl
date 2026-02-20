(* ::Package:: *)

(* ============================================================
   FermatTools \[LongDash] Environment-aware Fermat interface for Mathematica
   
   USAGE:
   ------
   1. Set Fermat path via environment:
      export FERMATPATH="/path/to/fer64"          (file)
      export FERMATPATH="/path/to/Ferm7a"         (directory, searches fer64/fer/fer.exe)
   
   2. Or set in Mathematica:
      SetFermatPath["/path/to/fer64"]
   
   3. Or it will search PATH for "fer64"
   
   ============================================================ *)

BeginPackage["FermatTools`"];

ResolveFermatExe::usage = "ResolveFermatExe[] returns the absolute path to the Fermat executable.";
SetFermatPath::usage = "SetFermatPath[path] sets the Fermat executable path (file or directory).";
FermatTogether::usage = "FermatTogether[expr] rationalizes expr using Fermat.";
FermatListTogether::usage = "FermatListTogether[mat] rationalizes a matrix or list using Fermat.";

Begin["`Private`"];

(* Global variable for user-set Fermat path *)
$FermatExe = None;

(* ============================================================
   Path Resolution
   ============================================================ *)

ResolveFermatExe[] := Module[
  {envPath, exePath, candidates, found},
  
  (* 1. Check user-set $FermatExe *)
  If[$FermatExe =!= None && FileExistsQ[$FermatExe],
    Return[$FermatExe]
  ];
  
  (* 2. Check FERMATPATH environment variable *)
  envPath = Environment["FERMATPATH"];
  If[envPath =!= $Failed && envPath =!= "",
    If[DirectoryQ[envPath],
      (* Directory: try fer64, fer, fer.exe *)
      candidates = {
        FileNameJoin[{envPath, "fer64"}],
        FileNameJoin[{envPath, "fer"}],
        FileNameJoin[{envPath, "fer.exe"}]
      };
      found = SelectFirst[candidates, FileExistsQ[#] &, None];
      If[found =!= None, Return[found]];
    ,
      (* File: use directly *)
      If[FileExistsQ[envPath],
        Return[envPath]
      ]
    ]
  ];
  
  (* 3. Try fer64 from PATH *)
  exePath = FindFile["fer64"];
  If[exePath =!= $Failed,
    Return[exePath]
  ];
  
  (* 4. If nothing found, throw descriptive error *)
  Message[ResolveFermatExe::notfound];
  $Failed
];

ResolveFermatExe::notfound = "Fermat executable not found. Please set FERMATPATH environment variable (e.g. export FERMATPATH=/path/to/fer64) or call SetFermatPath[\"/path/to/fer64\"] in Mathematica.";

SetFermatPath[path_String] := Module[
  {},
  If[!FileExistsQ[path] && !DirectoryQ[path],
    Message[SetFermatPath::notfound, path];
    Return[$Failed]
  ];
  $FermatExe = path;
  path
];

SetFermatPath::notfound = "Path does not exist: `1`";

(* ============================================================
   User Functions (original implementations)
   ============================================================ *)

(* Create deterministic temp directory for Fermat files *)
$FermatTempDir := Module[{tmpDir, workDir},
  (* Use Directory[] first (script should have set this), fall back to $TemporaryDirectory *)
  workDir = If[
    StringQ[$InputFileName] && StringLength[$InputFileName] > 0,
    DirectoryName[$InputFileName],
    Directory[]
  ];
  (* Final fallback if Directory[] also fails *)
  If[!StringQ[workDir] || StringLength[workDir] === 0,
    workDir = $TemporaryDirectory
  ];
  tmpDir = FileNameJoin[{workDir, "Files", "tmp_fermat"}];
  If[!DirectoryQ[tmpDir], CreateDirectory[tmpDir, CreateIntermediateDirectories -> True]];
  tmpDir
];

(* Robust Fermat executable detection *)
GetFermatExe[] := Module[{ferExe},
  ferExe = Which[
    StringEndsQ[Environment["FERMATPATH"], "fer64"] || StringEndsQ[Environment["FERMATPATH"], "fer64.exe"],
      Environment["FERMATPATH"],
    DirectoryQ[Environment["FERMATPATH"]],
      FileNameJoin[{Environment["FERMATPATH"], "fer64"}],
    True,
      "fer64"
  ];
  If[!FileExistsQ[ferExe],
    ferExe = ResolveFermatExe[]
  ];
  ferExe
];

FermatTogether[expr_]:= 
Module[{input, vars, Command, res, Fermat, inname, outname, tmpDir}, 
  Fermat = GetFermatExe[];
  If[Fermat === $Failed, Return[$Failed]];
  
  tmpDir = $FermatTempDir;
  inname = FileNameJoin[{tmpDir, "ferin_" <> CreateUUID[] <> ".in"}];
  outname = FileNameJoin[{tmpDir, "ferout_" <> CreateUUID[] <> ".out"}];
  
  If[ListQ[expr], expr,
    vars = Variables[expr /. D -> d /. Complex[0,a_] :> im*a]; 
    input = OpenWrite[inname]; 
    Do[WriteString[input, "&(J=", vars[[i]], ");\n"], {i, Length[vars]}];
    WriteString[input, "&_t;\nexpr := ", ToString[expr /. D -> d /. Complex[0,a_] :> im*a, InputForm], ";\n"];
    WriteString[input, StringJoin["&(S='", outname, "');\n"], "&U;\n", "!(&o,expr);\n", "&x;\n"]; 
    Close[input];
    RunProcess[{Fermat}, "StandardOutput", "\n&(R='" <> inname <> "');\n&q;"];
    
    (* Check if output exists and is non-empty *)
    If[!FileExistsQ[outname] || FileByteCount[outname] === 0,
      Print["ERROR: Fermat output file not created or empty: ", outname];
      Print["Fermat executable: ", Fermat];
      Print["Input file: ", inname];
      Abort[]
    ];
    
    res = Get[outname];
    Quiet[DeleteFile[inname]]; 
    Quiet[DeleteFile[outname]]; 
    res /. d -> D /. im -> I
  ]
];

FermatListTogether[mat_]:= 
Module[{n, vars, input, res, Fermat, matrix, inname, outname, tmpDir}, 
  Fermat = GetFermatExe[];
  If[Fermat === $Failed, Return[$Failed]];
  
  tmpDir = $FermatTempDir;
  inname = FileNameJoin[{tmpDir, "ferInv_" <> CreateUUID[] <> ".in"}];
  outname = FileNameJoin[{tmpDir, "ferInv_" <> CreateUUID[] <> ".out"}];
  
  If[MatrixQ[mat], matrix = mat;, If[ListQ[mat], matrix = {mat};]];
  vars = Variables[matrix]; 
  n = Length[matrix];
  input = OpenWrite[inname]; 
  Do[WriteString[input, "&(J=", vars[[i]], ");\n"], {i, Length[vars]}];
  WriteString[input, "Array m", StringReplace[ToString[Dimensions[matrix]], {"{" -> "[", "}" -> "]"}], ";\n"];
  Do[WriteString[input, "m[", i, ",", j, "] := ", ToString[matrix[[i,j]], InputForm], ";\n"], {i, Dimensions[matrix][[1]]}, {j, Dimensions[matrix][[2]]}];
  WriteString[input, StringJoin["&(S='", outname, "');\n"], "&U;\n",  "!(&o,[m]);\n", "&x;\n"]; 
  Close[input];
  RunProcess[{Fermat}, "StandardOutput", "\n&(R='" <> inname <> "');\n&q;"];
  
  (* Check if output exists and is non-empty *)
  If[!FileExistsQ[outname] || FileByteCount[outname] === 0,
    Print["ERROR: Fermat output file not created or empty: ", outname];
    Print["Fermat executable: ", Fermat];
    Print["Input file: ", inname];
    Abort[]
  ];
  
  ToExpression[StringReplace[Import[outname, "String"], {":" -> ""}]]; 
  Quiet[DeleteFile[inname]]; 
  Quiet[DeleteFile[outname]]; 
  res = Monitor[Table[rat[m[i, j]], {i, Dimensions[matrix][[1]]}, {j, Dimensions[matrix][[2]]}], {i, j}]; 
  Clear[m]; 
  Return[res /. rat[a_Integer] :> a]
];

End[];

EndPackage[];
