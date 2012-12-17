#!/usr/bin/env python

# attempt at pulling roots.py / heatmap.py work and making it run in parallel with ruffus

# https://thoughtstreams.io/paltman/ruffus/

import array
import colorsys
import itertools
import os
import struct
import sys
import time
import zlib

import numpy
import ruffus


ROOT_CHUNKS_SIZE = 1000
INNER_ONLY = False
FILE_DEGREE = "degree.txt"
FILE_POLY_LIST = "poly.list"
FILE_SIZE = "size.txt"
FILE_HITS = "hits.txt"


@ruffus.files(FILE_DEGREE, FILE_POLY_LIST)
def create_polynomials(input_filename, output_filename):
    degree = int(open(input_filename, "rb").read())
    count = 0
    click = 2 ** degree / 10
    next = click
    with open(FILE_POLY_LIST, "wb") as fp:
        for poly in itertools.product(*([[-1, 1]] * degree)):
            count += 1
            if count == next:
                print >> sys.stderr, count
                next += click
            fp.write(
                "{}\n".format(" ".join([str(x) for x in poly]))
            )


@ruffus.follows(create_polynomials)
@ruffus.split(FILE_POLY_LIST, "*.poly")
def split_polynomials_list(input_filename, output_filenames):
    for f in output_filenames:
        os.unlink(f)
    with open(input_filename, "rb") as fp:
        count = 0
        output_filename = "{}.poly".format(count)
        for i, line in enumerate(fp):
            if i % ROOT_CHUNKS_SIZE == 0:
                count += 1
                output_filename = "{}.poly".format(count)
                out = open(output_filename, "wb")
            out.write(line)


@ruffus.transform(split_polynomials_list, ruffus.suffix(".poly"), ".roots")
def roots_for_poly_chunks(input_filename, output_filename):
    polys = open(input_filename, "rb").readlines()
    with open(os.path.join(output_filename), "wb") as fp:
        for line in polys:
            roots = numpy.roots([1] + [int(x) for x in line.strip().split()])
            for root in roots:
                if root.real >= 0 and root.imag >= 0:
                    if not INNER_ONLY or abs(root) <= 1:
                        fp.write("{} {}\n".format(root.real, root.imag))


@ruffus.merge(roots_for_poly_chunks, FILE_HITS)
def hits_for_roots(input_filenames, output_filename):
    size = int(open(FILE_SIZE, "rb").read())  # @@@ this is bad, hardcoded for now as i don't know how ot combine @files with @merge
    hits = numpy.zeros((int(size * 2.1), int(size * 1.5)), dtype=numpy.int)
    for input_filename in input_filenames:
        roots = open(input_filename, "rb").readlines()
        for root in roots:
            r, i = root.strip().split()
            x = round(float(r) * size)
            y = round(float(i) * size)
            hits[x, y] += 1
    with open(output_filename, "wb") as fp:
        map(lambda h: fp.write("{}\n".format(" ".join([str(x) for x in h]))), hits)


def rgb_for_value(value):
    return (
        int(255 * x)
        for x in colorsys.hsv_to_rgb(value / 4, 1 - value, 0.5 + value / 2)
    )


def output_chunk(f, chunk_type, data):
    f.write(struct.pack("!I", len(data)))
    f.write(chunk_type)
    f.write(data)
    checksum = zlib.crc32(data, zlib.crc32(chunk_type))
    f.write(struct.pack("!i", checksum))


@ruffus.files([FILE_SIZE, FILE_HITS], None)
@ruffus.follows(hits_for_roots)
def heatmap(input_filenames, output):
    size = int(open(input_filenames[0], "rb").read())
    hits = numpy.array([
        [float(y) for y in x.split()]
        for x in open(input_filenames[1], "rb").readlines()
    ])
    hit_to_rgb = {}
    filename = "littlewood_{}_{}.png".format(degree, size)
    width = int(size * 4)
    height = int(size * 2 * numpy.sqrt(2))
    log_max = numpy.log(numpy.amax(hits))
    with open(filename, "wb") as f:
        f.write(struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10))
        data = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
        output_chunk(f, "IHDR", data)
        compressor = zlib.compressobj()
        data = array.array("B")
        for py in range(height):
            if py % 100 == 0:
                print py
            hy = abs(py - height / 2)
            data.append(0)
            for px in range(width):
                hx = abs(px - width / 2)
                h = hits[hx, hy]
                if h > 0:
                    r, g, b = hit_to_rgb.get(h, (None, None, None))
                    if r is None:
                        value = numpy.log(h) / log_max
                        r, g, b = rgb_for_value(value)
                        hit_to_rgb[h] = (r, g, b)
                else:
                    r, g, b = 0, 0, 0
                data.extend([r, g, b])
        compressed = compressor.compress(data.tostring())
        flushed = compressor.flush()
        output_chunk(f, "IDAT", compressed + flushed)
        output_chunk(f, "IEND", "")
    return filename


def main(degree, size):
    print "generating roots for degree={}".format(degree,)
    
    start = time.time()
    
    open(FILE_DEGREE, "wb").write(degree)
    open(FILE_SIZE, "wb").write(size)
    
    ruffus.pipeline_run([heatmap], multiprocess=2)
    
    print "total time: {} seconds".format(round(time.time()) - start)


if __name__ == "__main__":
    degree = sys.argv[1]
    if len(sys.argv) == 3:
        size = sys.argv[2]
    else:
        size = "200"
    main(degree, size)
