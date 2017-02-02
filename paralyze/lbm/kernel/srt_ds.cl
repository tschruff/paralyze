// t : bed topography
// n : surface roughness
// current : [0-8] pdfs
//           [9]   bed elevation
//           [10]  surface roughness
//           [11]  u_x
//           [12]  u_y
//           [13]  h

__kernel void collide( __global const float16 * current, __global float16 * results )
{
    int gid = get_global_id(0);

    // compute source terms

}