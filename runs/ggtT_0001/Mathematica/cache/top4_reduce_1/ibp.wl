AppendTo[$Path,"/Users/mahdihoumani/Softwares/blade/blade/blade-main/BLAddOns/BladeIBP"];
AppendTo[$Path,"/Users/mahdihoumani/Softwares/finiteflow/mathlink"];
AppendTo[$LibraryPath,"/Users/mahdihoumani/Softwares/finiteflow"];
If[$FrontEnd===Null,$InputFileName,NotebookFileName[]]//DirectoryName//SetDirectory;
<<BladeIBP.m;
<<FiniteFlow.m
<<topology.wl;
IntegralOrdering = 1;
CreateDirectory["results"];
Put[ZeroSectors[top4],"results/zerosectors"];
If[NonZeroSectors[top4]==={}, Print["this family is trivial."];Quit[]];

Module[{rank,maxdots,GetSectors,GetSeeds,cutposi,learn,maplearn,filters,prefix,famcount,selectedfiles,lirankmin,rawmasters},

rank=2;
maxdots=0;
GetSectors=Automatic;
cutposi=Position[{0, 0, 0, 0},1]//Flatten;
learn={4 -> {0, 2}, 3 -> {0, 2}, 2 -> {0, 2}, _ -> {0, 2}};
maplearn=Map[{1,0}+#&,learn//Association]//Normal;
filters[learn_]:=Join[If[learn=!={},{If[-Plus@@Select[#[[2]],#<0&]>(Length@Select[#[[2]],#1>0&]/.learn)[[2]],False,True]&,
If[(Plus@@Select[#[[2]],#>0&]-Length@Select[#[[2]],#>0&])>(Length@Select[#[[2]],#1>0&]/.learn)[[1]],False,True]&},{}],
If[False,{If[(#[[2]][[cutposi]]=!=ConstantArray[1,Length[cutposi]]),False,True]&},{}]];
lirankmin[_]:=0;
GetSeeds["IBP"][sector_]:=GenSeeds[sector,{0,maxdots},0,rank,filters[learn]];
GetSeeds["LI"][sector_]:=GenSeeds[sector,{0,maxdots},lirankmin[sector],rank,filters[learn]];
GetSeeds["SR"][sector_]:=GenSeeds[sector,{0,0},0,rank,filters[learn]];
GetSeeds["Map"][sector_]:=GenSeeds[sector,{0,maxdots+1},0,rank,filters[maplearn]];
rawmasters=<|BL[top4, {1, 1, 1, 1}] -> {BL[top4, {1, 1, 1, 1}]}, BL[top4, {0, 1, 1, 1}] -> {BL[top4, {0, 1, 1, 1}]}, BL[top4, {0, 1, 1, 0}] -> {BL[top4, {0, 1, 1, 0}]}, BL[top4, {1, 0, 0, 1}] -> {BL[top4, {1, 0, 0, 1}]}, BL[top4, {0, 0, 0, 1}] -> {BL[top4, {0, 0, 0, 1}]}|>;
GetSeeds["SubSym"][sector_]:=Lookup[rawmasters,sector,{}];
GetSeeds["ExtMap"][sector_]:=GenSeeds[sector,{0,maxdots+1},0,rank];
FastGenIds[top4,GetSeeds,"Directory"->"ibps","LaunchKernels"->4,"GetSectors"->GetSectors];
];

Module[{exints,usints,usZeroIntegrals},

exints = {};
Export["ibps/exints_def.m",exints];
Export["ibps/ids_top4_exints.mx",(-#[[1]]+#[[2]])&/@exints,"MX"];
Export["ibps/ints_top4_exints.mx",IntegralsIn[exints],"MX"];
usints = {};
Export["ibps/usints_def.m",usints];
Export["ibps/ids_top4_usints.mx",(-#[[1]]+#[[2]])&/@usints,"MX"];
Export["ibps/ints_top4_usints.mx",IntegralsIn[usints],"MX"];


If[!({s12, s13, ep}==={}),SerializeFastIds[FileNames["ibps/ids_top4_*.mx"], {msq -> 1}, {s12, s13, ep}, "UserDefinedInts"->(First/@usints),"ExtraInts"->(First/@exints)]];
];
CloseKernels[];Pause[0.1];
Quit[];