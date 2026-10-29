"""Synthetic status contracts and lossless migration; no benchmark timings."""
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from common.edge_provenance import projection_metadata, verify_original
from common.results_schema import (COLUMNS, LEGACY_COLUMNS, TIME_COLUMNS,
                                   append_row, finalize_row, validate_row)
from tools.migrate_add_status import AUDIT, FILES, migrate, migrate_bytes, records
from tools.results_schema import CsvWriter, validate


def success():
    return dict(rq="edge", dataset="", state="original", codec="rle",
                file="synthetic.bin", orig_bytes=3, comp_bytes=6,
                comp_ms=1, decomp_ms=2, output_check="0123456789abcdef",
                roundtrip_ok=True, notes="", status="ok")


def failure(status):
    row = success()
    row.update(status=status, notes="synthetic failure", output_check="",
               roundtrip_ok=False if status == "wrong" else "")
    for col in TIME_COLUMNS:
        row[col] = ""
    return row


@pytest.mark.parametrize("status", ["ok", "timeout", "crash", "oom", "wrong"])
def test_status_writers_agree(tmp_path, status):
    row = success() if status == "ok" else failure(status)
    validate_row(row)
    validate(row)
    if status != "ok":
        assert finalize_row(row) == row
    common, pair1 = tmp_path / "common.csv", tmp_path / "pair1.csv"
    append_row(common, row)
    CsvWriter(pair1).write(row)
    for path in (common, pair1):
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == COLUMNS
            parsed = next(reader)
        validate_row(parsed)
        assert parsed["status"] == status
        if status != "ok":
            assert all(parsed[c] == "" for c in TIME_COLUMNS)
    assert CsvWriter(pair1).done_keys() == ({("synthetic.bin", "rle")} if status == "ok" else set())


@pytest.mark.parametrize("status", ["timeout", "crash", "oom", "wrong"])
@pytest.mark.parametrize("column", TIME_COLUMNS)
def test_failed_rows_reject_every_timing(status, column):
    row = failure(status)
    row[column] = 0
    with pytest.raises(ValueError):
        validate_row(row)


@pytest.mark.parametrize("patch", [
    {"status": ""}, {"status": "unknown"}, {"roundtrip_ok": False},
    {"output_check": "g" * 16}, {"comp_ms": ""}, {"decomp_ms": None},
    {"comp_ms": float("nan")}, {"decomp_ms": -1}, {"train_ms": float("inf")},
])
def test_invalid_success(patch):
    with pytest.raises(ValueError):
        validate_row(dict(success(), **patch))


@pytest.mark.parametrize("status", ["timeout", "crash", "oom", "wrong"])
def test_failure_requires_reason_and_matching_roundtrip(status):
    row = failure(status)
    with pytest.raises(ValueError):
        validate_row(dict(row, notes=" "))
    with pytest.raises(ValueError):
        validate_row(dict(row, roundtrip_ok=True))
    if status == "wrong":
        validate_row(dict(row, output_check="a" * 16))
    else:
        with pytest.raises(ValueError):
            validate_row(dict(row, output_check="a" * 16))


def legacy_csv():
    row = success()
    row.update(roundtrip_ok="true", comp_ms="1.000000", decomp_ms="2e0",
               notes='quoted, "text"\nsecond line', ratio="2.000000")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(LEGACY_COLUMNS)
    writer.writerow([row.get(c, "") for c in LEGACY_COLUMNS])
    return stream.getvalue().encode()


def test_cell_preservation_and_byte_idempotence():
    raw = legacy_csv()
    updated, count = migrate_bytes(raw)
    assert count == 1
    assert [row[:-1] for row in records(updated)] == records(raw)
    assert records(updated)[1][-1] == "ok"
    assert migrate_bytes(updated) == (updated, count)


def test_reject_old_header_before_append(tmp_path):
    path = tmp_path / "old.csv"
    raw = legacy_csv()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="Header"):
        append_row(path, success())
    with pytest.raises(ValueError, match="Header"):
        CsvWriter(path)
    assert path.read_bytes() == raw


def test_projection_preserves_hash_and_detects_tamper():
    raw = legacy_csv()
    audit = dict(edge_original_bytes=len(raw), edge_original_sha256=hashlib.sha256(raw).hexdigest(),
                 edge_original_projection=projection_metadata(1))
    updated, _ = migrate_bytes(raw)
    assert verify_original(updated, audit) == raw
    with pytest.raises(ValueError):
        verify_original(updated.replace(b"1.000000", b"9.000000"), audit)
    with pytest.raises(ValueError):
        verify_original(updated, dict(audit, edge_original_projection=projection_metadata(2)))


def test_migration_backups_and_second_run_no_writes(tmp_path):
    root, backup = tmp_path / "repo", tmp_path / "backup"
    raw = legacy_csv()
    for name in FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    audit = root / AUDIT
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(json.dumps(dict(edge_original_bytes=len(raw),
                                    edge_original_sha256=hashlib.sha256(raw).hexdigest())))
    originals = {name: (root / name).read_bytes() for name in (*FILES, AUDIT)}
    migrate(root, backup)
    for name in originals:
        assert (backup / name).read_bytes() == originals[name]
    after = {name: ((root / name).read_bytes(), (root / name).stat().st_mtime_ns)
             for name in originals}
    migrate(root, backup)
    for name in originals:
        assert ((root / name).read_bytes(), (root / name).stat().st_mtime_ns) == after[name]
    with pytest.raises(ValueError, match="outside"):
        migrate(root, root / "backup")


def test_analysis_excludes_failures_without_renumbering():
    from rq1.analyze_rq1 import METRICS, summarize
    good = dict(status="ok", dataset="C1", size_kib=256, codec="rle", seed=1)
    good.update({m: 1 for m in METRICS})
    with pytest.warns(UserWarning, match="excluded"):
        summary = summarize([failure("wrong"), good])
    assert summary[0]["source_csv_lines"] == "3"
    assert summary[0]["n_samples"] == 1
