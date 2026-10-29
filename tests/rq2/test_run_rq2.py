"""Kiểm tra runner bằng tmp_path và codec stub, không dùng dữ liệu R1 thật."""

from __future__ import annotations

import csv
import os
import random
import subprocess
import sys
import tracemalloc
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest

from common.results_schema import COLUMNS, sha16, validate_row
from rq2 import run_rq2
from rq2.reorder import counting_sort_runs, fisher_yates


@pytest.fixture(autouse=True)
def absent_optional_codecs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test mặc định không phụ thuộc RLE/LZW được cài trên máy chạy."""
    monkeypatch.setitem(sys.modules, "rle", None)
    monkeypatch.setitem(sys.modules, "lzw", None)


def make_data(tmp_path: Path, count: int = 3) -> tuple[Path, dict[str, bytes]]:
    """Tạo các tên file R1 với dữ liệu nhỏ, cố định."""
    directory = tmp_path / "data"
    directory.mkdir()
    samples = [b"banana bread" * 10, bytes(range(256)), random.Random(203).randbytes(512)]
    data = dict(zip(run_rq2.R1_FILES[:count], samples[:count]))
    for name, content in data.items():
        (directory / name).write_bytes(content)
    return directory, data


def read_rows(path: Path) -> list[dict[str, str]]:
    """Đọc CSV đồng thời kiểm tra header, độ rộng và từng dòng."""
    with path.open(newline="", encoding="utf-8") as stream:
        records = list(csv.reader(stream))
    assert records[0] == COLUMNS
    assert all(len(record) == 29 for record in records)
    rows = [dict(zip(COLUMNS, record)) for record in records[1:]]
    for row in rows:
        validate_row(row)
    return rows


def install_stub(
    monkeypatch: pytest.MonkeyPatch, name: str,
    decoder: Callable[[bytes], bytes] | None = None,
) -> None:
    """Đăng ký module stub giữ nguyên dữ liệu sau tiền tố, không cài RLE/LZW."""
    module = ModuleType(name)
    module.compress = lambda data: b"STUB" + data
    module.decompress = decoder or (lambda blob: blob[4:])
    monkeypatch.setitem(sys.modules, name, module)


def test_huffman_nine_rows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Ba file × ba trạng thái, seed/hash/notes đúng và H0 bất biến."""
    directory, data = make_data(tmp_path)
    out = tmp_path / "results.csv"
    assert run_rq2.main(["--data-dir", str(directory), "--out", str(out)]) == 0
    rows = read_rows(out)
    assert len(rows) == 9
    assert {row["state"] for row in rows} == {"original", "runs", "shuffled"}
    assert {row["codec"] for row in rows} == {"huffman"}
    for row in rows:
        original = data[row["file"]]
        assert row["rq"] == "2" and row["dataset"] == "R1"
        assert row["seed"] == ("1" if row["state"] == "shuffled" else "")
        expected = {
            "original": original, "runs": counting_sort_runs(original),
            "shuffled": fisher_yates(original, 1),
        }[row["state"]]
        assert row["output_check"] == sha16(expected)
        ratio = (int(row["comp_bytes"]) - 268) / len(original)
        assert row["notes"] == f"ratio_no_header={ratio:.6f}"
        assert float(row["ratio"]) == pytest.approx(int(row["comp_bytes"]) / len(original), rel=1e-5)
        assert float(row["peak_mem_kib"]) > 0
        assert all(row[key] == "" for key in (
            "size_kib", "train_variant", "k_merges", "train_corpus", "test_corpus",
            "ratio_tokens_only", "n_tokens", "bytes_per_token", "train_ms",
        ))
    for name in data:
        entropies = [float(row["h0_bits"]) for row in rows if row["file"] == name]
        assert max(entropies) - min(entropies) < 1e-9
    output = capsys.readouterr()
    assert "Số dòng đã ghi: 9; số dòng kỳ vọng: 9" in output.out
    assert "Codec đã chạy: huffman" in output.out
    for codec in ("rle", "lzw"):
        assert f"bỏ qua codec {codec}: chưa có module" in output.err


def test_multiple_seeds(tmp_path: Path) -> None:
    """Ba seed sinh ba dòng shuffled cho mỗi file và codec."""
    directory, data = make_data(tmp_path)
    out = tmp_path / "results.csv"
    assert run_rq2.main([
        "--data-dir", str(directory), "--out", str(out), "--seeds", "1", "2", "3",
    ]) == 0
    rows = read_rows(out)
    assert len(rows) == 15
    for name, original in data.items():
        shuffled = [row for row in rows if row["file"] == name and row["state"] == "shuffled"]
        assert len(shuffled) == 3
        assert {row["seed"] for row in shuffled} == {"1", "2", "3"}
        for row in shuffled:
            assert row["output_check"] == sha16(fisher_yates(original, int(row["seed"])))


@pytest.mark.parametrize("count", [0, 1])
def test_missing_files(tmp_path: Path, capsys: pytest.CaptureFixture[str], count: int) -> None:
    """Bỏ qua file thiếu; thiếu hết trả mã lỗi và hướng dẫn đặt file."""
    directory, data = make_data(tmp_path, count)
    out = tmp_path / "results.csv"
    result = run_rq2.main(["--data-dir", str(directory), "--out", str(out)])
    output = capsys.readouterr()
    for name in run_rq2.R1_FILES[count:]:
        assert f"thiếu file {name}" in output.err
    if count:
        assert result == 0
        rows = read_rows(out)
        assert len(rows) == 3
        assert {row["file"] for row in rows} == set(data)
        assert "số dòng kỳ vọng: 3" in output.out
    else:
        assert result != 0
        assert not out.exists()
        assert "Đặt" in output.err and "--data-dir" in output.err


def test_optional_codec_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nạp cả hai tên module tùy chọn, tạo đủ 27 dòng hợp lệ."""
    directory, _ = make_data(tmp_path)
    out = tmp_path / "results.csv"
    install_stub(monkeypatch, "rq2_stub_rle")
    install_stub(monkeypatch, "rq2_stub_lzw")
    assert run_rq2.main([
        "--data-dir", str(directory), "--out", str(out),
        "--codec", "rle=rq2_stub_rle", "lzw=rq2_stub_lzw",
    ]) == 0
    rows = read_rows(out)
    assert len(rows) == 27
    for name in ("huffman", "rle", "lzw"):
        assert sum(row["codec"] == name for row in rows) == 9
    assert all(row["notes"] == "" for row in rows if row["codec"] != "huffman")


@pytest.mark.parametrize("broken_call", [1, 2, 4])
def test_broken_codec_stops_without_bad_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], broken_call: int,
) -> None:
    """Lỗi ở bất kỳ lượt đo, kể cả lượt bộ nhớ, đều dừng trước khi ghi dòng."""
    directory, _ = make_data(tmp_path)
    out = tmp_path / "results.csv"
    calls = 0

    def decode(blob: bytes) -> bytes:
        nonlocal calls
        calls += 1
        return b"wrong" if calls == broken_call else blob[4:]

    install_stub(monkeypatch, "rq2_broken_rle", decode)
    assert run_rq2.main([
        "--data-dir", str(directory), "--out", str(out), "--codec", "rle=rq2_broken_rle",
    ]) != 0
    rows = read_rows(out)
    assert len(rows) == 1  # Huffman/original trước codec lỗi; không chạy tiếp runs/shuffled.
    assert rows[0]["codec"] == "huffman"
    output = capsys.readouterr()
    for detail in ("codec=rle", "file=alice29.txt", "trạng thái=original", "SHA-256"):
        assert detail in output.err
    assert calls == broken_call
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize("overwrite", [False, True])
def test_existing_output(tmp_path: Path, overwrite: bool) -> None:
    """Chỉ thay thế file cũ khi có --overwrite, không nối vào nội dung cũ."""
    directory, _ = make_data(tmp_path)
    out = tmp_path / "results.csv"
    original = b"existing output must survive\n"
    out.write_bytes(original)
    args = ["--data-dir", str(directory), "--out", str(out)]
    result = run_rq2.main(args + (["--overwrite"] if overwrite else []))
    if overwrite:
        assert result == 0
        assert len(read_rows(out)) == 9
    else:
        assert result != 0
        assert out.read_bytes() == original


def test_cannot_overwrite_input(tmp_path: Path) -> None:
    """--overwrite không được xóa dữ liệu R1 nếu --out trỏ vào đầu vào."""
    directory, data = make_data(tmp_path, 1)
    path = directory / "alice29.txt"
    assert run_rq2.main([
        "--data-dir", str(directory), "--out", str(path), "--overwrite",
    ]) != 0
    assert path.read_bytes() == data[path.name]


def test_empty_data(tmp_path: Path) -> None:
    """File rỗng vẫn chạy; tỷ lệ không xác định và throughput để trống."""
    directory, _ = make_data(tmp_path, 1)
    (directory / "alice29.txt").write_bytes(b"")
    out = tmp_path / "results.csv"
    assert run_rq2.main(["--data-dir", str(directory), "--out", str(out)]) == 0
    rows = read_rows(out)
    assert len(rows) == 3
    for row in rows:
        assert row["orig_bytes"] == "0"
        assert row["ratio"] == row["comp_kibs"] == row["decomp_kibs"] == ""
        assert row["h0_bits"] == row["h0_ratio"] == "0"
        assert row["notes"] == "ratio_no_header="


def test_measure_medians_and_separate_memory_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Đúng trung vị; chỉ lượt cuối bật tracing, peak đổi byte sang KiB."""
    tracing = []

    def compress(data: bytes) -> bytes:
        tracing.append(tracemalloc.is_tracing())
        return b"!" + data

    def decompress(blob: bytes) -> bytes:
        tracing.append(tracemalloc.is_tracing())
        return blob[1:]

    ticks = iter([0, .003, 1, 1.030, 2, 2.001, 3, 3.010, 4, 4.002, 5, 5.020])
    monkeypatch.setattr(run_rq2.time, "perf_counter", lambda: next(ticks))
    monkeypatch.setattr(run_rq2.tracemalloc, "get_traced_memory", lambda: (1024, 4096))
    result = run_rq2.measure(run_rq2.Codec("stub", compress, decompress), b"sample", 3)
    assert result.comp_ms == pytest.approx(2)
    assert result.decomp_ms == pytest.approx(20)
    assert result.peak_mem_kib == 4
    assert result.comp_bytes == 7 and result.restored == b"sample"
    assert tracing == [False] * 6 + [True] * 2
    assert not tracemalloc.is_tracing()


def test_memory_exception_stops_tracing() -> None:
    """Dọn tracemalloc ngay cả khi codec ném lỗi trong lượt đo bộ nhớ."""
    def decompress(blob: bytes) -> bytes:
        if tracemalloc.is_tracing():
            raise RuntimeError("memory pass failed")
        return blob

    codec = run_rq2.Codec("stub", bytes, decompress)
    with pytest.raises(RuntimeError, match="memory pass failed"):
        run_rq2.measure(codec, b"test", 1)
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize("repeats", ["0", "-1"])
def test_reject_nonpositive_repeats(repeats: str) -> None:
    """CLI từ chối số lượt đo không hợp lệ trước khi ghi kết quả."""
    with pytest.raises(SystemExit) as error:
        run_rq2.main(["--repeats", repeats])
    assert error.value.code != 0


def test_module_entrypoint(tmp_path: Path) -> None:
    """Chạy tiến trình python -m với module codec thiếu được chỉ định rõ."""
    directory, _ = make_data(tmp_path)
    out = tmp_path / "results.csv"
    result = subprocess.run(
        [sys.executable, "-m", "rq2.run_rq2", "--data-dir", str(directory),
         "--out", str(out), "--codec", "rle=rq2_missing_rle_test", "lzw=rq2_missing_lzw_test"],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True,
        encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
        timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert len(read_rows(out)) == 9
    assert "số dòng kỳ vọng: 9" in result.stdout
