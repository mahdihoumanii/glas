#-
#: IncDir procedures
Off Statistics;

#include declarations.h
    .sort

#include Files/Amps/amp1l/d1.h
    .sort

#$max = 0;
if ( count(gs,1) > $max ) $max = count_(gs,1);

    .sort
#write <Files/gs_power_1l.txt> "%$" $max
.end
