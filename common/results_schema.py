"""Lược đồ CSV chung cho CSD203 Đề tài 4. Mỗi cặp import module này để ghi kết quả."""
from __future__ import annotations

import csv
import hashlib
import math
import os
import warnings
from typing import Any, Mapping

COLUMNS: list[str] = [
    "rq", "dataset", "file", "state", "size_kib", "seed", "codec",
    "train_variant", "k_merges", "train_corpus", "test_corpus",
    "orig_bytes", "comp_bytes", "ratio", "ratio_tokens_only",
    "h0_bits", "h0_ratio", "n_tokens", "bytes_per_token",
    "comp_ms", "decomp_ms", "comp_kibs", "decomp_kibs", "train_ms",
    "peak_mem_kib", "output_check", "roundtrip_ok", "notes", "status",
]
LEGACY_COLUMNS = COLUMNS[:-1]
STATUS_VALUES = {"ok", "timeout", "crash", "oom", "wrong"}
TIME_COLUMNS = ("comp_ms", "decomp_ms", "comp_kibs", "decomp_kibs", "train_ms")

RQ_VALUES = {"1", "2", "3", "edge"}
DATASETS = {"C1", "C2", "C3", "V1", "E1", "R1"}
STATES = {"original", "runs", "shuffled"}
CODECS = {"rle", "huffman", "lzw", "bpe"}
TRAIN_VARIANTS = {"inc", "noheap", "naive"}
SIZES_KIB = {256, 512, 1024, 2048, 4096}
K_VALUES = {256, 1024, 3840}


def sha16(data: bytes) -> str:
    """16 ký tự hex đầu của SHA-256 (cột output_check)."""
    return hashlib.sha256(data).hexdigest()[:16]


def _kibs(nbytes: int, ms: float | None) -> float | None:
    if ms is None or ms <= 0 or nbytes <= 0:
        return None
    return (nbytes / 1024) / (ms / 1000)


def finalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Điền các cột dẫn xuất còn thiếu (ratio, h0_ratio, throughput, bytes_per_token)."""
    r = dict(row)
    if r.get("status") != "ok":
        return r  # Do not invent derived measurements for failed/incomplete runs.
    orig, comp = r.get("orig_bytes"), r.get("comp_bytes")
    if r.get("ratio") in (None, "") and orig and comp not in (None, ""):
        r["ratio"] = comp / orig
    if r.get("h0_ratio") in (None, "") and r.get("h0_bits") not in (None, ""):
        r["h0_ratio"] = r["h0_bits"] / 8
    if r.get("comp_kibs") in (None, "") and orig:
        r["comp_kibs"] = _kibs(orig, r.get("comp_ms"))
    if r.get("decomp_kibs") in (None, "") and orig:
        r["decomp_kibs"] = _kibs(orig, r.get("decomp_ms"))
    if r.get("bytes_per_token") in (None, "") and orig and r.get("n_tokens"):
        r["bytes_per_token"] = orig / r["n_tokens"]
    return r


def validate_row(row: Mapping[str, Any]) -> None:
    """Raise ValueError nếu dòng vi phạm lược đồ."""
    extra = set(row) - set(COLUMNS)
    if extra:
        raise ValueError(f"Cột lạ: {sorted(extra)}")
    for col, allowed in (("rq", RQ_VALUES), ("dataset", DATASETS),
                         ("state", STATES), ("codec", CODECS)):
        if col == "dataset" and row.get("rq") == "edge" and row.get(col) in (None, ""):
            continue
        if str(row.get(col, "")) not in allowed:
            raise ValueError(f"{col}={row.get(col)!r} không hợp lệ (cho phép {sorted(allowed)})")
    tv = row.get("train_variant")
    if tv not in (None, "") and tv not in TRAIN_VARIANTS:
        raise ValueError(f"train_variant={tv!r} không hợp lệ")
    if row.get("size_kib") not in (None, "") and int(row["size_kib"]) not in SIZES_KIB:
        raise ValueError(f"size_kib={row['size_kib']!r} không hợp lệ")
    if (row.get("k_merges") not in (None, "")
            and int(row["k_merges"]) not in K_VALUES
            and not (row.get("rq") == "edge" and int(row["k_merges"]) == 3)):
        raise ValueError(f"k_merges={row['k_merges']!r} không hợp lệ")
    validate_status(row)


def validate_status(row: Mapping[str, Any]) -> None:
    """Status contract shared by both CSV writers; no implicit success."""
    status = row.get("status")
    if status not in STATUS_VALUES:
        raise ValueError(f"status={status!r} không hợp lệ")
    chk = row.get("output_check")
    valid_hash = isinstance(chk, str) and len(chk) == 16 and all(c in "0123456789abcdef" for c in chk)
    if status == "ok":
        if str(row.get("roundtrip_ok")).lower() != "true":
            raise ValueError("status=ok yêu cầu roundtrip_ok=true")
        if not valid_hash:
            raise ValueError("output_check phải gồm đúng 16 ký tự hex thường")
        for col in ("orig_bytes", "comp_bytes"):
            if row.get(col) in (None, "") or int(row[col]) < 0:
                raise ValueError(f"Thiếu hoặc sai {col}")
        for col in ("comp_ms", "decomp_ms"):
            try:
                value = float(row.get(col))
            except (TypeError, ValueError):
                raise ValueError(f"status=ok yêu cầu {col}") from None
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{col} phải hữu hạn và không âm")
        for col in ("comp_kibs", "decomp_kibs", "train_ms"):
            if row.get(col) not in (None, ""):
                value = float(row[col])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"{col} phải hữu hạn và không âm")
        if int(row["orig_bytes"]) == 0 and any(row.get(c) not in (None, "") for c in ("comp_kibs", "decomp_kibs")):
            raise ValueError("Throughput phải trống với input rỗng")
    else:
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            raise ValueError("status khác ok yêu cầu notes mô tả nguyên nhân")
        if any(row.get(c) not in (None, "") for c in TIME_COLUMNS):
            raise ValueError("Thời gian/throughput phải trống khi status khác ok")
        if status == "wrong":
            if str(row.get("roundtrip_ok")).lower() != "false":
                raise ValueError("status=wrong yêu cầu roundtrip_ok=false")
            if chk not in (None, "") and not valid_hash:
                raise ValueError("output_check sai định dạng")
        elif row.get("roundtrip_ok") not in (None, "") or chk not in (None, ""):
            raise ValueError("timeout/crash/oom yêu cầu roundtrip_ok và output_check trống")


def is_ok(row: Mapping[str, Any], context: str = "CSV") -> bool:
    """Analysis gate; retain original row indices by calling before aggregation."""
    status = row.get("status")
    if status not in STATUS_VALUES:
        raise ValueError(f"{context}: invalid/missing status={status!r}")
    if status != "ok":
        validate_status(row)
        warnings.warn(f"{context}: excluded status={status}: {row.get('notes')}", stacklevel=2)
        return False
    return True


def require_ok_rows(rows):
    """Fixed-matrix report/check consumers must not silently use failed runs."""
    for line, row in enumerate(rows, 2):
        if not is_ok(row, f"CSV line {line}"):
            raise ValueError(f"CSV line {line}: report requires status=ok")
    return rows


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def append_row(path: str, row: Mapping[str, Any]) -> None:
    """Hoàn thiện, kiểm tra rồi ghi nối một dòng (tự tạo header nếu file chưa có)."""
    full = finalize_row(row)
    validate_row(full)
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    if not new_file:
        with open(path, newline="", encoding="utf-8") as f:
            if next(csv.reader(f), []) != COLUMNS:
                raise ValueError("Header CSV không khớp schema; migrate trước khi append")
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new_file:
            w.writerow(COLUMNS)
        w.writerow([_fmt(full.get(c)) for c in COLUMNS])
