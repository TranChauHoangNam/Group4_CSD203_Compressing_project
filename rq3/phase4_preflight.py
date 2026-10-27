"""E1-only one-run prefix calibration before the approved RQ3 matrix."""
import json
import re
import time
from pathlib import Path
from rq3 import bpe
from rq3.phase3_feasibility import load_corpus, protected_hashes, sha
from rq3.phase3_analyze import fit, predict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rq3/out/phase4_preflight.json"


def main():
    if OUT.exists():
        raise FileExistsError("Preflight already recorded; do not repeat one-run cells")
    whole = load_corpus("E1", "train")
    report = {"corpus": "E1", "timer": "time.perf_counter", "runs_per_cell": 1,
              "protected_before": protected_hashes(), "cells": []}
    def save():
        OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save()
    for kib in (16, 32, 64, 128):
        data = whole[:kib*1024]
        ub = sum(map(len, set(re.findall(rb" ?[^\s]+|\s+", data))))
        for k in (64, 256):
            expected = None
            for variant in ("naive", "noheap", "inc"):
                previous = [c for c in report["cells"] if c["variant"] == variant]
                estimate = max([10.0] + [c["train_ms"]/1000 * max(len(data)/c["raw_bytes"], ub/c["unique_bytes"]) * max(1,k/max(1,c["m"])) * 2 for c in previous])
                print(f"ESTIMATE E1 {kib} KiB K={k} {variant}: {estimate:.3f}s", flush=True)
                if estimate > 300:
                    report["stopped_before"] = [kib,k,variant,estimate]
                    save()
                    raise SystemExit("STOP: estimate >300s")
                start = time.perf_counter()
                merges = bpe.train(data,k,variant)
                elapsed = (time.perf_counter()-start)*1000
                if expected is None:
                    expected = merges
                if merges != expected:
                    raise ValueError("Merge mismatch: STOP")
                row = dict(corpus="E1",raw_bytes=len(data),unique_bytes=ub,k=k,m=len(merges),variant=variant,train_ms=elapsed,merges_sha256=sha(json.dumps(merges).encode()))
                report["cells"].append(row)
                save()
                print("MEASURED",row,flush=True)
    rows = [c for c in report["cells"] if c["variant"] == "naive"]
    full_unique = sum(map(len,set(re.findall(rb" ?[^\s]+|\s+",whole))))
    estimates=[]
    report["naive_full_k256_models"]={}
    for predictor, size in (("raw_bytes",len(whole)),("unique_bytes",full_unique)):
        coefficients=fit(rows,predictor)
        values=[predict(coefficients,size,256)]
        for n in sorted({r["raw_bytes"] for r in rows}):
            values.append(predict(fit([r for r in rows if r["raw_bytes"]!=n],predictor),size,256))
        report["naive_full_k256_models"][predictor]={"central_s":values[0],"sensitivity_range_s":[min(values),max(values)]}
        estimates+=values
    report["naive_full_k256_range_s"]=[min(estimates),max(estimates)]
    report["safe_to_start_naive_full_k256"] = max(estimates)<=300
    assert report["protected_before"]==protected_hashes()
    save()
    print("E1-BASED ESTIMATE naive full K=256:",report["naive_full_k256_models"],flush=True)
    print("ESTIMATE range:", report["naive_full_k256_range_s"],flush=True)
    if not report["safe_to_start_naive_full_k256"]:
        raise SystemExit("STOP: full naive K=256 upper estimate >300s; not run")


if __name__ == "__main__":
    main()
