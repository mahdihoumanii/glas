#-
#: IncDir procedures
Off Statistics;

#include declarations.h
.sort

#include Files/Amps/amp1l/d1.h

L F = d1;
.sort

#$max = 0;
if ( count(gs,1) > $max ) $max = count_(gs,1);

Print ">> diagram 1: Max power of gs is %$", $max;
.sort
#write <Files/gs_probe.txt> "`$max'"

.end
