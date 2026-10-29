"""Chạy các ca biên (file rỗng, 1 byte, 64 KiB cùng byte, 256 giá trị, ABABABA)
và kiểm tra rejected invalid magic. Ghi vào results/results_edge.csv.

Ca 'aaabdaaabac' với K = 3 là của BPE (Cặp 3), không chạy ở đây.
"""
import argparse
import importlib

from measure import measure
from results_schema import CsvWriter, h0_bits, throughput_kibs

CASES = {
    "edge_empty.bin": b"",
    "edge_1byte.bin": b"A",
    "edge_64kib_same.bin": b"\x41" * 65536,
    "edge_256_values.bin": bytes(range(256)),
    "edge_ABABABA.bin": b"ABABABA",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/results_edge.csv")
    ap.add_argument("--codecs", nargs="+", default=["rle", "huffman", "lzw"])
    a = ap.parse_args()
    writer = CsvWriter(a.out)
    for cname in a.codecs:
        try:
            codec = importlib.import_module(cname)
        except ModuleNotFoundError as e:
            if e.name != cname:
                raise
            print(f"[WARNING] module unavailable '{cname}', bỏ qua")
            continue
        # Magic sai phải bị từ chối
        good = codec.compress(b"hello hello hello")
        try:
            codec.decompress(b"XXXX" + good[4:])
            print(f"[LỖI] {cname}: không rejected invalid magic")
        except ValueError:
            print(f"[OK] {cname}: rejected invalid magic")
        else:
            raise RuntimeError(f"{cname}: codec không rejected invalid magic")
        for fname, data in CASES.items():
            r = measure(codec, data, repeats=1, with_mem=True)
            h0 = h0_bits(data)
            n = r["orig_bytes"]
            row = {
                "rq": "edge", "dataset": "", "file": fname, "state": "original", "codec": cname,
                "ratio": (r["comp_bytes"] / n) if n else None,
                "h0_bits": h0 if n else None, "h0_ratio": (h0 / 8) if n else None,
                "comp_kibs": throughput_kibs(n, r["comp_ms"]),
                "decomp_kibs": throughput_kibs(n, r["decomp_ms"]),
                **r, "status": "ok",
            }
            writer.write(row)
            print(f"[OK] {cname:8s} {fname:22s} {n} -> {r['comp_bytes']} byte")


if __name__ == "__main__":
    main()
