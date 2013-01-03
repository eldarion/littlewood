import sys

import numpy


def roots_for_poly_chunks(inner_only):
    polys = open("polys.dat", "rb").readlines()
    with open("roots.dat", "wb") as fp:
        for line in polys:
            roots = numpy.roots([1] + [int(x) for x in line.strip().split()])
            for root in roots:
                if root.real >= 0 and root.imag >= 0:
                    if not inner_only or abs(root) <= 1:
                        fp.write("{} {}\n".format(root.real, root.imag))


if __name__ == "__main__":
    roots_for_poly_chunks(len(sys.argv) == 2)
