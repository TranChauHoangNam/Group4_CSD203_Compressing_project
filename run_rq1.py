"""Chạy RQ1: RLE / Huffman / LZW trên C1, C2, C3, V1 với S = 256 KiB ... 4 MiB.

Ví dụ:
  python run_rq1.py --data-dir data --out results/results_rq1.csv
  python run_rq1.py --codecs rle lzw --repeats 1 --sizes 256 512      # chạy thử nhanh

Có thể ngắt rồi chạy lại: dòng đã ghi (cùng file + codec) sẽ được bỏ qua.
Codec không có module (vd. huffman.py của Cặp 2 chưa nộp) sẽ bị bỏ qua kèm cảnh báo.
Module codec cần có: compress(data: bytes) -> bytes, decompress(blob: bytes) -> bytes.
"""
import argparse
import importlib
from pathlib import Path

import gen_synthetic
from measure import measure
from results_schema import CsvWriter, h0_bits, throughput_kibs


def load_codec(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name == name:
            return None
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="results/results_rq1.csv")
    ap.add_argument("--codecs", nargs="+", default=["rle", "huffman", "lzw"])
    ap.add_argument("--families", nargs="+", default=["C1", "C2", "C3", "V1"])
    ap.add_argument("--sizes", type=int, nargs="+", default=list(gen_synthetic.SIZES_KIB), help="KiB")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(gen_synthetic.SEEDS))
    ap.add_argument("--repeats", type=int, default=3, help="số lần đo thời gian, lấy trung vị")
    ap.add_argument("--no-mem", action="store_true", help="bỏ đo bộ nhớ (nhanh hơn)")
    a = ap.parse_args()

    data_dir = Path(a.data_dir)
    codecs = {}
    for name in a.codecs:
        m = load_codec(name)
        if m is None:
            print(f"[WARNING] module unavailable '{name}', bỏ qua codec này")
        else:
            codecs[name] = m

    writer = CsvWriter(a.out)
    done = writer.done_keys()

    jobs = []  # (dataset, size_kib, seed hoặc None, đường dẫn file)
    for fam in a.families:
        for s in a.sizes:
            if fam == "V1":
                jobs.append((fam, s, None, data_dir / "wiki" / f"v1_{s}kib.txt"))
            else:
                for sd in a.seeds:
                    jobs.append((fam, s, sd, None))

    for fam, s, sd, path in jobs:
        if path is None:
            path = gen_synthetic.ensure_file(fam, s, sd, data_dir / "synthetic")
        if not path.exists():
            print(f"[WARNING] missing {path} (chạy prepare_wiki.py trước), bỏ qua")
            continue
        todo = [c for c in codecs if (path.name, c) not in done]
        if not todo:
            continue
        data = path.read_bytes()
        h0 = h0_bits(data)
        for cname in todo:
            r = measure(codecs[cname], data, repeats=a.repeats, with_mem=not a.no_mem)
            row = {
                "rq": "1", "dataset": fam, "file": path.name, "state": "original",
                "size_kib": s, "seed": sd, "codec": cname,
                "ratio": r["comp_bytes"] / r["orig_bytes"],
                "h0_bits": h0, "h0_ratio": h0 / 8,
                "comp_kibs": throughput_kibs(r["orig_bytes"], r["comp_ms"]),
                "decomp_kibs": throughput_kibs(r["orig_bytes"], r["decomp_ms"]),
                **r,
            }
            writer.write(row)
            print(f"{path.name:28s} {cname:8s} ratio={row['ratio']:.4f} "
                  f"comp={r['comp_ms']:.0f}ms decomp={r['decomp_ms']:.0f}ms")


if __name__ == "__main__":
    main()
