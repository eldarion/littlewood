#!/usr/bin/env python

# attempt at pulling roots.py / heatmap.py work and making it run in parallel with ruffus

# https://thoughtstreams.io/paltman/ruffus/

import array
import colorsys
import itertools
import struct
import sys
import time
import zlib

import numpy
import ruffus


INNER_ONLY = False


def roots_for_poly(poly):
    roots = []
    for root in numpy.roots((1,) + poly):
        if root.real >= 0 and root.imag >= 0:
            if not INNER_ONLY or abs(root) <= 1:
                roots.append((root.real, root.imag))
    return roots


@ruffus.files("degree.txt", "roots.txt")
def roots_for_degree(input_filename, output_filename):
    degree = int(open(input_filename, "rb").read())
    
    count = 0
    click = 2 ** degree / 10
    next = click
    roots = []
    for poly in itertools.product(*([[-1, 1]] * degree)):
        count += 1
        if count == next:
            print >> sys.stderr, count
            next += click
        roots.extend(roots_for_poly(poly))
    
    with open(output_filename, "wb") as fp:
        map(lambda x: fp.write("{} {}\n".format(x[0], x[1])), roots)


def output_chunk(f, chunk_type, data):
    f.write(struct.pack("!I", len(data)))
    f.write(chunk_type)
    f.write(data)
    checksum = zlib.crc32(data, zlib.crc32(chunk_type))
    f.write(struct.pack("!i", checksum))


def hits_for_roots(roots_filename, size):
    hits = numpy.zeros((int(size * 2.1), int(size * 1.5)), dtype=numpy.int)
    with open(roots_filename, "rb") as fp:
        for root in fp:
            r, i = root.strip().split()
            x = round(float(r) * size)
            y = round(float(i) * size)
            hits[x, y] += 1
        return hits


def rgb_for_value(value):
    return (
        int(255 * x)
        for x in colorsys.hsv_to_rgb(value / 4, 1 - value, 0.5 + value / 2)
    )


@ruffus.files(["degree.txt", "size.txt", "roots.txt"], None)
@ruffus.follows(roots_for_degree)
def heatmap(input_filenames, output):
    degree = int(open(input_filenames[0], "rb").read())
    size = int(open(input_filenames[1], "rb").read())
    hits = hits_for_roots(input_filenames[2], size)
    
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
    
    open("degree.txt", "wb").write(degree)
    open("size.txt", "wb").write(size)
    
    ruffus.pipeline_run([heatmap])
    
    print "total time: {} seconds".format(round(time.time()) - start)


if __name__ == "__main__":
    degree = sys.argv[1]
    if len(sys.argv) == 3:
        size = sys.argv[2]
    else:
        size = "200"
    main(degree, size)
