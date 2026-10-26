"""Lược đồ CSV 28 cột + hàm ghi dòng có kiểm tra (bản thay thế tạm cho results_schema.py
của nhóm nếu chưa có; cột và thứ tự đúng theo csv_schema.md).

Quy ước: UTF-8 không BOM, phân cách phẩy, LF, ô không áp dụng để TRỐNG.
Không ghi dòng nếu round-trip sai (roundtrip_ok phải là True).
"""
import csv
import math
import re
from collections import Counter
from pathlib import Path

COLUMNS = [
    "rq", "dataset", "file", "state", "size_kib", "seed", "codec", "train_variant",
    "k_merges", "train_corpus", "test_corpus", "orig_bytes", "comp_bytes", "ratio",
    "ratio_tokens_only", "h0_bits", "h0_ratio", "n_tokens", "bytes_per_token",
    "comp_ms", "decomp_ms", "comp_kibs", "decomp_kibs", "train_ms", "peak_mem_kib",
    "output_check", "roundtrip_ok", "notes",
]
assert len(COLUMNS) == 28

ALLOWED = {
    "rq": {"1", "2", "3", "edge"},
    "dataset": {"", "C1", "C2", "C3", "V1", "E1", "R1"},  # ca biên để trống dataset
    "state": {"", "original", "runs", "shuffled"},
    "codec": {"rle", "huffman", "lzw", "bpe"},
    "train_variant": {"", "inc", "noheap", "naive"},
}
FLOAT_COLS = {"ratio", "ratio_tokens_only", "h0_bits", "h0_ratio", "bytes_per_token", "comp_ms",
              "decomp_ms", "comp_kibs", "decomp_kibs", "train_ms", "peak_mem_kib"}


def h0_bits(data: bytes) -> float:
    """Entropy bậc 0 (bit/byte): H0 = -sum p_i log2 p_i."""
    n = len(data)
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in Counter(data).values())


def throughput_kibs(orig_bytes: int, ms: float):
    if orig_bytes <= 0 or ms is None or ms <= 0:
        return None
    return (orig_bytes / 1024) / (ms / 1000)


def _fmt(col, v):
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if col in FLOAT_COLS:
        return f"{float(v):.6f}"
    return str(v)


def validate(row: dict):
    unknown = set(row) - set(COLUMNS)
    if unknown:
        raise ValueError(f"Cột lạ: {sorted(unknown)}")
    for col, ok in ALLOWED.items():
        v = str(row.get(col) if row.get(col) is not None else "")
        if v not in ok:
            raise ValueError(f"Giá trị '{v}' không hợp lệ cho cột {col}")
    if row.get("roundtrip_ok") is not True:
        raise ValueError("roundtrip_ok phải là True; sai round-trip thì dừng và sửa lỗi, không ghi số liệu")
    if not re.fullmatch(r"[0-9a-f]{16}", str(row.get("output_check", ""))):
        raise ValueError("output_check phải là 16 ký tự hex")
    for col in ("rq", "file", "codec", "orig_bytes", "comp_bytes"):
        if row.get(col) in (None, ""):
            raise ValueError(f"Thiếu cột bắt buộc {col}")


class CsvWriter:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f, lineterminator="\n").writerow(COLUMNS)
        else:
            with open(self.path, newline="", encoding="utf-8-sig") as f:
                header = next(csv.reader(f), [])
            if header != COLUMNS:
                raise ValueError(
                    f"Header CSV không khớp schema 28 cột: {self.path}. "
                    "Hãy dùng file mới hoặc sao lưu file cũ trước khi chạy."
                )

    def write(self, row: dict):
        validate(row)
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f, lineterminator="\n").writerow([_fmt(c, row.get(c)) for c in COLUMNS])

    def done_keys(self, key_cols=("file", "codec")):
        """Tập khóa các dòng đã ghi (để chạy tiếp khi bị ngắt giữa chừng)."""
        keys = set()
        with open(self.path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                keys.add(tuple(r[c] for c in key_cols))
        return keys
