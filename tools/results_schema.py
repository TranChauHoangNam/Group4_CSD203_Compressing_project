"""Lược đồ CSV 29 cột; dùng validator chung, giữ cách định dạng số Cặp 1.

Quy ước: UTF-8 không BOM, phân cách phẩy, LF, ô không áp dụng để TRỐNG.
Status bắt buộc; chỉ status=ok có thời gian và tốc độ.
"""
import csv
import math
from collections import Counter
from pathlib import Path

from common.results_schema import COLUMNS, validate_row

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
    validate_row(row)


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
                    f"Header CSV không khớp schema 29 cột: {self.path}. "
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
                validate_row(r)
                if r["status"] == "ok":
                    keys.add(tuple(r[c] for c in key_cols))
        return keys
