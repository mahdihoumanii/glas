#procedure SymToRat
    .sort 
#do i = {s12,s23,s34,s45,s15,mt,s13,s14}
id `i'^pow? = rat(`i'^pow,1);
    .sort 
#enddo

#do i= 1,1
id once den(mt?) = rat(1, mt);
if (count(den,1)!= 0); 
    redefine i "0";
endif;
    .sort 
#enddo 


#endprocedure

