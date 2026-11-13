"""Compare cramjam.gzip in two virtualenvs (base and PR builds)."""
import os
import platform
import random
import subprocess
import sys

SIZE = 48 * 1024 * 1024
ROUNDS = 5


def fastq(path):
    rng = random.Random(0)
    acgt = bytes(b"ACGT"[i & 3] for i in range(256))
    qual = bytes(b"FFFFFFFFFFFF::,#"[i & 15] for i in range(256))
    with open(path, "wb") as f:
        n = i = 0
        while n < SIZE:
            rec = b"@read%d/1\n%s\n+\n%s\n" % (
                i, rng.randbytes(150).translate(acgt), rng.randbytes(150).translate(qual))
            f.write(rec)
            n += len(rec)
            i += 1


def json_lines(path):
    rng = random.Random(1)
    words = [("w%x" % rng.getrandbits(40)).encode() for _ in range(5000)]
    with open(path, "wb") as f:
        n = i = 0
        while n < SIZE:
            rec = b'{"id": %d, "user": "%s", "tags": ["%s", "%s"], "score": %d.%d, "ok": true}\n' % (
                i, rng.choice(words), rng.choice(words), rng.choice(words),
                rng.randrange(1000), rng.randrange(100))
            f.write(rec)
            n += len(rec)
            i += 1


def incompressible(path):
    with open(path, "wb") as f:
        f.write(random.Random(2).randbytes(SIZE))


def main():
    base, pr = sys.argv[1], sys.argv[2]
    print("machine:", platform.machine(), platform.platform())
    if sys.platform == "darwin":
        print("cpu:", subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                     capture_output=True, text=True).stdout.strip())
    else:
        print("cpu:", subprocess.run("lscpu | grep -E 'Model name|Vendor ID|BIOS Model' | tr -s ' '",
                                     shell=True, capture_output=True, text=True).stdout.strip())
    for name, py in (("base", base), ("pr", pr)):
        v = subprocess.run([py, "-c", "import cramjam; print(cramjam.__version__)"],
                           capture_output=True, text=True, check=True).stdout.strip()
        print(f"{name}: cramjam {v}")

    print("| data | gzip size | decompress base MB/s | decompress PR MB/s | speedup | compress base MB/s | compress PR MB/s | speedup |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, make in (("FASTQ", fastq), ("JSON lines", json_lines), ("random bytes", incompressible)):
        path = name.replace(" ", "_") + ".bin"
        make(path)
        best = {"base": [1e9, 1e9], "pr": [1e9, 1e9]}
        for _ in range(ROUNDS):
            for label, py in (("base", base), ("pr", pr)):
                out = subprocess.run([py, "bench/worker.py", path], capture_output=True,
                                     text=True, check=True).stdout.split()
                n, csize, c, d = int(out[0]), int(out[1]), float(out[2]), float(out[3])
                best[label][0] = min(best[label][0], c)
                best[label][1] = min(best[label][1], d)
        mb = n / 1e6
        (bc, bd), (pc, pd) = best["base"], best["pr"]
        print(f"| {name} | {csize / n:.0%} | {mb / bd:.0f} | {mb / pd:.0f} | {bd / pd:.2f}x "
              f"| {mb / bc:.0f} | {mb / pc:.0f} | {bc / pc:.2f}x |")
        os.remove(path)


main()
