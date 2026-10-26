"""Kiem chung co che cho ket qua RQ2 tren du lieu that trong data/."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from statistics import mean

FILES = ["alice29.txt", "kennedy.xls", "v1_test_1mib.txt"]


def lzw_full_position(sorted_data: bytes):
    """Chi so byte (bat dau tu 0) tai do tu dien LZW 4096 muc day, hoac None."""
    if not sorted_data:
        return None
    table, nxt, w = {}, 256, sorted_data[0]
    for i in range(1, len(sorted_data)):
        b = sorted_data[i]
        k = (w << 8) | b
        c = table.get(k)
        if c is not None:
            w = c
            continue
        if nxt < 4096:
            table[k] = nxt
            nxt += 1
            if nxt == 4096:
                return i
        w = b
    return None


def inspect_data(d):
    n = len(d)
    if not n:
        raise ValueError("Khong phan tich file rong")
    cnt = Counter(d)
    sum_p2 = sum((c / n) ** 2 for c in cnt.values())
    runs_orig = 1 + sum(d[i] != d[i - 1] for i in range(1, n))
    return dict(n=n, distinct=len(cnt), sum_p2=sum_p2, runs_orig=runs_orig,
                shuffled_prediction=2 * (1 - sum_p2), original_prediction=2 * runs_orig / n,
                pos=lzw_full_position(bytes(sorted(d))), original_pos=lzw_full_position(d))


def render(data_dir, csv_path):
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    lines = ["[DO DUOC] Nguon ratio: " + csv_path.as_posix(),
             "Quy uoc: delta = CSV - du doan; KHOP neu abs(delta) < 0.05 (nguong doi chieu, khong phai kiem dinh).",
             "LZW: chi so byte bat dau tu 0; delta ratio = runs - original; khong phai du doan ratio."]
    seeds = sorted({int(r["seed"]) for r in rows if r["seed"]})
    lines.append(f"CSV: {len(rows)} dong; {len(rows[0])} cot; {len(FILES)} file; "
                 f"{len({r['state'] for r in rows})} state; {len({r['codec'] for r in rows})} codec; seeds = {seeds}")
    protocol = Path("rq2/run_logs/official.json")
    if protocol.exists():
        repeats = json.loads(protocol.read_text(encoding="utf-8"))["repeats"]
        lines.append(f"Thiet lap tu log official.json (khong do lai): repeats = {repeats}; lay trung vi thoi gian.")
    lines.append("Hang so dinh dang trong ma chi doc: Huffman header = 268 byte; LZW = 4096 muc; RLE header = 12 byte, count toi da = 255.")
    for name in FILES:
        p = data_dir / name
        if not p.exists():
            lines.append(f"[bo qua] khong thay {p}")
            continue
        m = inspect_data(p.read_bytes())
        n, cnt, sum_p2, runs_orig, pos = m['n'], m['distinct'], m['sum_p2'], m['runs_orig'], m['pos']

        def ratio(codec, state):
            values = [float(r['ratio']) for r in rows if (r['file'], r['codec'], r['state']) == (name, codec, state)]
            if not values:
                raise ValueError(f"CSV thieu {name}/{codec}/{state}")
            return mean(values)

        def comparison(predicted, actual):
            delta = actual - predicted
            return f"CSV = {actual:.6g}; delta = {delta:.6g}; {'KHOP' if abs(delta) < .05 else 'LECH'}"

        lines.append(f"\n== {name}: {n} byte, {cnt} gia tri byte khac nhau ==")
        lines.append(f"  sum(p^2) = {sum_p2:.4f}  ->  RLE ky vong khi xao tron ~ 2*(1-sum p^2) = {2*(1-sum_p2):.4f}; " + comparison(m['shuffled_prediction'], ratio('rle', 'shuffled')))
        lines.append(f"  so run o du lieu goc = {runs_orig}  (RLE goc ~ 2*run/n = {2*runs_orig/n:.4f}, chua tinh tach run > 255); " + comparison(m['original_prediction'], ratio('rle', 'original')))
        if pos is None:
            lines.append("  LZW 'runs': tu dien KHONG day")
        else:
            lines.append(f"  LZW 'runs': tu dien day tai byte {pos} ({100*pos/n:.0f}% du lieu); {100*(1-pos/n):.0f}% du lieu sau do dung tu dien dong bang")
        # Khong suy ra ratio tu vi tri day: doi chieu hai phep do doc lap.
        lines[-1] += (f"; CSV runs = {ratio('lzw', 'runs'):.6g}; CSV original = {ratio('lzw', 'original'):.6g}; "
                      f"delta ratio = {ratio('lzw', 'runs') - ratio('lzw', 'original'):.6g}")
        lines.append(f"  LZW 'original': vi tri day = {m['original_pos']}; chi do thoi diem day, chua kiem chung nhan qua.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", nargs="?", type=Path, default=Path("data"))
    parser.add_argument("--csv", type=Path, default=Path("results_rq2_all.csv"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    output = render(args.data_dir, args.csv)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
