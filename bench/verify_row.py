"""Replay one submitted CSV record without writing results or model caches."""
import argparse
import csv
import gc
import hashlib
import importlib
import json
import math
from pathlib import Path
from statistics import median
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "tools"))

from common.results_schema import COLUMNS, STATUS_VALUES
from gen_synthetic import make, file_name
from rq2.reorder import counting_sort_runs, fisher_yates
from rq3 import bpe
from rq3.run_rq3 import EDGE_CASES, parse_notes
from tools.measure import measure, RoundTripError
from tools.run_edge import CASES

FILTERS = ("rq", "file", "codec", "seed", "dataset", "state", "size_kib",
           "train_variant", "k_merges", "train_corpus", "test_corpus")
CANTERBURY = {
    "alice29.txt": "7467306ee0feed4971260f3c87421154a05be571d944e9cb021a5713700c38f0",
    "kennedy.xls": "9af47239ca29dfe20e633f80bbbb9a4cc9783d0803d7b2b5626f42e4c3790420",
}


class DataError(Exception):
    pass


class ConfigError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_file(path, expected_hash, expected_size=None):
    if not path.is_file():
        raise DataError(f"MISSING_DATA: {path}; restore the exact data described in README/manifest")
    data = path.read_bytes()
    if (expected_size is not None and len(data) != int(expected_size)) or sha(data) != expected_hash:
        raise DataError(f"DATA_MISMATCH: {path}; size/SHA-256 differs; no algorithm executed")
    return data


def load_inputs(row, data_dir, manifest_path):
    """Validate inputs before invoking a codec; no downloads or file generation."""
    notes = parse_notes(row.get("notes", ""))
    rq, codec, name = row["rq"], row["codec"], row["file"]
    if Path(name).name != name or any(c in name for c in ("/", "\\", ":")):
        raise ValueError("file must be a basename")
    if codec not in {"rle", "huffman", "lzw", "bpe"}:
        raise ValueError("Unsupported codec")
    manifest = None

    def source(filename):
        nonlocal manifest
        if manifest is None:
            if not manifest_path.is_file():
                raise DataError(f"MISSING_DATA: {manifest_path}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        entry = manifest.get(filename)
        if not entry:
            raise DataError(f"MISSING_DATA: manifest entry for {filename}")
        return entry

    def wiki(filename):
        entry = source(filename)
        return checked_file(data_dir / "wiki" / filename, entry["sha256"], entry["bytes"])

    train = None
    if rq == "edge":
        cases = EDGE_CASES if codec == "bpe" else CASES
        if name not in cases:
            raise ValueError("Unknown edge case")
        data = cases[name]
        if codec == "bpe":
            train = data
    elif rq == "1":
        if codec == "bpe" or row["state"] != "original":
            raise ValueError("Unsupported RQ1 configuration")
        family, size = row["dataset"], int(row["size_kib"]) * 1024
        if family in {"C1", "C2", "C3"}:
            seed = int(row["seed"])
            if name != file_name(family, size, seed) or size <= 0:
                raise ValueError("Synthetic file/dataset/size/seed disagree")
            data = make(family, size, seed)
        elif family == "V1" and name == f"v1_{row['size_kib']}kib.txt":
            data = wiki(name)
        else:
            raise ValueError("Unsupported RQ1 dataset/file")
    elif rq == "2":
        if codec == "bpe" or row["dataset"] != "R1":
            raise ValueError("Unsupported RQ2 configuration")
        # A supplied manifest may describe a separate, explicitly selected corpus.
        entry = source(name) if name not in CANTERBURY else None
        data = checked_file(data_dir / name, entry["sha256"] if entry else CANTERBURY[name],
                            entry["bytes"] if entry else row["orig_bytes"])
        if row["state"] == "runs":
            data = counting_sort_runs(data)
        elif row["state"] == "shuffled":
            data = fisher_yates(data, int(row["seed"]))
        elif row["state"] != "original":
            raise ValueError("Unsupported RQ2 state")
    elif rq == "3":
        if codec not in {"bpe", "lzw"} or row["test_corpus"] not in {"V1", "E1"}:
            raise ValueError("Unsupported RQ3 configuration")
        if name != f"{row['test_corpus'].lower()}_test_1mib.txt" or row["dataset"] != row["test_corpus"]:
            raise ValueError("RQ3 dataset/file/test_corpus disagree")
        data = wiki(name)
        if codec == "bpe":
            if row["train_corpus"] not in {"V1", "E1"} or int(notes.get("train_prefix_kib", "-1")) != 0:
                raise ValueError("RQ3 verification requires explicit full-corpus training (train_prefix_kib=0)")
            train = wiki(f"{row['train_corpus'].lower()}_train_1mib.txt")
            if len(train) != int(notes["train_bytes"]) or sha(train) != notes["train_sha256"]:
                raise DataError("DATA_MISMATCH: full train input differs from CSV notes")
    else:
        raise ValueError("Unsupported rq")
    if len(data) != int(row["orig_bytes"]) or sha(data)[:16] != row["output_check"]:
        raise DataError("DATA_MISMATCH: reconstructed input differs from submitted orig_bytes/output_check")
    return data, train, notes


def replay(request):
    row = request["row"]
    try:
        data, train, notes = load_inputs(row, Path(request["data_dir"]), Path(request["manifest"]))
        if row["codec"] == "bpe" and (row["train_variant"] not in {"inc", "noheap", "naive"}
                                      or not 0 <= int(row["k_merges"]) <= bpe.MAX_MERGES):
            raise ValueError("Invalid BPE variant/K")
        runs = int(notes.get("train_runs", "1"))
        repeats = int(notes.get("timing_runs", "1" if row["rq"] == "edge" and row["codec"] != "bpe" else "3"))
        if min(runs, repeats) < 1:
            raise ValueError("Repetition counts must be positive")
    except (ValueError, KeyError, TypeError) as exc:
        raise ConfigError(str(exc)) from exc
    gc.enable()  # Default GC in a fresh interpreter; no tracing or warm-up pass.
    train_ms = None
    if row["codec"] == "bpe":
        samples, previous = [], None
        for _ in range(runs):
            start = time.perf_counter_ns()
            merges = bpe.train(train, int(row["k_merges"]), row["train_variant"])
            samples.append((time.perf_counter_ns() - start) / 1e6)
            if previous is not None and merges != previous:
                raise RoundTripError("Training merge lists differ across repeats")
            previous = merges
        train_ms = median(samples)
        codec = SimpleNamespace(compress=lambda value: bpe.compress_with_merges(value, merges),
                                decompress=bpe.decompress)
    else:
        codec = importlib.import_module(row["codec"])
    measured = measure(codec, data, repeats=repeats, with_mem=False, timer_ns=True)
    return dict(status="ok", comp_bytes=measured["comp_bytes"], output_check=measured["output_check"],
                comp_ms=measured["comp_ms"], decomp_ms=measured["decomp_ms"], train_ms=train_ms)


def worker():
    try:
        result = replay(json.load(sys.stdin))
    except DataError as exc:
        result = dict(error=str(exc), exit_code=2)
    except MemoryError:
        result = dict(status="oom", error="MemoryError")
    except RoundTripError as exc:
        result = dict(status="wrong", error=str(exc))
    except ConfigError as exc:
        result = dict(error=f"INVALID_CONFIG: {exc}", exit_code=2)
    except Exception as exc:
        result = dict(status="crash", error=f"{type(exc).__name__}: {exc}")
    print(json.dumps(result))
    return 0


def select_row(args):
    with args.csv.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError("CSV must use the current schema with explicit status")
        rows = list(reader)
    filters = {k: getattr(args, k) for k in FILTERS if getattr(args, k) is not None}
    if args.row is not None and filters:
        raise ValueError("Use --row or filters, not both")
    matches = [(line, row) for line, row in enumerate(rows, 2)
               if (args.row is None or line == args.row) and all(row[k] == v for k, v in filters.items())]
    if len(matches) != 1:
        print(f"SELECTION_ERROR: {len(matches)} matching rows; select exactly one")
        for line, row in matches:
            print(f"  --row {line}: " + " ".join(f"{k}={row[k]}" for k in FILTERS if row[k]))
        return None
    line, row = matches[0]
    if row["status"] not in STATUS_VALUES:
        raise ValueError("Invalid submitted status")
    return line, row


def compare(row, actual):
    print("metric | submitted | rerun | rerun/submitted | PASS/FAIL")
    passed = True
    for key in ("status", "comp_bytes", "output_check"):
        ok = str(actual.get(key, "")) == row[key]
        print(f"{key} | {row[key]} | {actual.get(key, '')} | - | {'PASS' if ok else 'FAIL'}")
        passed &= ok
    for key in ("comp_ms", "decomp_ms", "train_ms"):
        if not row.get(key):
            continue
        expected, value = float(row[key]), actual.get(key)
        ratio = value / expected if isinstance(value, (int, float)) and expected > 0 else None
        ok = ratio is not None and math.isfinite(ratio) and .5 <= ratio <= 2
        advisory = row["rq"] == "edge"
        outcome = "INFO (edge timing only)" if advisory else "PASS" if ok else "FAIL"
        print(f"{key} | {expected:.9g} | {value if value is not None else ''} | {format(ratio, '.4f') if ratio is not None else '-'} | {outcome}")
        if not advisory:
            passed &= ok
    if row["rq"] == "edge":
        print("Edge timings are advisory: tiny durations are dominated by timer/OS noise; no 0.5x-2.0x failure.")
    return 0 if passed else 1


def positive_timeout(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and positive")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--row", type=int, help="CSV record number including header=1")
    for field in FILTERS:
        parser.add_argument("--" + field.replace("_", "-"), dest=field)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / "docs/manifest.json")
    parser.add_argument("--timeout", type=positive_timeout, default=60)
    args = parser.parse_args(argv)
    try:
        selected = select_row(args)
        if selected is None:
            return 2
        line, row = selected
        request = dict(row=row, data_dir=str(args.data_dir.resolve()), manifest=str(args.manifest.resolve()))
        print(f"VERIFY {args.csv}:{line}; timeout={args.timeout:g}s; memory pass disabled", flush=True)
        started = time.perf_counter_ns()
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                                     input=json.dumps(request), capture_output=True, text=True,
                                     encoding="utf-8", timeout=args.timeout)
            if process.returncode:
                actual = dict(status="crash", error=f"worker exit={process.returncode}: {process.stderr.strip()}")
            else:
                actual = json.loads(process.stdout)
        except subprocess.TimeoutExpired:
            actual = dict(status="timeout", error=f"Exceeded {args.timeout:g}s subprocess limit")
        print(f"wall_seconds={(time.perf_counter_ns()-started)/1e9:.3f}")
        if "status" in actual:
            print(f"status={actual['status']}")
        if actual.get("error"):
            print(actual["error"])
        if actual.get("exit_code") == 2:
            return 2
        if actual.get("status") == "timeout" and row["rq"] == "3" and row["train_variant"] == "naive":
            if args.timeout == 60:
                print("Vượt giới hạn 60 s của quy định, số đã nộp đo bằng thí nghiệm riêng final_submission/naive_full_experiment.json.")
            print("Use --timeout SECONDS to confirm a longer run; the submitted CSV is never changed.")
        return compare(row, actual)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"INPUT_ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(worker() if sys.argv[1:] == ["--worker"] else main())
