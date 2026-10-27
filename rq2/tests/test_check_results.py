"""Dữ liệu nhỏ chỉ để kiểm thử validator, không phải kết quả thực nghiệm."""
import csv

import pytest

from common.results_schema import COLUMNS, append_row, sha16
from rq2.check_results import CODECS, FILES, check_results


@pytest.fixture
def sample_results(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = tmp_path / "results.csv"
    for file in FILES:
        data = b"AAABBB"
        (data_dir / file).write_bytes(data)
        for codec in CODECS:
            for state, seed in [("original", None), ("runs", None), ("shuffled", 1)]:
                comp = 269 if codec == "huffman" else 16
                append_row(str(csv_path), dict(
                    rq="2", dataset="R1", file=file, codec=codec, state=state, seed=seed,
                    orig_bytes=6, comp_bytes=comp, h0_bits=1.0,
                    comp_ms=1.0, decomp_ms=1.0, peak_mem_kib=1.0,
                    output_check=sha16(data), roundtrip_ok=True,
                ))
    log = tmp_path / "runner.log"
    log.write_text("Số dòng đã ghi: 27; số dòng kỳ vọng: 27\n"
                   "Codec đã chạy: huffman, rle, lzw\n"
                   "Codec bị bỏ qua: không có\nFile bị bỏ qua: không có\n", encoding="utf-8")
    return csv_path, data_dir, [1], log


def test_complete_matrix_passes(sample_results):
    assert all(r["ok"] for r in check_results(*sample_results))


@pytest.mark.parametrize("mutation,failed_item", [
    ("duplicate", 2), ("huffman", 5), ("rle", 7), ("hash", 3), ("h0", 4),
    ("original_hash", 9), ("rle_bound", 7),
])
def test_detects_corruption(sample_results, mutation, failed_item):
    path = sample_results[0]
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if mutation == "duplicate":
        rows[-1] = dict(rows[0])  # Số dòng vẫn đúng, nhưng ma trận sai.
    elif mutation == "huffman":
        next(r for r in rows if r["codec"] == "huffman")["comp_bytes"] = "270"
    elif mutation == "rle":
        next(r for r in rows if r["codec"] == "rle" and r["state"] == "runs")["comp_bytes"] = "18"
    elif mutation == "hash":
        rows[0]["output_check"] = "wrong"
    elif mutation == "original_hash":
        rows[0]["output_check"] = "0" * 16
    elif mutation == "rle_bound":
        next(r for r in rows if r["codec"] == "rle" and r["state"] == "original")["comp_bytes"] = "26"
    else:
        rows[0]["h0_bits"] = "1.1"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    result = check_results(*sample_results)
    assert not result[failed_item - 1]["ok"]


def test_runner_warning_rejected(sample_results):
    log = sample_results[-1]
    with log.open("a", encoding="utf-8") as stream:
        stream.write("Cảnh báo: bỏ qua codec rle\n")
    assert not check_results(*sample_results)[7]["ok"]


@pytest.mark.parametrize('mode,expected', [('complete', 0), ('missing_data', 2), ('missing_csv', 1)])
def test_main_distinguishes_missing_input_from_failure(sample_results, capsys, mode, expected):
    from rq2.check_results import main
    path, data_dir, seeds, log = sample_results
    if mode == 'missing_data':
        (data_dir / FILES[0]).unlink()
    elif mode == 'missing_csv':
        path.unlink()
    result = main(['--csv', str(path), '--data-dir', str(data_dir), '--seeds', '1', '--runner-log', str(log)])
    assert result == expected
    output = capsys.readouterr().out
    if mode == 'missing_data':
        assert 'Missing data file:' in output
        assert "See README 'Data' section." in output
        assert 'KH\u00d4NG \u0110\u1ea0T' not in output
