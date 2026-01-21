l d3x8 = ( + LoopInt(SPD(p1,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( ep*rat(72,mt^2*s12 - s12^2 - s12*s13) + rat(72,s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(-72,mt^2*s12 - s12^2 - s12*s13) + rat(-144,s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(72,s12^2) + rat(144*mt^4 - 72*mt^2*s12 - 288*mt^2*s13
          + 72*s12^2 + 216*s12*s13 + 144*s13^2,mt^2*s12^3 - s12^4 - s12^3*s13)
          )

       + LoopInt(SPD(p1,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(72*mt^2 - 72*s13, - mt^2*s12^2 + s12^3 + s12^2*s13)
          + rat( - 144*mt^4 + 72*mt^2*s12 + 288*mt^2*s13 - 72*s12^2 - 216*s12*
         s13 - 144*s13^2,mt^2*s12^3 - s12^4 - s12^3*s13) )

       + LoopInt(SPD(p2,lm1)^2*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*i_*gs^6
       * ( rat(72,s12^2) )

       + LoopInt(SPD(p2,lm1)*SPD(p3,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat(-72,s12^2) + rat( - 144*mt^4 + 72*mt^2*s12 + 288*mt^2
         *s13 - 72*s12^2 - 216*s12*s13 - 144*s13^2,mt^2*s12^3 - s12^4 - s12^3*
         s13) )

       + LoopInt(SPD(p2,lm1)*SPD(p4,lm1)*FAD(lm1,0)*FAD( - p1 - p2 + lm1,0))*
      i_*gs^6 * ( ep*rat( - 72*mt^2 + 72*s13, - mt^2*s12^2 + s12^3 + s12^2*s13
         ) + rat(144*mt^4 - 72*mt^2*s12 - 288*mt^2*s13 + 72*s12^2 + 216*s12*
         s13 + 144*s13^2,mt^2*s12^3 - s12^4 - s12^3*s13) )); 

