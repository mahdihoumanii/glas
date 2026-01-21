If[KeyExistsQ["ParallelOptions"/.SystemOptions["ParallelOptions"],#],SetSystemOptions["ParallelOptions"->#->1]]&/@{"ParallelThreadNumber","MKLThreadNumber"};
SetDim[4 - 2*ep];
Internal = {l};
External = {p1, p2, p3, p4};
MomentumConservation = {p4 -> p1 + p2 - p3};
Replacements = {p1^2 -> 0, p1*p2 -> s12/2, p1*p3 -> (msq - s13)/2, p2^2 -> 0, p2*p3 -> (-msq + s12 + s13)/2, p3^2 -> msq};
Propagators = {l^2, (l - p1)^2, -msq + (l - p3)^2, -msq + (l + p2 - p3)^2}/. MomentumConservation//Expand;
NewBasis[top6,Propagators,Internal, External, MomentumConservation, Replacements,"ExtraIntDeriv"->{{{0}, {0}, {0}, {0}}}];
AnalyzeSectors[top6,{1, 1, 1, 1},"CutDs"->{0, 0, 0, 0},"Prescription"->{1, 1, 1, 1},"CloseSyms"->False,"ExtSyms"->True];
