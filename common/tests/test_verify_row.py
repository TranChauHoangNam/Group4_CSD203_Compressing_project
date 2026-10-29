"""Small replay fixtures; integration timings are observations, not assertions."""
import csv
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import gen_synthetic
import rle
from rq3 import bpe
from tools import verify_row as verify
from tools import measure as measurement
from common.results_schema import COLUMNS


def row_for(data, **fields):
    row = {c: "" for c in COLUMNS}
    row.update(rq="1", dataset="C1", state="original", codec="rle", size_kib="1",
               seed="1", file="C1_1024_s1.bin", status="ok", roundtrip_ok="true",
               orig_bytes=str(len(data)), comp_bytes=str(len(rle.compress(data))),
               output_check=verify.sha(data)[:16], comp_ms="1", decomp_ms="1")
    row.update(fields)
    return row


def csv_file(tmp_path, rows):
    path = tmp_path / "synthetic_results.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def run(path, *extra):
    return subprocess.run([sys.executable, str(verify.ROOT / "tools/verify_row.py"), str(path), *extra],
                          capture_output=True, text=True, encoding="utf-8", timeout=10)


def assert_replayed(result):
    # A tiny fixture may fall outside a timing band due to process/timer noise.
    assert result.returncode in (0, 1), result.stdout + result.stderr
    assert "status | ok | ok | - | PASS" in result.stdout
    assert "output_check" in result.stdout
    assert "comp_bytes" in result.stdout
    assert "wall_seconds=" in result.stdout


def corpus(tmp_path, files):
    directory = tmp_path / "data"
    directory.mkdir(exist_ok=True)
    manifest = {}
    for name, data in files.items():
        path = directory / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(data)
        manifest[Path(name).name] = dict(bytes=len(data), sha256=verify.sha(data))
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(dict(files=manifest)), encoding="utf-8")
    return directory, path


def test_rq1_small_no_input_file(tmp_path):
    data = gen_synthetic.make("C1", 1024, 1)
    path = csv_file(tmp_path, [row_for(data)])
    assert_replayed(run(path, "--row", "2", "--data-dir", str(tmp_path / "absent")))


def test_rq2_shuffled(tmp_path):
    data = b"AAAAABBBCC DDEE" * 20
    directory, manifest = corpus(tmp_path, {"v1_test_1mib.txt": data})
    reordered = verify.fisher_yates(data, 3)
    row = row_for(reordered, rq="2", dataset="R1", file="v1_test_1mib.txt",
                  state="shuffled", seed="3", size_kib="")
    path = csv_file(tmp_path, [row])
    assert_replayed(run(path, "--rq", "2", "--state", "shuffled", "--seed", "3",
                        "--data-dir", str(directory), "--manifest", str(manifest)))


def test_rq3_full_small_k(tmp_path):
    train, data = b"aaabdaaabac " * 8, b"aaabdaaabac"
    directory, manifest = corpus(tmp_path, {"wiki/v1_train_1mib.txt": train,
                                            "wiki/v1_test_1mib.txt": data})
    row = row_for(data, rq="3", dataset="V1", codec="bpe", file="v1_test_1mib.txt",
                  train_variant="inc", k_merges="3", train_corpus="V1", test_corpus="V1",
                  size_kib="", seed="", train_ms="1",
                  comp_bytes=str(len(bpe.compress_with_merges(data, bpe.train(train, 3, "inc")))),
                  notes=f"train_prefix_kib=0;train_bytes={len(train)};train_sha256={verify.sha(train)};train_runs=3;timing_runs=3")
    path = csv_file(tmp_path, [row])
    result = run(path, "--row", "2", "--data-dir", str(directory), "--manifest", str(manifest))
    assert_replayed(result)
    assert "train_ms |" in result.stdout


def test_missing_and_bad_data(tmp_path):
    data = b"ABC" * 4
    directory, manifest = corpus(tmp_path, {"wiki/v1_1kib.txt": data})
    path = csv_file(tmp_path, [row_for(data, dataset="V1", file="v1_1kib.txt", seed="")])
    source = directory / "wiki/v1_1kib.txt"
    source.write_bytes(b"wrong")
    result = run(path, "--row", "2", "--data-dir", str(directory), "--manifest", str(manifest))
    assert result.returncode == 2 and "DATA_MISMATCH" in result.stdout
    source.unlink()
    result = run(path, "--row", "2", "--data-dir", str(directory), "--manifest", str(manifest))
    assert result.returncode == 2 and "MISSING_DATA" in result.stdout


def test_ambiguous_and_header_row(tmp_path):
    data = gen_synthetic.make("C1", 1024, 1)
    path = csv_file(tmp_path, [row_for(data), row_for(data)])
    result = run(path, "--codec", "rle")
    assert result.returncode == 2
    assert "--row 2:" in result.stdout and "--row 3:" in result.stdout
    assert "VERIFY " not in result.stdout
    result = run(path, "--row", "1")
    assert result.returncode == 2


def test_timeout_is_reported_not_raised(tmp_path, monkeypatch, capsys):
    path = csv_file(tmp_path, [row_for(b"A", rq="3", train_variant="naive")])
    def timeout(command, **kwargs):
        assert command[0] == sys.executable
        assert kwargs["timeout"] == 60
        raise subprocess.TimeoutExpired(command, 60)
    monkeypatch.setattr(verify.subprocess, "run", timeout)
    assert verify.main([str(path), "--row", "2"]) == 1
    output = capsys.readouterr().out
    assert "status | ok | timeout" in output
    assert "final_submission/naive_full_experiment.json" in output


def test_explicit_timeout_and_actual_edge_case(tmp_path):
    path = csv_file(tmp_path, [row_for(b"", rq="edge", dataset="", file="edge_empty.bin",
                                      seed="", size_kib="")])
    result = run(path, "--row", "2")
    assert result.returncode == 0 and "INFO (edge timing only)" in result.stdout
    result = run(path, "--row", "2", "--timeout", "0.000001")
    assert result.returncode == 1 and "status=timeout" in result.stdout


def test_reject_prefix_instead_of_full_train(tmp_path):
    data = b"aaabdaaabac"
    directory, manifest = corpus(tmp_path, {"wiki/v1_test_1mib.txt": data})
    row = row_for(data, rq="3", dataset="V1", codec="bpe", file="v1_test_1mib.txt",
                  train_variant="inc", k_merges="3", train_corpus="V1", test_corpus="V1",
                  notes="train_prefix_kib=128")
    path = csv_file(tmp_path, [row])
    result = run(path, "--row", "2", "--data-dir", str(directory), "--manifest", str(manifest))
    assert result.returncode == 2 and "full-corpus" in result.stdout


@pytest.mark.parametrize("factor,expected", [(.49, 1), (.5, 0), (2, 0), (2.01, 1)])
def test_all_three_timing_bands(factor, expected):
    row = row_for(b"A", rq="3", train_ms="1")
    actual = dict(status="ok", comp_bytes=int(row["comp_bytes"]), output_check=row["output_check"],
                  comp_ms=1, decomp_ms=1, train_ms=1)
    for field in ("comp_ms", "decomp_ms", "train_ms"):
        assert verify.compare(row, dict(actual, **{field: factor})) == expected


def test_edge_timing_is_advisory_but_hash_is_required(capsys):
    row = row_for(b"A", rq="edge")
    actual = dict(status="ok", comp_bytes=int(row["comp_bytes"]), output_check=row["output_check"],
                  comp_ms=1000, decomp_ms=.00001)
    assert verify.compare(row, actual) == 0
    assert "advisory" in capsys.readouterr().out
    assert verify.compare(row, dict(actual, output_check="0" * 16)) == 1


def test_shared_ns_timer_and_no_memory(monkeypatch):
    ticks = iter([0, 1_000_000, 3_000_000] * 3)
    monkeypatch.setattr(measurement.time, "perf_counter_ns", lambda: next(ticks))
    def forbidden():
        raise AssertionError("Legacy clock/memory pass must not run")
    monkeypatch.setattr(measurement.time, "perf_counter", forbidden)
    monkeypatch.setattr(measurement.tracemalloc, "start", forbidden)
    codec = SimpleNamespace(compress=lambda data: data, decompress=lambda data: data)
    result = measurement.measure(codec, b"A", timer_ns=True, with_mem=False)
    assert result["comp_ms"] == 1 and result["decomp_ms"] == 2
    assert result["peak_mem_kib"] is None
