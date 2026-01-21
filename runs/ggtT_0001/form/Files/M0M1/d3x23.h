l d3x23 = ( + LoopInt(SPD(p1,lm1)^2*SPD(p2,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*
      FAD( - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 512*mt^2 + 256*s12 + 512*s13,
          - 3*mt^2*s12^2 + 3*s12^3 + 3*s12^2*s13) )

       + LoopInt(SPD(p1,lm1)^2*SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^4 + 512*mt^2*s13 - 256*
         s13^2,3*mt^2*s12^3 - 3*s12^4 - 3*s12^3*s13) )

       + LoopInt(SPD(p1,lm1)^2*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(256*mt^2 - 256*s13,3*s12^3) )

       + LoopInt(SPD(p1,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,
      mt))*i_*gs^6 * ( nh*rat( - 64*mt^4 - 128*mt^2*s12 - 128*mt^2*s13 + 64*
         s12^2 + 256*s12*s13 + 192*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13)
          + nh*ep*rat(128*mt^2 - 64*s12 - 128*s13,3*mt^2*s12 - 3*s12^2 - 3*s12
         *s13) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(-512,3*s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1
      ,mt)*FAD( - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(512*mt^2 - 256*s12 - 512*
         s13,3*s12^3) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1
      ,mt)*FAD( - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 512*mt^4 + 768*mt^2*s12
          + 1024*mt^2*s13 - 768*s12^2 - 768*s12*s13 - 512*s13^2,3*mt^2*s12^3
          - 3*s12^4 - 3*s12^3*s13) )

       + LoopInt(SPD(p1,lm1)*SPD(p2,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat(768*mt^4 - 384*mt^2*s12 - 1024*mt^2*s13
          + 256*s12*s13 + 256*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh
         *ep*rat(-64,3*mt^2 - 3*s12 - 3*s13) )

       + LoopInt(SPD(p1,lm1)*SPD(p3,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1
      ,mt)*FAD( - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^2 + 256*s13, - 
         mt^2*s12^2 + s12^3 + s12^2*s13) )

       + LoopInt(SPD(p1,lm1)*SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat(64*s12 + 128*s13, - 3*mt^2*s12 + 3*
         s12^2 + 3*s12*s13) + nh*ep*rat(-64,3*s12) )

       + LoopInt(SPD(p1,lm1)*SPD(p4,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(-256,3*s12^2) )

       + LoopInt(SPD(p1,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^4 + 320*mt^2*s12 + 512*mt^2*
         s13 - 192*s12*s13 - 256*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13)
          + nh*ep*rat( - 64*mt^2 + 64*s13,3*mt^2*s12 - 3*s12^2 - 3*s12*s13) )

       + LoopInt(SPD(p1,lm1)*SPD(lm1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(256*mt^6 - 128*mt^4*s12 - 768*mt^4*
         s13 + 64*mt^2*s12^2 + 512*mt^2*s12*s13 + 768*mt^2*s13^2 - 128*s12^2*
         s13 - 384*s12*s13^2 - 256*s13^3,3*mt^2*s12^3 - 3*s12^4 - 3*s12^3*s13)
          + nh*ep*rat( - 64*mt^2 + 32*s12 + 64*s13,3*mt^2*s12 - 3*s12^2 - 3*
         s12*s13) )

       + LoopInt(SPD(p1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt)
      )*i_*gs^6 * ( nh*rat( - 256*mt^8 + 64*mt^6*s12 + 768*mt^6*s13 - 192*mt^4
         *s12^2 - 320*mt^4*s12*s13 - 768*mt^4*s13^2 + 32*mt^2*s12^3 + 192*mt^2
         *s12^2*s13 + 192*mt^2*s12*s13^2 + 256*mt^2*s13^3 + 32*s12^3*s13 + 64*
         s12^2*s13^2 + 64*s12*s13^3,3*mt^2*s12^3 - 3*s12^4 - 3*s12^3*s13) + nh
         *ep*rat(96*mt^4 - 32*mt^2*s12 - 128*mt^2*s13 + 16*s12^2 + 32*s13^2,3*
         mt^2*s12 - 3*s12^2 - 3*s12*s13) )

       + LoopInt(SPD(p2,lm1)^2*SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^2 + 256*s12 + 256*s13,3*
         s12^3) )

       + LoopInt(SPD(p2,lm1)^2*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(256*mt^2 - 256*s13,3*s12^3) )

       + LoopInt(SPD(p2,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,
      mt))*i_*gs^6 * ( nh*rat( - 192*mt^2 - 64*s12 - 64*s13,3*s12^2) + nh*ep*
         rat(128,3*s12) )

       + LoopInt(SPD(p2,lm1)*SPD(p3,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1
      ,mt)*FAD( - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(-256,s12^2) )

       + LoopInt(SPD(p2,lm1)*SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 128*mt^2 + 64*s12 + 128*s13,3*s12^2)
          + nh*ep*rat(-64,3*s12) )

       + LoopInt(SPD(p2,lm1)*SPD(p4,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^2 + 256*s13, - 3*mt^2*
         s12^2 + 3*s12^3 + 3*s12^2*s13) )

       + LoopInt(SPD(p2,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat(128*mt^4 - 384*mt^2*s12 - 256*mt^2*s13
          + 128*s12*s13 + 128*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh
         *ep*rat( - 64*mt^2 + 128*s12 + 64*s13,3*mt^2*s12 - 3*s12^2 - 3*s12*
         s13) )

       + LoopInt(SPD(p2,lm1)*SPD(lm1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^6 + 256*mt^4*s12 + 768*
         mt^4*s13 - 64*mt^2*s12^2 - 768*mt^2*s12*s13 - 768*mt^2*s13^2 + 256*
         s12^2*s13 + 512*s12*s13^2 + 256*s13^3,3*mt^2*s12^3 - 3*s12^4 - 3*
         s12^3*s13) + nh*ep*rat(64,3*s12) )

       + LoopInt(SPD(p2,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt)
      )*i_*gs^6 * ( nh*rat(256*mt^8 - 192*mt^6*s12 - 768*mt^6*s13 + 128*mt^4*
         s12^2 + 576*mt^4*s12*s13 + 768*mt^4*s13^2 - 96*mt^2*s12^3 - 192*mt^2*
         s12^2*s13 - 320*mt^2*s12*s13^2 - 256*mt^2*s13^3 - 32*s12^4 - 96*s12^3
         *s13 - 128*s12^2*s13^2 - 64*s12*s13^3,3*mt^2*s12^3 - 3*s12^4 - 3*
         s12^3*s13) + nh*ep*rat( - 96*mt^2 - 32*s12 + 32*s13,3*s12) )

       + LoopInt(SPD(p3,lm1)*SPD(p4,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(-512,3*mt^2*s12 - 3*s12^2 - 3*s12*
         s13) )

       + LoopInt(SPD(p3,lm1)*SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - 
      p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 128*mt^2 + 64*s12 + 128*s13,3*mt^2*
         s12 - 3*s12^2 - 3*s12*s13) )

       + LoopInt(SPD(p3,lm1)*SPD(lm1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat(128*mt^4 - 256*mt^2*s13 + 128*s12*
         s13 + 128*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh*ep*rat(32,
         3*s12) )

       + LoopInt(SPD(p3,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt)
      )*i_*gs^6 * ( nh*rat( - 128*mt^6 + 64*mt^4*s12 + 256*mt^4*s13 - 64*mt^2*
         s12^2 - 192*mt^2*s12*s13 - 128*mt^2*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*
         s12^2*s13) + nh*ep*rat( - 32*mt^2 + 16*s12,3*s12) )

       + LoopInt(SPD(p4,lm1)^2*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,
      mt))*i_*gs^6 * ( nh*rat(128*mt^2 - 64*s12 - 128*s13,3*mt^2*s12 - 3*s12^2
          - 3*s12*s13) )

       + LoopInt(SPD(p4,lm1)*SPD(lm1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD(
       - p2 - lm1,mt))*i_*gs^6 * ( nh*rat( - 256*mt^4 + 512*mt^2*s13 - 256*s12
         *s13 - 256*s13^2,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh*ep*rat(
          - 32*mt^2 + 64*s12 + 32*s13,3*mt^2*s12 - 3*s12^2 - 3*s12*s13) )

       + LoopInt(SPD(p4,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt)
      )*i_*gs^6 * ( nh*rat(256*mt^6 - 512*mt^4*s13 + 128*mt^2*s12^2 + 192*mt^2
         *s12*s13 + 256*mt^2*s13^2 + 32*s12^3 + 64*s12^2*s13 + 64*s12*s13^2,3*
         mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh*ep*rat(32*mt^4 - 80*mt^2*s12
          - 32*mt^2*s13 - 32*s12^2 + 16*s12*s13,3*mt^2*s12 - 3*s12^2 - 3*s12*
         s13) )

       + LoopInt(SPD(lm1,lm1)*FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt
      ))*i_*gs^6 * ( nh*rat( - 128*mt^6 + 64*mt^4*s12 + 384*mt^4*s13 - 256*
         mt^2*s12*s13 - 384*mt^2*s13^2 + 64*s12^2*s13 + 192*s12*s13^2 + 128*
         s13^3,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh*ep*rat( - 64*mt^2 + 
         64*s13,3*s12) )

       + LoopInt(FAD(-lm1,mt)*FAD(p1 - lm1,mt)*FAD( - p2 - lm1,mt))*i_*gs^6
       * ( nh*rat(128*mt^8 - 128*mt^6*s12 - 384*mt^6*s13 + 64*mt^4*s12^2 + 384
         *mt^4*s12*s13 + 384*mt^4*s13^2 - 128*mt^2*s12^2*s13 - 256*mt^2*s12*
         s13^2 - 128*mt^2*s13^3,3*mt^2*s12^2 - 3*s12^3 - 3*s12^2*s13) + nh*ep*
         rat(64*mt^4 - 64*mt^2*s13,3*s12) )); 

