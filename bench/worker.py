"""Time cramjam.gzip on one file in this interpreter; print the best times."""
import sys
import time

import cramjam

data = open(sys.argv[1], "rb").read()
compressed = bytes(cramjam.gzip.compress(data))
assert bytes(cramjam.gzip.decompress(compressed)) == data


def best(fn, reps):
    times = []
    for _ in range(reps):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return min(times)


d = best(lambda: cramjam.gzip.decompress(compressed), 9)
c = best(lambda: cramjam.gzip.compress(data), 3)
print(len(data), len(compressed), c, d)
