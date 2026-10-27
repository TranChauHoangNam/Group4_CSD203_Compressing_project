"""Isolated full-corpus naive BPE checks; never edits the primary RQ3 CSV."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from rq3 import bpe
from rq3.phase3_feasibility import load_corpus

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).with_name("naive_full_experiment.json")
AUDIT = ROOT / "rq3/out/rq3_run_audit.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", choices=("V1", "E1"))
    parser.add_argument("k", type=int, choices=(1024, 3840))
    args = parser.parse_args()
    if OUT.exists():
        audit = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        audit = {"timer": "time.perf_counter", "runs_per_cell": 1, "cells": []}
    ident = f"{args.corpus}|{args.k}"
    if any(row["id"] == ident for row in audit["cells"]):
        raise SystemExit(f"Already measured: {ident}")
    data = load_corpus(args.corpus, "train")
    print(f"START {ident} bytes={len(data)} sha256={sha(data)}", flush=True)
    start = time.perf_counter()
    merges = bpe.train(data, args.k, "naive")
    elapsed_ms = (time.perf_counter() - start) * 1000
    existing = json.loads(AUDIT.read_text(encoding="utf-8"))
    expected = [tuple(pair) for pair in
                existing["models"][f"{args.corpus}|{args.k}|inc"]["merges"]]
    merge_sha = sha(json.dumps(merges).encode())
    expected_sha = sha(json.dumps(expected).encode())
    first_mismatch = next((i for i, pair in enumerate(zip(merges, expected))
                           if pair[0] != pair[1]), None)
    if first_mismatch is None and len(merges) != len(expected):
        first_mismatch = min(len(merges), len(expected))
    row = {"id": ident, "corpus": args.corpus, "variant": "naive", "k": args.k,
           "raw_bytes": len(data), "train_runs": 1, "train_ms": elapsed_ms,
           "m_actual": len(merges), "input_sha256": sha(data),
           "merges_sha256": merge_sha, "matches_full_inc": merges == expected,
           "first_mismatch_index": first_mismatch,
           "naive_pair_at_mismatch": merges[first_mismatch] if first_mismatch is not None and first_mismatch < len(merges) else None,
           "inc_pair_at_mismatch": expected[first_mismatch] if first_mismatch is not None and first_mismatch < len(expected) else None}
    audit["cells"].append(row)
    OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print("MEASURED", json.dumps(row), flush=True)
    if first_mismatch is not None:
        print("MERGE MISMATCH", first_mismatch, "naive", row["naive_pair_at_mismatch"],
              "inc", row["inc_pair_at_mismatch"], flush=True)


if __name__ == "__main__":
    main()
