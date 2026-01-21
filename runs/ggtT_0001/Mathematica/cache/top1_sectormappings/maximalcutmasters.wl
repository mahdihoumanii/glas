AppendTo[$Path,"/Users/mahdihoumani/Softwares/blade/blade/blade-main/BLAddOns/BladeIBP"];
AppendTo[$Path,"/Users/mahdihoumani/Softwares/finiteflow/mathlink"];
AppendTo[$LibraryPath,"/Users/mahdihoumani/Softwares/finiteflow"];
If[$FrontEnd===Null,$InputFileName,NotebookFileName[]]//DirectoryName//SetDirectory;
<<BladeIBP.m;
<<FiniteFlow.m;
<<topology.wl;


IntegralOrdering=1;
family=top1;


FFLinearSolveLearn[eqs_,paras_,allvars_,neededvars_]:=Module[{graph,in,sys},
(*initialize fflow*)
FiniteFlow`Private`FFGraphId = Association[{}];
FiniteFlow`Private`FFAlgId = Association[{}];
FiniteFlow`Private`FFGraphInputs = Association[{}];
FFNThreads = Automatic;
(*solve*)
FFSparseSolve[eqs,allvars,"Parameters"->paras,"NeededVars"->neededvars,"IndepVarsOnly"->True]
];


SetOptions[AutoDetermine,"CutNoDot" -> False, "CloseSymmetry" -> False, "MaxIncrement" -> 2, "StartingPower" -> 2, "HighestPower" -> 5, "CheckSymmetry" -> True, "Nthreads" -> 4];


SetOptions[AutoDetermine,"GenCutIds" -> GenCutIds, "LinearReduce" -> FFLinearSolveLearn];


SetOptions[AutoDetermine,"Numeric"->{msq -> 1}];


Block[{mapdir,flag},
mapdir = "results";
If[!DirectoryQ@mapdir, CreateDirectory[mapdir]];
flag=AutoDetermine[family];
If[!FreeQ[flag,$Failed],Print["error: AutoDetermine failed"];Abort[]];
Put[MappedSectors[family],FileNameJoin[{mapdir,"mappedsectors"}]];
Put[UniqueSectors[family],FileNameJoin[{mapdir,"uniquesectors"}]];
Put[ZeroSectors[family],FileNameJoin[{mapdir,"zerosectors"}]];
Put[FastMIs[#]&/@NonZeroSectors[family]//Flatten//SortIntegrals,FileNameJoin[{mapdir,"rawmastersnomap"}]];
Put[FastMIs[#]&/@UniqueSectors[family]//Flatten//SortIntegrals,FileNameJoin[{mapdir,"rawmasters"}]];
Print["# rawmasters(nomap): ", Length@(Get@FileNameJoin[{mapdir,"rawmastersnomap"}]),", # rawmasters: ", Length@(Get@FileNameJoin[{mapdir,"rawmasters"}]) ];
];


CloseKernels[];Pause[0.1];


Quit[];