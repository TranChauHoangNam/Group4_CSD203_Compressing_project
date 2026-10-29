"""Verify historical edge evidence without replacing its original SHA-256."""
import csv
import hashlib
import io

from common.results_schema import COLUMNS, LEGACY_COLUMNS

METHOD = "legacy-28-columns-utf8-lf-v1"


def legacy_prefix(raw, row_count):
    records = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    if not records or records[0] not in (COLUMNS, LEGACY_COLUMNS):
        raise ValueError("Unexpected edge header")
    if row_count < 0 or len(records) < row_count + 1:
        raise ValueError("Missing original edge rows")
    width = len(records[0])
    if any(len(row) != width for row in records[1:]):
        raise ValueError("Malformed edge row")
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\n").writerows(
        [LEGACY_COLUMNS] + [r[:len(LEGACY_COLUMNS)] for r in records[1:row_count + 1]])
    return out.getvalue().encode("utf-8")


def verify_original(raw, audit):
    projection = audit.get("edge_original_projection")
    if projection is None:
        original = raw[:audit["edge_original_bytes"]]
    else:
        if projection.get("method") != METHOD or projection.get("columns") != LEGACY_COLUMNS:
            raise ValueError("Unsupported edge projection")
        original = legacy_prefix(raw, projection["row_count"])
    if len(original) != audit["edge_original_bytes"] or hashlib.sha256(original).hexdigest() != audit["edge_original_sha256"]:
        raise ValueError("Original edge evidence differs")
    return original


def projection_metadata(row_count):
    return dict(method=METHOD, columns=LEGACY_COLUMNS, row_count=row_count)
