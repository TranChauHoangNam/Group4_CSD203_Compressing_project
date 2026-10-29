"""Add status=ok to the four active CSVs, preserving every existing cell string.

Run from the repository root: python -m tools.migrate_add_status --backup-dir PATH
PATH must be outside the repository. Archives and derived CSVs are not migrated.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from common.edge_provenance import projection_metadata, verify_original
from common.results_schema import COLUMNS, LEGACY_COLUMNS, validate_row

ROOT = Path(__file__).resolve().parents[1]
FILES = ("results/results_rq1.csv", "results_rq2_all.csv",
         "results/results_rq3.csv", "results/results_edge.csv")
AUDIT = "rq3/out/rq3_run_audit.json"


def records(raw):
    return list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))


def migrate_bytes(raw):
    before = records(raw)
    if not before or before[0] not in (LEGACY_COLUMNS, COLUMNS):
        raise ValueError("Unsupported CSV header; expected 28 or 29 columns")
    width = len(before[0])
    if any(len(r) != width for r in before[1:]):
        raise ValueError("CSV row width differs from header")
    if before[0] == COLUMNS:
        for row in before[1:]:
            validate_row(dict(zip(COLUMNS, row)))
        return raw, len(before) - 1  # Idempotence includes the exact bytes.
    after = [COLUMNS] + [row + ["ok"] for row in before[1:]]
    for row in after[1:]:
        validate_row(dict(zip(COLUMNS, row)))
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(after)
    result = stream.getvalue().encode("utf-8")
    if [r[:-1] for r in records(result)] != before:
        raise ValueError("Migration changed an existing cell")
    return result, len(before) - 1


def migrate(root, backup_dir):
    root, backup_dir = Path(root).resolve(), Path(backup_dir).resolve()
    if backup_dir == root or root in backup_dir.parents:
        raise ValueError("Backup must be outside the repository")
    originals = {name: (root / name).read_bytes() for name in (*FILES, AUDIT)}
    updates, counts = {}, {}
    for name in FILES:
        updates[name], counts[name] = migrate_bytes(originals[name])
    audit = json.loads(originals[AUDIT])
    original_edge = verify_original(originals[FILES[-1]], audit)
    if "edge_original_projection" not in audit:
        audit["edge_original_projection"] = projection_metadata(len(records(original_edge)) - 1)
        updates[AUDIT] = (json.dumps(audit, indent=2) + "\n").encode("utf-8")
    else:
        updates[AUDIT] = originals[AUDIT]
    verify_original(updates[FILES[-1]], audit)
    changed = [name for name in updates if updates[name] != originals[name]]
    # Preflight all destinations before touching any source.
    for name in changed:
        dest = backup_dir / name
        if dest.exists() and dest.read_bytes() != originals[name]:
            raise ValueError(f"Backup already exists with different bytes: {dest}")
    for name in changed:
        dest = backup_dir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(originals[name])
    for name in changed:
        path = root / name
        if path.read_bytes() != originals[name]:
            raise ValueError(f"Source changed during migration: {path}")
        path.write_bytes(updates[name])
    for name in FILES:
        current = (root / name).read_bytes()
        if current != updates[name]:
            raise ValueError(f"Read-back mismatch: {name}")
        print(f"{name}: {counts[name]} -> {counts[name]} rows; existing cells unchanged; "
              f"sha256={hashlib.sha256(current).hexdigest()}")
    print(f"Changed files: {len(changed)}; archive and derived CSVs untouched")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", required=True, type=Path)
    args = parser.parse_args()
    migrate(ROOT, args.backup_dir)


if __name__ == "__main__":
    main()
