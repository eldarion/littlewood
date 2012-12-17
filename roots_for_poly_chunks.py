import sys

import numpy


def roots_for_poly_chunks(input_filename, output_filename, inner_only):
    polys = open(input_filename, "rb").readlines()
    with open(output_filename, "wb") as fp:
        for line in polys:
            roots = numpy.roots([1] + [int(x) for x in line.strip().split()])
            for root in roots:
                if root.real >= 0 and root.imag >= 0:
                    if not inner_only or abs(root) <= 1:
                        fp.write("{} {}\n".format(root.real, root.imag))


if __name__ == "__main__":
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    
    if len(sys.argv) == 4:
        inner_only = sys.argv[3]
    else:
        inner_only = False
    
    roots_for_poly_chunks(input_filename, output_filename, inner_only)
