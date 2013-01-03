import itertools
import sys


def create_polynomials(degree):
    count = 0
    counter = 0
    click = 2 ** degree / 10
    next = click
    polys = []
    for poly in itertools.product(*([[-1, 1]] * degree)):
        polys.append(" ".join([str(x) for x in poly]))
        count += 1
        if count == next:
            with open("{}.poly".format(counter), "wb") as fp:
                for p in polys:
                    fp.write("{}\n".format(p))
            polys = []
            next += click
            counter += 1


if __name__ == "__main__":
    create_polynomials(int(sys.argv[1]))
