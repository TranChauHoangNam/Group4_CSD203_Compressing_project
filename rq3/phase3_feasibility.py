"""One-run feasibility measurements only; never writes Phase 4 result CSVs."""
import argparse
import hashlib
import json
import platform
import re
import sys
import time
from pathlib import Path

from rq3 import bpe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rq3/out/phase3_measurements.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def protected_hashes():
    paths = [ROOT / n for n in ("rle.py", "lzw.py", "container.py", "results_rq2_all.csv", "common/results_schema.py", "rq3/bpe.py")]
    paths += list((ROOT / "tools").glob("*.py")) + list((ROOT / "rq2").rglob("*"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths
            if p.is_file() and "__pycache__" not in p.parts}


def save(report):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_corpus(corpus, part):
    name = f"{corpus.lower()}_{part}_1mib.txt"
    data = (ROOT / "data/wiki" / name).read_bytes()
    manifest = json.loads((ROOT / "docs/manifest.json").read_text(encoding="utf-8"))["files"][name]
    if len(data) != manifest["bytes"] or sha(data) != manifest["sha256"]:
        raise ValueError(f"Manifest mismatch: {name}")
    return data


def initialize():
    if OUT.exists():
        raise FileExistsError("Measurement report exists; do not repeat one-run cells")
    report = {"python": sys.version, "platform": platform.platform(),
              "timer": "time.perf_counter", "repeats_per_cell": 1,
              "protected_before": protected_hashes(), "segments": [], "cells": []}
    for corpus in ("V1", "E1"):
        whole = load_corpus(corpus, "train")
        for kib in (16, 32, 64, 128, 1024):
            data = whole[:kib * 1024]
            segments = re.findall(rb" ?[^\s]+|\s+", data)
            unique = set(segments)
            row = {"corpus": corpus, "size_kib_label": kib, "raw_bytes": len(data),
                   "segments": len(segments), "unique_segments": len(unique),
                   "unique_bytes": sum(map(len, unique)), "sha256": sha(data)}
            report["segments"].append(row)
            print("SEGMENTS", row, flush=True)
    save(report)


def guard(report, estimate_s, label):
    print(f"PRE-RUN ESTIMATE {label}: {estimate_s:.3f} s (planning bound, not measured)", flush=True)
    if estimate_s > 300:
        report["stopped_before_cell"] = {"label": label, "estimate_s": estimate_s}
        save(report)
        raise SystemExit("STOP: single-cell estimate exceeds 5 minutes; cell NOT run")


def timed_train(report, data, stat, k, variant, estimate_s, scope):
    label = f"{scope} {variant} V1 {len(data)} bytes K={k}"
    guard(report, estimate_s, label)
    start = time.perf_counter()
    merges = bpe.train(data, k, variant)
    elapsed = time.perf_counter() - start
    row = {"scope": scope, "corpus": "V1", "variant": variant, "k": k,
           "m": len(merges), "raw_bytes": len(data), "unique_bytes": stat["unique_bytes"],
           "train_ms": elapsed * 1000, "pre_run_estimate_s": estimate_s,
           "merges_sha256": sha(json.dumps(merges).encode("ascii"))}
    peers = [c for c in report["cells"] if c["raw_bytes"] == len(data) and c["k"] == k]
    if any(c["merges_sha256"] != row["merges_sha256"] for c in peers):
        raise ValueError("Merge mismatch across variants; STOP")
    report["cells"].append(row)
    save(report)
    print("MEASURED", row, flush=True)
    return row, merges


def prefixes(report):
    whole = load_corpus("V1", "train")
    for kib in (16, 32, 64, 128):
        stat = next(s for s in report["segments"] if s["corpus"] == "V1" and s["size_kib_label"] == kib)
        data = whole[:kib * 1024]
        for k in (64, 256):
            for variant in ("naive", "noheap", "inc"):
                if any(c["scope"] == "prefix" and c["raw_bytes"] == len(data) and c["k"] == k and c["variant"] == variant for c in report["cells"]):
                    continue
                previous = [c for c in report["cells"] if c["variant"] == variant]
                # Conservative planning: max raw/unique and K scaling, factor two.
                estimates = [c["train_ms"] / 1000 * max(len(data) / c["raw_bytes"], stat["unique_bytes"] / c["unique_bytes"])
                             * max(1, k / max(c["m"], 1)) * 2 for c in previous]
                bound = max(estimates) if estimates else 10.0
                timed_train(report, data, stat, k, variant, bound, "prefix")


def full_inc(report):
    whole = load_corpus("V1", "train")
    test = load_corpus("V1", "test")
    stat = next(s for s in report["segments"] if s["corpus"] == "V1" and s["size_kib_label"] == 1024)
    for k in (256, 1024, 3840):
        existing = [c for c in report["cells"] if c["scope"] == "full" and c["k"] == k]
        if existing:
            if "decode_ms" not in existing[0]:
                raise RuntimeError("Incomplete full cell; do not silently repeat training")
            continue
        previous = [c for c in report["cells"] if c["variant"] == "inc"]
        if not previous:
            raise RuntimeError("Run prefixes before full cells")
        bound = max(c["train_ms"] / 1000 * max(len(whole) / c["raw_bytes"], stat["unique_bytes"] / c["unique_bytes"])
                    * max(1, k / max(c["m"], 1)) * 2 for c in previous)
        row, merges = timed_train(report, whole, stat, k, "inc", bound, "full")
        # Prior Phase 2 tests round-tripped 64 KiB in seconds; initial test bound
        # is 60 seconds, subsequent bounds scale the measured test time by two.
        prior = [c for c in report["cells"] if "encode_ms" in c]
        test_bound = max([60.0] + [(c["encode_ms"] + c["decode_ms"]) / 1000 * 2 for c in prior])
        guard(report, test_bound, f"encode/decode V1 test K={k}")
        start = time.perf_counter()
        tokens = bpe.encode(test, merges)
        row["encode_ms"] = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        restored = bpe.decode(tokens, merges)
        row["decode_ms"] = (time.perf_counter() - start) * 1000
        row.update(test_bytes=len(test), n_tokens=len(tokens), output_sha256=sha(restored))
        if sha(restored) != sha(test):
            raise ValueError("Roundtrip SHA-256 mismatch; STOP")
        save(report)
        print("MEASURED FULL", row, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("stats", "prefix", "full", "verify"))
    args = parser.parse_args()
    if args.stage == "stats":
        initialize()
        return
    report = json.loads(OUT.read_text(encoding="utf-8"))
    if report["protected_before"] != protected_hashes():
        raise RuntimeError("Protected file hash changed")
    if args.stage == "prefix":
        prefixes(report)
    elif args.stage == "full":
        full_inc(report)
    else:
        assert len(report["segments"]) == 10
        assert len([c for c in report["cells"] if c["scope"] == "prefix"]) == 24
        assert len([c for c in report["cells"] if c["scope"] == "full"]) == 3
        assert all(c["m"] <= c["k"] and c["train_ms"] > 0 for c in report["cells"])
        assert all("decode_ms" in c for c in report["cells"] if c["scope"] == "full")
        print("PASS: 10 segment rows, 24 prefix cells, 3 full cells, protected hashes unchanged")


if __name__ == "__main__":
    main()
