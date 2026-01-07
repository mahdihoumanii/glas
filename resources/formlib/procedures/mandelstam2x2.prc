#procedure mandelstam2x2(p1,p2,p3,p4,m1,m2,m3,m4)
** Mandelstam variables for 4 parton process with p1+p2= p3+p4  ******

id `p1'.`p1' = `m1'^2;
id `p2'.`p2' = `m2'^2;
id `p3'.`p3' = `m3'^2;
id `p4'.`p4' = `m4'^2;

id `p1'.`p2' = s12/2 - `m1'^2/2 - `m2'^2/2;
id `p3'.`p4' = s12/2 - `m3'^2/2 - `m4'^2/2;

id `p1'.`p3' = -s13/2 + `m1'^2/2 + `m3'^2/2;
id `p1'.`p4' = -s14/2 + `m1'^2/2 + `m4'^2/2;
id `p2'.`p3' = -s14/2 + `m2'^2/2 + `m3'^2/2;
id `p2'.`p4' = -s13/2 + `m2'^2/2 + `m4'^2/2;

id mass(`p1')= `m1';
id mass(`p2')= `m2';
id mass(`p3')= `m3';
id mass(`p4')= `m4';

id s14 = `m1'^2+ `m2'^2 + `m3'^2 + `m4'^2 - s12- s13;

argument den; 
id `p1'.`p1' = `m1'^2;
id `p2'.`p2' = `m2'^2;
id `p3'.`p3' = `m3'^2;
id `p4'.`p4' = `m4'^2;

id `p1'.`p2' = s12/2 - `m1'^2/2 - `m2'^2/2;
id `p3'.`p4' = s12/2 - `m3'^2/2 - `m4'^2/2;

id `p1'.`p3' = -s13/2 + `m1'^2/2 + `m3'^2/2;
id `p1'.`p4' = -s14/2 + `m1'^2/2 + `m4'^2/2;
id `p2'.`p3' = -s14/2 + `m2'^2/2 + `m3'^2/2;
id `p2'.`p4' = -s13/2 + `m2'^2/2 + `m4'^2/2;
id mass(`p1')= `m1';
id mass(`p2')= `m2';
id mass(`p3')= `m3';
id mass(`p4')= `m4';
id s14 = `m1'^2+ `m2'^2 + `m3'^2 + `m4'^2 - s12- s13;

endargument;




#endprocedure