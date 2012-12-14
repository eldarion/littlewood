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


INNER_ONLY = False


def roots_for_poly(poly):
    roots = []
    for root in numpy.roots((1,) + poly):
        if root.real >= 0 and root.imag >= 0:
            if not INNER_ONLY or abs(root) <= 1:
                roots.append((root.real, root.imag))
    return roots


def roots_for_degree(degree):
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
    return roots


def output_chunk(f, chunk_type, data):
    f.write(struct.pack("!I", len(data)))
    f.write(chunk_type)
    f.write(data)
    checksum = zlib.crc32(data, zlib.crc32(chunk_type))
    f.write(struct.pack("!i", checksum))


def hits_for_roots(roots, size):
    hits = numpy.zeros((int(size * 2.1), int(size * 1.5)), dtype=numpy.int)
    for root in roots:
        x = round(float(root[0]) * size)
        y = round(float(root[1]) * size)
        hits[x, y] += 1
    return hits


def rgb_for_value(value):
    return (
        int(255 * x)
        for x in colorsys.hsv_to_rgb(value / 4, 1 - value, 0.5 + value / 2)
    )


def heatmap(degree, roots, size):
    hits = hits_for_roots(roots, size)
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


def main(degree):
    print "generating roots for degree={}".format(degree,)

    start = time.time()

    roots = roots_for_degree(degree)

    print >> sys.stderr, "created {} roots in {} seconds".format(
        len(roots),
        time.time() - start
    )
    
    heatmap_start = time.time()
    
    print "writing out PNG..."
    
    filename = heatmap(degree, roots, 200)
    
    print "wrote out {} in {} seconds".format(
        filename,
        round(time.time() - heatmap_start)
    )
    
    print "total time: {} seconds".format(round(time.time()) - start)


if __name__ == "__main__":
    main(int(sys.argv[1]))
