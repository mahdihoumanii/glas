l d2x5 = ( + LoopInt(SPD(p1,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( nl*rat(96,s12^2) + nl*ep*rat(-96,mt^2*s12 - s13*s12) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( nl*rat(-192,s12^2) + nl*ep*rat(96,mt^2*s12 - s13*s12) )

       + LoopInt(SPD(p1,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( nl*rat(192*mt^4 - 384*mt^2*s13 + 96*mt^2*s12 + 192*s13^2 + 
         96*s13*s12,mt^2*s12^3 - s13*s12^3) + nl*ep*rat( - 96*mt^2 + 96*s13 + 
         96*s12,mt^2*s12^2 - s13*s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( nl*rat( - 192*mt^4 + 384*mt^2*s13 - 96*mt^2*s12 - 192*s13^2
          - 96*s13*s12,mt^2*s12^3 - s13*s12^3) + nl*ep*rat(96,s12^2) )

       + LoopInt(SPD(p1,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6 * ( 
         nl*rat(192*mt^6 - 576*mt^4*s13 + 576*mt^2*s13^2 + 192*mt^2*s13*s12 - 
         96*mt^2*s12^2 - 192*s13^3 - 192*s13^2*s12,mt^2*s12^3 - s13*s12^3) + 
         nl*ep*rat( - 96*mt^2 + 96*s13 + 96*s12,s12^2) )

       + LoopInt(SPD(p2,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( nl*rat(96,s12^2) )

       + LoopInt(SPD(p2,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( nl*rat( - 192*mt^4 + 384*mt^2*s13 - 96*mt^2*s12 - 192*s13^2
          - 96*s13*s12,mt^2*s12^3 - s13*s12^3) + nl*ep*rat(96*mt^2 - 96*s13 - 
         96*s12,mt^2*s12^2 - s13*s12^2) )

       + LoopInt(SPD(p2,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( nl*rat(192*mt^4 - 384*mt^2*s13 + 96*mt^2*s12 + 192*s13^2 + 
         96*s13*s12,mt^2*s12^3 - s13*s12^3) + nl*ep*rat(-96,s12^2) )

       + LoopInt(SPD(p2,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6 * ( 
         nl*rat(192*mt^6 - 576*mt^4*s13 + 576*mt^2*s13^2 + 192*mt^2*s13*s12 - 
         96*mt^2*s12^2 - 192*s13^3 - 192*s13^2*s12,mt^2*s12^3 - s13*s12^3) + 
         nl*ep*rat( - 96*mt^2 + 96*s13 + 96*s12,s12^2) )

       + LoopInt(SPD(lm1,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6 * ( 
         nl*rat( - 192*mt^6 + 576*mt^4*s13 - 576*mt^2*s13^2 - 192*mt^2*s13*s12
          + 96*mt^2*s12^2 + 192*s13^3 + 192*s13^2*s12,mt^2*s12^3 - s13*s12^3)
          + nl*ep*rat(96*mt^2 - 96*s13 - 96*s12,s12^2) )); 

