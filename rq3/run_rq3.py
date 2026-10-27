"""Full-corpus RQ3 matrix. Timings and traced memory are separate passes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import median
import struct
import time
import tracemalloc

import lzw
from common.results_schema import COLUMNS, append_row, sha16
from rq3 import bpe
from rq3.phase3_feasibility import load_corpus, protected_hashes
from rq3.phase3_analyze import fit, predict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rq3/out"
RESULTS = ROOT / "results/results_rq3.csv"
AUDIT = OUT / "rq3_run_audit.json"
CORPORA = ("V1", "E1")
VARIANTS = ("inc", "noheap", "naive")
KS = (256, 1024, 3840)
EDGE_CASES = {"edge_empty.bin": b"", "edge_1byte.bin": b"A",
              "edge_64kib_same.bin": b"A"*65536, "edge_256_values.bin": bytes(range(256)),
              "edge_ABABABA.bin": b"ABABABA", "edge_aaabdaaabac.bin": b"aaabdaaabac"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def notes_text(values):
    return ";".join(f"{k}={v}" for k,v in values.items())


def parse_notes(text):
    return dict(item.split("=",1) for item in text.split(";") if "=" in item)


def key(row):
    return "|".join(str(row.get(k,"")) for k in ("codec","train_variant","k_merges","train_corpus","test_corpus","file"))


def read_rows(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Unexpected CSV header: {path}")
        return list(reader)


def guard(label, seconds):
    print(f"ESTIMATE before {label}: {seconds:.2f}s",flush=True)
    if seconds>300:
        raise SystemExit(f"STOP before {label}: estimate {seconds:.2f}s >300s")


def save(audit):
    OUT.mkdir(parents=True,exist_ok=True)
    temporary=AUDIT.with_suffix(".tmp")
    temporary.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    temporary.replace(AUDIT)


def assert_roundtrip(data, restored):
    if not isinstance(restored,bytes) or digest(restored)!=digest(data):
        raise ValueError("SHA-256 round-trip mismatch: STOP; no CSV row written")


def measure(compress, decompress, data, repeats=3):
    if tracemalloc.is_tracing():
        raise RuntimeError("Tracing must be off during timing")
    cm,dm=[],[]
    expected_blob=None
    for _ in range(repeats):
        start=time.perf_counter(); blob=compress(data); cm.append((time.perf_counter()-start)*1000)
        start=time.perf_counter(); restored=decompress(blob); dm.append((time.perf_counter()-start)*1000)
        assert_roundtrip(data,restored)
        if expected_blob is None:
            expected_blob=blob
        elif blob!=expected_blob:
            raise ValueError("Non-deterministic compressed output")
        del blob,restored
    guard("separate compress+decompress tracemalloc pass",max(10,(median(cm)+median(dm))/1000*40))
    tracemalloc.start()
    try:
        blob=compress(data)
        restored=decompress(blob)
        peak=tracemalloc.get_traced_memory()[1]/1024
    finally:
        tracemalloc.stop()
    assert_roundtrip(data,restored)
    if blob!=expected_blob:
        raise ValueError("Traced compressed output differs")
    return dict(orig_bytes=len(data),comp_bytes=len(blob),comp_ms=median(cm),decomp_ms=median(dm),
                peak_mem_kib=peak,output_check=sha16(restored),roundtrip_ok=True), blob, dict(comp_ms_runs=cm,decomp_ms_runs=dm)


def train_estimate(corpus,variant,k,prefix):
    source=OUT/("phase4_preflight.json" if corpus=="E1" else "phase3_measurements.json")
    rows=[r for r in json.loads(source.read_text())["cells"] if r["variant"]==variant and r["raw_bytes"]<=131072]
    last=next(r for r in rows if r["raw_bytes"]==131072 and r["k"]==256)
    if variant=="naive":
        supplement=ROOT/'final_submission/naive_full_experiment.json'
        if not prefix and supplement.exists():
            cells=json.loads(supplement.read_text())["cells"]
            match=next((c for c in cells if c['corpus']==corpus and c['k']==k),None)
            if match is not None:
                return match['train_ms']/1000*1.25
        if prefix:
            return last["train_ms"]/1000*(k/256)*2
        if corpus=="E1":
            return json.loads(source.read_text())["naive_full_k256_range_s"][1]
        return 2*last["train_ms"]/1000*8
    # Use corpus-specific prefix data, both predictors and held-out-size fits.
    whole=load_corpus(corpus,"train")
    import re
    sizes={"raw_bytes":len(whole),"unique_bytes":sum(map(len,set(re.findall(rb" ?[^\s]+|\s+",whole))))}
    estimates=[]
    for predictor,size in sizes.items():
        estimates.append(predict(fit(rows,predictor),size,k))
        for n in sorted({r["raw_bytes"] for r in rows}):
            estimates.append(predict(fit([r for r in rows if r["raw_bytes"]!=n],predictor),size,k))
    return max(estimates)*3  # Three timed training runs in one model cell.


def trained_model(audit,corpus,k,variant):
    name=f"{corpus}|{k}|{variant}"
    data=load_corpus(corpus,"train")
    if name in audit["models"]:
        model=audit["models"][name]
        if model['train_prefix_kib'] or model['train_sha256']!=digest(data):
            raise ValueError("Stale/prefix model: run python -m rq3.upgrade_full first")
        return model
    prefix=0
    guard(f"train {name} prefix={prefix}",train_estimate(corpus,variant,k,prefix))
    runs=1 if variant=="naive" else 3
    samples=[]; merges=None
    for _ in range(runs):
        start=time.perf_counter(); current=bpe.train(data,k,variant); samples.append((time.perf_counter()-start)*1000)
        if merges is not None and current!=merges:
            raise ValueError("Training runs disagree")
        merges=current
    model=dict(merges=merges,train_ms_runs=samples,train_ms=median(samples),train_runs=runs,
               train_prefix_kib=prefix,train_bytes=len(data),train_sha256=digest(data),
               merges_sha256=digest(json.dumps(merges).encode()),m_actual=len(merges))
    for peer in audit["models"].values():
        if peer["train_sha256"]==model["train_sha256"] and peer.get("k")==k and peer["merges_sha256"]!=model["merges_sha256"]:
            raise ValueError("Variant merge mismatch for equal training input")
    model["k"]=k
    audit["models"][name]=model; save(audit)
    print(f"TRAIN {name}: m={len(merges)} ms={model['train_ms']:.3f} runs={runs} prefix={prefix}",flush=True)
    return model


def run_results(audit):
    RESULTS.parent.mkdir(exist_ok=True)
    existing=read_rows(RESULTS)
    done={key(r) for r in existing}
    if len(done)!=len(existing): raise ValueError("Duplicate existing results")
    for variant in VARIANTS:
        for corpus in CORPORA:
            for k in KS:
                model=trained_model(audit,corpus,k,variant)
                merges=[tuple(p) for p in model["merges"]]
                for test in CORPORA:
                    base=dict(rq="3",dataset=test,file=f"{test.lower()}_test_1mib.txt",state="original",codec="bpe",train_variant=variant,k_merges=k,train_corpus=corpus,test_corpus=test)
                    ident=key(base)
                    if ident in done: continue
                    data=load_corpus(test,"test")
                    guard(f"timing compression {ident}",60)
                    result,blob,times=measure(lambda b:bpe.compress_with_merges(b,merges),bpe.decompress,data)
                    m=int.from_bytes(blob[12:14],"big")
                    n=int.from_bytes(blob[14+3*m:22+3*m],"big")
                    payload=len(blob)-(22+3*m)
                    notes={n:model[n] for n in ("train_runs","train_prefix_kib","train_bytes","train_sha256","merges_sha256","m_actual")}
                    notes.update(train_stat="single" if variant=="naive" else "median3",payload_bytes=payload,
                                 mem_scope="compress_decompress_pretrained",mem_test_bytes=len(data),mem_training_included="false",timing_runs=3)
                    row=dict(base,**result,ratio_tokens_only=payload/len(data),n_tokens=n,train_ms=model["train_ms"],notes=notes_text(notes))
                    audit["rows"][ident]=dict(times,output_sha256=digest(data),notes=notes)
                    save(audit)
                    append_row(str(RESULTS),row);done.add(ident)
                    print(f"ROW {len(done)}/38 {ident} bytes={len(blob)} tokens={n} peak={result['peak_mem_kib']:.1f}KiB",flush=True)
    for test in CORPORA:
        base=dict(rq="3",dataset=test,file=f"{test.lower()}_test_1mib.txt",state="original",codec="lzw",test_corpus=test)
        ident=key(base)
        if ident in done: continue
        result,blob,times=measure(lzw.compress,lzw.decompress,load_corpus(test,"test"))
        row=dict(base,**result,notes=notes_text(dict(timing_runs=3,mem_scope="compress_decompress",mem_test_bytes=result["orig_bytes"])))
        audit["rows"][ident]=times;save(audit);append_row(str(RESULTS),row)
        print("LZW",test,result,flush=True)


def run_edges(audit):
    path=ROOT/"results/results_edge.csv"
    existing=read_rows(path)
    done={(r["file"],r["train_variant"]) for r in existing if r["codec"]=="bpe"}
    if "edge_original_sha256" not in audit:
        audit["edge_original_sha256"]=digest(path.read_bytes()) if path.exists() else None
        audit["edge_original_bytes"]=len(path.read_bytes()) if path.exists() else 0
        save(audit)
    for variant in VARIANTS:
        for name,data in EDGE_CASES.items():
            if (name,variant) in done: continue
            k=3 if name=="edge_aaabdaaabac.bin" else 256
            start=time.perf_counter();merges=bpe.train(data,k,variant);train_ms=(time.perf_counter()-start)*1000
            result,blob,times=measure(lambda b:bpe.compress_with_merges(b,merges),bpe.decompress,data)
            m=len(merges);n=int.from_bytes(blob[14+3*m:22+3*m],"big");payload=len(blob)-22-3*m
            row=dict(rq="edge",dataset="",file=name,state="original",codec="bpe",train_variant=variant,k_merges=k,
                     **result,n_tokens=n,train_ms=train_ms,ratio_tokens_only=payload/len(data) if data else None,
                     notes=notes_text(dict(train_runs=1,m_actual=m,payload_bytes=payload,mem_scope="compress_decompress_pretrained",mem_test_bytes=len(data))))
            if name=="edge_aaabdaaabac.bin" and (merges!=[(97,97),(97,98),(256,257)] or len(blob)!=39):
                raise ValueError("D7 mismatch")
            append_row(str(path),row)
            print("EDGE",variant,name,"m",m,"tokens",n,flush=True)


def train_memory(audit):
    path=OUT/"train_mem.csv"
    if path.exists(): raise FileExistsError("Training-memory measurements already exist; no repeat")
    fields=["corpus","variant","train_prefix_kib","train_bytes","k","m","peak_train_mem_kib","traced_elapsed_ms","train_sha256","scope"]
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for corpus in CORPORA:
            data=load_corpus(corpus,"train")[:131072]
            expected=None
            for variant in VARIANTS:
                source=OUT/("phase4_preflight.json" if corpus=="E1" else "phase3_measurements.json")
                row=next(c for c in json.loads(source.read_text())["cells"] if c["raw_bytes"]==131072 and c["k"]==256 and c["variant"]==variant)
                guard(f"training-memory {corpus} {variant} 128KiB K=256",max(10,row["train_ms"]/1000*30))
                tracemalloc.start();start=time.perf_counter()
                try:
                    merges=bpe.train(data,256,variant)
                    peak=tracemalloc.get_traced_memory()[1]/1024
                finally:
                    elapsed=(time.perf_counter()-start)*1000;tracemalloc.stop()
                if expected is None: expected=merges
                if merges!=expected: raise ValueError("Training-memory variant mismatch")
                result=dict(corpus=corpus,variant=variant,train_prefix_kib=128,train_bytes=len(data),k=256,m=len(merges),
                            peak_train_mem_kib=peak,traced_elapsed_ms=elapsed,train_sha256=digest(data),scope="training_only_128KiB_prefix_single_traced_run")
                writer.writerow(result);f.flush();print("TRAIN_MEM",result,flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage",choices=("results","edge","train-memory","verify-hashes"))
    args=ap.parse_args()
    preflight=json.loads((OUT/"phase4_preflight.json").read_text())
    if not preflight["safe_to_start_naive_full_k256"]: raise SystemExit("STOP: preflight bound >300s")
    audit=json.loads(AUDIT.read_text()) if AUDIT.exists() else dict(protected_before=protected_hashes(),models={},rows={})
    before=protected_hashes()
    audit.setdefault('execution_sources',[]).append(dict(stage=args.stage,sha256=before))
    if args.stage=="results": run_results(audit)
    elif args.stage=="edge": run_edges(audit)
    elif args.stage=="train-memory": train_memory(audit)
    assert before==protected_hashes(), "Source files changed during measurement"
    save(audit)
    print("Protected hashes: unchanged",flush=True)


if __name__=="__main__": main()
