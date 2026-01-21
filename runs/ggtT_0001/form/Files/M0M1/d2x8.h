l d2x8 = ( + LoopInt(SPD(p1,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( ep*rat(-72,mt^2*s12 - s13*s12) + rat(72,s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(72,mt^2*s12 - s13*s12) + rat(-144,s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat( - 72*mt^2 + 72*s13 + 72*s12,mt^2*s12^2 - s13*s12^2)
          + rat(144*mt^4 - 288*mt^2*s13 + 72*mt^2*s12 + 144*s13^2 + 72*s13*s12
         ,mt^2*s12^3 - s13*s12^3) )

       + LoopInt(SPD(p1,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(72,s12^2) + rat( - 144*mt^4 + 288*mt^2*s13 - 72*mt^2*
         s12 - 144*s13^2 - 72*s13*s12,mt^2*s12^3 - s13*s12^3) )

       + LoopInt(SPD(p2,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( rat(72,s12^2) )

       + LoopInt(SPD(p2,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(72*mt^2 - 72*s13 - 72*s12,mt^2*s12^2 - s13*s12^2) + 
         rat( - 144*mt^4 + 288*mt^2*s13 - 72*mt^2*s12 - 144*s13^2 - 72*s13*s12
         ,mt^2*s12^3 - s13*s12^3) )

       + LoopInt(SPD(p2,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(-72,s12^2) + rat(144*mt^4 - 288*mt^2*s13 + 72*mt^2*
         s12 + 144*s13^2 + 72*s13*s12,mt^2*s12^3 - s13*s12^3) )); 

