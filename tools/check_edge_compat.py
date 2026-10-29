"""Kiểm tra CSV edge bằng schema chung, không chuyển đổi giá trị CSV."""
import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.results_schema import COLUMNS, validate_row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("results/results_edge.csv"))
    args = parser.parse_args()
    total = rejected = 0
    with args.csv.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError("Unexpected edge CSV header")
        for line, row in enumerate(reader, start=2):
            total += 1
            try:
                if row.get("rq") != "edge" or row.get("dataset") != "":
                    raise ValueError("Yêu cầu rq=edge và dataset trống")
                validate_row(row)
            except (ValueError, TypeError) as exc:
                rejected += 1
                print(f"REJECT dòng {line} ({row.get('file')}, {row.get('codec')}): {exc}")
    print(f"{total} dòng; {total - rejected} đạt; {rejected} bị từ chối")
    return int(rejected != 0)


if __name__ == "__main__":
    raise SystemExit(main())
