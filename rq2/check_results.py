"""Kiểm tra chín điều kiện RQ2; chạy từ gốc bằng python -m rq2.check_results."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import math
from pathlib import Path
import re

from common.results_schema import COLUMNS, sha16, validate_row

FILES = ("alice29.txt", "kennedy.xls", "v1_test_1mib.txt")
CODECS = ("huffman", "lzw", "rle")


def check_results(csv_path: Path, data_dir: Path, seeds: list[int], runner_log: Path):
    """Giữ tám mục cũ, thêm đối chiếu hash original với dữ liệu thật."""
    with csv_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        header = reader.fieldnames
    results = []

    def record(number, title, errors):
        results.append({"item": number, "title": title, "ok": not errors, "errors": errors})

    expected = len(FILES) * (2 + len(seeds)) * len(CODECS)
    record(1, f"Số dòng: {len(rows)}/{expected}",
           [] if len(rows) == expected else [f"Cần {expected}, nhận {len(rows)}"])
    errors = []
    if header != COLUMNS:
        errors.append("Header không khớp chính xác 28 cột")
    if not seeds or len(set(seeds)) != len(seeds):
        errors.append("Danh sách seed phải khác rỗng, không trùng")
    expected_keys = {
        (file, codec, state, seed)
        for file in FILES for codec in CODECS
        for state, seed in [("original", ""), ("runs", "")] +
        [("shuffled", str(seed)) for seed in seeds]
    }
    actual_keys = Counter((r.get("file"), r.get("codec"), r.get("state"), r.get("seed")) for r in rows)
    if set(actual_keys) != expected_keys or any(n != 1 for n in actual_keys.values()):
        errors.append("Ma trận file/codec/state/seed thiếu, thừa hoặc trùng")
    sizes = {file: (data_dir / file).stat().st_size for file in FILES}
    for line, row in enumerate(rows, 2):
        try:
            validate_row(row)
            if row["rq"] != "2" or row["dataset"] != "R1":
                raise ValueError("rq/dataset không phải 2/R1")
            if int(row["orig_bytes"]) != sizes.get(row["file"]):
                raise ValueError("orig_bytes khác file dữ liệu")
            if int(row["comp_bytes"]) < 0:
                raise ValueError("comp_bytes âm")
            for col in ("ratio", "h0_bits", "h0_ratio", "comp_ms", "decomp_ms",
                        "comp_kibs", "decomp_kibs", "peak_mem_kib"):
                value = float(row[col])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"{col} không hữu hạn hoặc âm")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"Dòng {line}: {exc}")
    record(2, "Header, schema và ma trận codec/state/seed", errors)
    errors = [f"Dòng {i}: roundtrip_ok/output_check sai" for i, r in enumerate(rows, 2)
              if r.get("roundtrip_ok") != "true" or
              not re.fullmatch(r"[0-9a-f]{16}", r.get("output_check") or "")]
    record(3, "Round-trip true và output_check 16 hex", errors)

    for number, title in [(4, "H0 không đổi, sai số < 1e-9"),
                          (5, "Huffman có cùng comp_bytes tuyệt đối")]:
        errors = []
        for file in FILES:
            group = [r for r in rows if r.get("file") == file and
                     (number == 4 or r.get("codec") == "huffman")]
            try:
                values = [float(r["h0_bits"]) if number == 4 else int(r["comp_bytes"]) for r in group]
                if not values or any(not math.isfinite(v) for v in values):
                    raise ValueError("Thiếu giá trị hữu hạn")
                if (max(values) - min(values) >= 1e-9) if number == 4 else len(set(values)) != 1:
                    raise ValueError(f"Giá trị không bằng nhau: {values}")
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(f"{file}: {exc}")
        record(number, title, errors)

    errors = []
    for r in rows:
        if r.get("codec") != "huffman":
            continue
        try:
            h0 = float(r["h0_ratio"])
            ratio = float(r["ratio"])
            payload = (int(r["comp_bytes"]) - 268) / int(r["orig_bytes"])
            if not all(math.isfinite(x) for x in (h0, ratio, payload)) or ratio < h0 or payload < h0 - 1e-6:
                raise ValueError(f"ratio={ratio}, payload={payload}, H0/8={h0}")
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            errors.append(f"{r.get('file')}/{r.get('state')}: {exc}")
    record(6, "Huffman không thấp hơn mốc H0/8", errors)

    bounds = {file: 12 + 2 * sum((n + 254) // 255 for n in Counter((data_dir / file).read_bytes()).values())
              for file in FILES}
    errors = []
    for r in rows:
        if r.get("codec") != "rle":
            continue
        try:
            comp = int(r["comp_bytes"])
            bound = bounds[r["file"]] if r["state"] == "runs" else 12 + 2 * int(r["orig_bytes"])
            if (comp != bound) if r["state"] == "runs" else comp > bound:
                raise ValueError(f"comp_bytes={comp}, giới hạn={bound}")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"{r.get('file')}/{r.get('state')}: {exc}")
    record(7, "RLE runs đúng công thức; original/shuffled không vượt giới hạn", errors)

    log = runner_log.read_text(encoding="utf-8")
    errors = []
    for required in (f"Số dòng đã ghi: {expected}; số dòng kỳ vọng: {expected}",
                     "Codec đã chạy: huffman, rle, lzw", "Codec bị bỏ qua: không có", "File bị bỏ qua: không có"):
        if required not in log:
            errors.append(f"Thiếu xác nhận trong log: {required}")
    if "Cảnh báo:" in log or "Lỗi" in log:
        errors.append("Log chứa cảnh báo hoặc lỗi")
    record(8, "Log runner hoàn tất, không bỏ qua file/codec", errors)
    digests = {file: sha16((data_dir / file).read_bytes()) for file in FILES}
    errors = [
        f"Dòng {line}: {row.get('file')}/{row.get('codec')}/original: "
        f"output_check={row.get('output_check')}, sha16(data)={digests.get(row.get('file'))}"
        for line, row in enumerate(rows, 2)
        if row.get("state") == "original"
        and row.get("output_check") != digests.get(row.get("file"))
    ]
    record(9, "output_check original bằng sha16 của file trong data/", errors)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("results_rq2_all.csv"))
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--runner-log", type=Path, default=Path("rq2/run_logs/official.log"))
    args = parser.parse_args(argv)
    try:
        results = check_results(args.csv, args.data_dir, args.seeds, args.runner_log)
    except FileNotFoundError as exc:
        missing = Path(exc.filename) if exc.filename else None
        if missing in {args.data_dir / file for file in FILES}:
            print(f"Missing data file: {missing}. See README 'Data' section.")
            return 2
        print(f"KH\u00d4NG \u0110\u1ea0T: kh\u00f4ng \u0111\u1ecdc \u0111\u01b0\u1ee3c \u0111\u1ea7u v\u00e0o: {exc}")
        return 1
    except (OSError, ValueError, csv.Error) as exc:
        print(f"KHÔNG ĐẠT: không đọc được đầu vào: {exc}")
        return 1
    for result in results:
        print(f"{'ĐẠT' if result['ok'] else 'KHÔNG ĐẠT'} {result['item']}. {result['title']}")
        for error in result["errors"]:
            print(f"  {error}")
    if not results[4]["ok"]:
        print("LỖI NGHIÊM TRỌNG: kích thước Huffman thay đổi; dừng phân tích.")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
