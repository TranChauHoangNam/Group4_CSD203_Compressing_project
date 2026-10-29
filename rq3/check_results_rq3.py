"""Validate the full-corpus RQ3 matrix and its measurement audit."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from common.results_schema import COLUMNS, validate_row
from common.edge_provenance import verify_original
from rq3.run_rq3 import CORPORA, VARIANTS, KS, EDGE_CASES, key, parse_notes

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    with path.open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        assert reader.fieldnames==COLUMNS,"CSV header differs"
        return list(reader)


def check_rows(rows,audit,manifest):
    checks=[]
    def check(title,fn):
        try:
            fn();checks.append((title,True,""))
        except (AssertionError,KeyError,ValueError,TypeError,ZeroDivisionError) as exc:
            checks.append((title,False,str(exc)))
    expected={('bpe',v,str(k),a,b,f'{b.lower()}_test_1mib.txt') for v in VARIANTS for k in KS for a in CORPORA for b in CORPORA}
    expected|={('lzw','','','',b,f'{b.lower()}_test_1mib.txt') for b in CORPORA}
    def matrix():
        actual=[tuple(r.get(c,'') for c in ('codec','train_variant','k_merges','train_corpus','test_corpus','file')) for r in rows]
        assert len(rows)==38,f"rows={len(rows)}, expected=38"
        assert len(set(actual))==len(actual),"Duplicate key"
        assert set(actual)==expected,"Missing/unapproved matrix cells"
    check("38 rows, approved matrix and unique keys",matrix)
    def schema():
        for r in rows:
            validate_row(r)
            assert r['rq']=='3' and r['state']=='original' and r['dataset']==r['test_corpus']
            assert r['status']=='ok' and r['roundtrip_ok']=='true'
            source=manifest[r['file']]
            assert int(r['orig_bytes'])==source['bytes']
            assert r['output_check']==source['sha256'][:16]
    check("Schema, roundtrip, dataset and output hashes",schema)
    def metrics():
        for r in rows:
            orig,comp=int(r['orig_bytes']),int(r['comp_bytes'])
            assert math.isclose(float(r['ratio']),comp/orig,rel_tol=0,abs_tol=1e-5)
            assert float(r['peak_mem_kib'])>0
            notes=parse_notes(r['notes'])
            assert int(notes['mem_test_bytes'])==orig,"Memory pass not on full test"
            for ms,kibs in (('comp_ms','comp_kibs'),('decomp_ms','decomp_kibs')):
                assert float(r[ms])>0
                assert math.isclose(float(r[kibs]),orig/1024/(float(r[ms])/1000),rel_tol=1.1e-5)
            if r['codec']=='bpe':
                n,m=int(r['n_tokens']),int(notes['m_actual'])
                payload=(12*n+7)//8
                assert 0<=m<=int(r['k_merges'])
                assert int(notes['payload_bytes'])==payload
                assert comp==22+3*m+payload,"Wire-format accounting differs"
                assert math.isclose(float(r['ratio_tokens_only']),payload/orig,rel_tol=0,abs_tol=1e-5)
                assert math.isclose(float(r['bytes_per_token']),orig/n,rel_tol=0,abs_tol=1e-5)
                assert float(r['ratio_tokens_only'])<=float(r['ratio'])
    check("Ratios, tokens, fixed-12-bit accounting, full-test memory",metrics)
    def provenance():
        for r in rows:
            if r['codec']!='bpe':
                assert all(r[c]=='' for c in ('train_variant','k_merges','train_corpus','train_ms'))
                continue
            v,k=r['train_variant'],int(r['k_merges']);notes=parse_notes(r['notes'])
            prefix=0
            runs=1 if v=='naive' else 3
            assert int(notes['train_prefix_kib'])==prefix
            assert int(notes['train_runs'])==runs
            assert notes['train_stat']==('single' if runs==1 else 'median3')
            expected_bytes=131072 if prefix else manifest[f"{r['train_corpus'].lower()}_train_1mib.txt"]['bytes']
            assert int(notes['train_bytes'])==expected_bytes
            assert notes['mem_scope']=='compress_decompress_pretrained' and notes['mem_training_included']=='false'
            model=audit['models'][f"{r['train_corpus']}|{k}|{v}"]
            assert len(model['train_ms_runs'])==runs
            assert math.isclose(float(r['train_ms']),median(model['train_ms_runs']),rel_tol=5.1e-6)
            for field in ('train_sha256','merges_sha256'):
                assert notes[field]==model[field]
            assert notes['train_sha256']==manifest[f"{r['train_corpus'].lower()}_train_1mib.txt"]['sha256']
            observed=audit['rows'][key(r)]
            assert observed['output_sha256']==manifest[r['file']]['sha256']
        for r in rows:
            samples=audit['rows'][key(r)]
            for field in ('comp_ms','decomp_ms'):
                assert len(samples[field+'_runs'])==3
                assert math.isclose(float(r[field]),median(samples[field+'_runs']),rel_tol=5.1e-6)
    check("Training scope, repetitions and medians trace to audit",provenance)
    def equivalence():
        groups={}
        for r in rows:
            if r['codec']!='bpe': continue
            notes=parse_notes(r['notes'])
            group=(r['train_corpus'],r['test_corpus'],r['k_merges'],notes['train_sha256'])
            groups.setdefault(group,[]).append(r)
        for group,items in groups.items():
            assert len({(r['n_tokens'],r['comp_bytes']) for r in items})==1,f"Equal-input variants differ: {group}"
            assert len({parse_notes(r['notes'])['merges_sha256'] for r in items})==1
        for a in CORPORA:
            for b in CORPORA:
                for k in KS:
                    items=[r for r in rows if r['codec']=='bpe' and r['train_corpus']==a and r['test_corpus']==b and r['k_merges']==str(k)]
                    assert len(items)==3
                    assert len({parse_notes(r['notes'])['train_sha256'] for r in items})==1
    check("Variant equivalence only for identical training inputs",equivalence)
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=ROOT/'results/results_rq3.csv')
    args=parser.parse_args()
    audit=json.loads((ROOT/'rq3/out/rq3_run_audit.json').read_text())
    manifest=json.loads((ROOT/'docs/manifest.json').read_text(encoding='utf-8'))['files']
    checks=check_rows(read(args.csv),audit,manifest)
    try:
        edges=read(ROOT/'results/results_edge.csv')
        bpes=[r for r in edges if r['codec']=='bpe']
        assert len(bpes)==18
        assert {(r['file'],r['train_variant']) for r in bpes}=={(f,v) for f in EDGE_CASES for v in VARIANTS}
        for r in bpes:
            validate_row(r);data=EDGE_CASES[r['file']]
            assert r['rq']=='edge' and r['dataset']=='' and r['status']=='ok' and r['roundtrip_ok']=='true'
            assert r['output_check']==hashlib.sha256(data).hexdigest()[:16]
            assert int(r['orig_bytes'])==len(data)
            if not data:
                assert r['ratio']==r['ratio_tokens_only']==r['bytes_per_token']==''
            if r['file']=='edge_aaabdaaabac.bin':
                assert r['k_merges']=='3' and r['comp_bytes']=='39' and r['n_tokens']=='5'
        raw=(ROOT/'results/results_edge.csv').read_bytes()
        verify_original(raw, audit)
        checks.append(('18 BPE edge rows; original edge evidence preserved',True,''))
    except (AssertionError,KeyError,ValueError) as exc:
        checks.append(('18 BPE edge rows; original edge evidence preserved',False,str(exc)))
    try:
        with (ROOT/'rq3/out/train_mem.csv').open(newline='',encoding='utf-8') as f: memory=list(csv.DictReader(f))
        assert len(memory)==6
        assert {(r['corpus'],r['variant']) for r in memory}=={(c,v) for c in CORPORA for v in VARIANTS}
        missing_data=[]
        for r in memory:
            assert r['train_prefix_kib']=='128' and r['train_bytes']=='131072' and r['k']=='256'
            assert float(r['peak_train_mem_kib'])>0
            assert r['scope']=='training_only_128KiB_prefix_single_traced_run'
            path=ROOT/'data/wiki'/f"{r['corpus'].lower()}_train_1mib.txt"
            if not path.is_file():
                if path not in missing_data:
                    missing_data.append(path)
                continue
            actual=path.read_bytes()[:131072]
            assert r['train_sha256']==hashlib.sha256(actual).hexdigest()
        for corpus in CORPORA:
            same=[r for r in memory if r['corpus']==corpus]
            assert len({(r['train_sha256'],r['m']) for r in same})==1
        reason="thi\u1ebfu "+', '.join(str(p) for p in missing_data)+"; see README 'Data' section" if missing_data else ''
        checks.append(('6 separate training-memory rows, 128 KiB K=256',None if missing_data else True,reason))
    except (AssertionError,KeyError,ValueError) as exc:
        checks.append(('6 separate training-memory rows, 128 KiB K=256',False,str(exc)))
    for title,passed,reason in checks:
        if passed is None:
            print('CH\u01afA KI\u1ec2M ('+reason+') '+title)
        else:
            print(('\u0110\u1ea0T' if passed else 'KH\u00d4NG \u0110\u1ea0T')+' '+title+(': '+reason if reason else ''))
    passed_count=sum(ok is True for _,ok,_ in checks)
    unchecked=sum(ok is None for _,ok,_ in checks)
    print(f"SUMMARY: {passed_count}/{len(checks)} checks passed"+(f"; {unchecked} unchecked (missing data)" if unchecked else ''))
    if any(ok is False for _,ok,_ in checks):
        return 1
    return 2 if unchecked else 0


if __name__=='__main__': raise SystemExit(main())
