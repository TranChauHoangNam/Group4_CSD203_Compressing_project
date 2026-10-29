"""Kiểm tra hợp đồng CSV chung bằng dữ liệu tổng hợp."""

import csv
from pathlib import Path
from typing import Any

import pytest

from common.results_schema import COLUMNS, append_row, finalize_row, sha16, validate_row

EXPECTED_COLUMNS = (
    "rq,dataset,file,state,size_kib,seed,codec,train_variant,k_merges,train_corpus,"
    "test_corpus,orig_bytes,comp_bytes,ratio,ratio_tokens_only,h0_bits,h0_ratio,"
    "n_tokens,bytes_per_token,comp_ms,decomp_ms,comp_kibs,decomp_kibs,train_ms,"
    "peak_mem_kib,output_check,roundtrip_ok,notes,status"
).split(",")


def sample_row() -> dict[str, Any]:
    """Tạo một dòng có các cột dẫn xuất tính tay được."""
    return {
        "rq": "2", "dataset": "R1", "file": "sample.bin", "state": "original",
        "codec": "huffman", "orig_bytes": 2048, "comp_bytes": 1024,
        "h0_bits": 4.0, "comp_ms": 10.0, "decomp_ms": 5.0,
        "output_check": sha16(b"abc"), "roundtrip_ok": True, "status": "ok", "notes": "mẫu, thử",
    }


@pytest.mark.parametrize("existing_empty", [False, True])
def test_append_header_derived_columns_and_width(tmp_path: Path, existing_empty: bool) -> None:
    """Header chỉ ghi một lần; mỗi dòng đủ 29 cột và đúng giá trị dẫn xuất."""
    path = tmp_path / "results.csv"
    if existing_empty:
        path.touch()
    row = sample_row()
    full = finalize_row(row)
    assert "ratio" not in row
    assert full["ratio"] == full["h0_ratio"] == 0.5
    assert full["comp_kibs"] == 200.0
    assert full["decomp_kibs"] == 400.0
    validate_row(full)
    append_row(str(path), row)
    append_row(str(path), row)
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    with path.open(newline="", encoding="utf-8") as stream:
        records = list(csv.reader(stream))
    assert records[0] == COLUMNS == EXPECTED_COLUMNS
    assert len(records) == 3
    assert all(len(record) == 29 for record in records)
    for record in records[1:]:
        parsed = dict(zip(COLUMNS, record))
        validate_row(parsed)
        assert parsed["ratio"] == parsed["h0_ratio"] == "0.5"
        assert parsed["comp_kibs"] == "200"
        assert parsed["decomp_kibs"] == "400"
        assert parsed["roundtrip_ok"] == "true"
        assert parsed["notes"] == "mẫu, thử"


@pytest.mark.parametrize("invalid", [
    {"rq": "4"}, {"output_check": "A" * 16}, {"output_check": "a" * 15},
    {"output_check": "a" * 17}, {"output_check": "g" * 16},
    {"output_check": None}, {"roundtrip_ok": False}, {"unknown_column": 1},
])
def test_reject_invalid_rows_without_writing(tmp_path: Path, invalid: dict[str, Any]) -> None:
    """Dòng sai bị từ chối trước khi thay đổi CSV đang có."""
    path = tmp_path / "results.csv"
    append_row(str(path), sample_row())
    before = path.read_bytes()
    row = {**sample_row(), **invalid}
    with pytest.raises(ValueError):
        validate_row(row)
    with pytest.raises(ValueError):
        append_row(str(path), row)
    assert path.read_bytes() == before


def test_sha16_known_vector() -> None:
    """Hash rút gọn dùng đúng 16 ký tự hex thường đầu của SHA-256."""
    assert sha16(b"abc") == "ba7816bf8f01cfea"
