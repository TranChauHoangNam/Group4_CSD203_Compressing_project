"""Sinh dữ liệu tổng hợp C1, C2, C3 (có seed, tái lập được).

C1: run dài, độ dài run trung bình 32 byte (phân bố hình học), hai run liền kề luôn khác byte.
C2: 1.000 "từ" theo quy luật Zipf (s = 1), ngăn cách bằng dấu cách.
C3: byte ngẫu nhiên đều (bất khả nén).

Tên file: {họ}_{kích thước byte}_s{seed}.bin, ví dụ C2_1048576_s1.bin
"""
import argparse
import math
import random
import string
from itertools import accumulate
from pathlib import Path

SIZES_KIB = (256, 512, 1024, 2048, 4096)
SEEDS = (1, 2, 3)


def make_c1(size: int, seed: int, mean_run: int = 32) -> bytes:
    rng = random.Random(f"C1-{seed}")
    p = 1.0 / mean_run
    log_q = math.log(1.0 - p)
    out = bytearray()
    prev = -1
    while len(out) < size:
        u = 1.0 - rng.random()  # thuộc (0, 1]
        run = 1 + int(math.log(u) / log_q)  # kỳ vọng = 1/p = mean_run
        b = rng.randrange(256)
        if b == prev:
            b = (b + 1 + rng.randrange(255)) % 256
        out += bytes((b,)) * run
        prev = b
    return bytes(out[:size])


def make_c2(size: int, seed: int, vocab_size: int = 1000) -> bytes:
    rng = random.Random(f"C2-{seed}")
    vocab, seen = [], set()
    while len(vocab) < vocab_size:
        w = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(2, 9)))
        if w not in seen:
            seen.add(w)
            vocab.append(w)  # vocab[0] là hạng 1
    cum = list(accumulate(1.0 / r for r in range(1, vocab_size + 1)))  # Zipf s = 1
    out = bytearray()
    while len(out) < size:
        words = rng.choices(vocab, cum_weights=cum, k=4096)
        out += (" ".join(words) + " ").encode("ascii")
    return bytes(out[:size])


def make_c3(size: int, seed: int) -> bytes:
    return random.Random(f"C3-{seed}").randbytes(size)


MAKERS = {"C1": make_c1, "C2": make_c2, "C3": make_c3}


def make(family: str, size: int, seed: int) -> bytes:
    return MAKERS[family](size, seed)


def file_name(family: str, size: int, seed: int) -> str:
    return f"{family}_{size}_s{seed}.bin"


def ensure_file(family: str, size_kib: int, seed: int, out_dir) -> Path:
    """Trả về đường dẫn file, tạo nếu chưa có."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    size = size_kib * 1024
    path = out_dir / file_name(family, size, seed)
    if not path.exists():
        path.write_bytes(make(family, size, seed))
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="data/synthetic")
    ap.add_argument("--sizes-kib", type=int, nargs="+", default=list(SIZES_KIB))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--families", nargs="+", default=["C1", "C2", "C3"])
    a = ap.parse_args()
    for fam in a.families:
        for s in a.sizes_kib:
            for sd in a.seeds:
                p = ensure_file(fam, s, sd, a.out_dir)
                print(p)


if __name__ == "__main__":
    main()
