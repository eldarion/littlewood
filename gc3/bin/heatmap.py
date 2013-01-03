import array
import colorsys
import glob
import struct
import sys
import zlib

import numpy


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


def hits_for_roots(size):
    hits = numpy.zeros((int(size * 2.1), int(size * 1.5)), dtype=numpy.int)
    for input_filename in glob.glob("*.root"):
        roots = open(input_filename, "rb").readlines()
        for root in roots:
            r, i = root.strip().split()
            x = round(float(r) * size)
            y = round(float(i) * size)
            hits[x, y] += 1
    return hits


def heatmap(size):
    hits = hits_for_roots(size)
    hit_to_rgb = {}
    width = int(size * 4)
    height = int(size * 2 * numpy.sqrt(2))
    log_max = numpy.log(numpy.amax(hits))
    with open("littlewood.png", "wb") as f:
        f.write(struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10))
        data = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
        output_chunk(f, "IHDR", data)
        compressor = zlib.compressobj()
        data = array.array("B")
        for py in range(height):
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


if __name__ == "__main__":
    heatmap(int(sys.argv[1]))