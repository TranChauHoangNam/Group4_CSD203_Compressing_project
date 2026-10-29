"""Runner/checker contracts on synthetic records, without corpus benchmarks."""
import hashlib
from statistics import median

import pytest

from common.results_schema import COLUMNS, finalize_row, _fmt
from rq3.run_rq3 import CORPORA, VARIANTS, KS, key, notes_text, measure, guard
from rq3.check_results_rq3 import check_rows


def fixture_matrix():
    digest=hashlib.sha256(b"abcdefgh").hexdigest()
    manifest={f"{c.lower()}_{part}_1mib.txt":dict(bytes=8,sha256=digest) for c in CORPORA for part in ('train','test')}
    rows=[];audit=dict(models={},rows={})
    for variant in VARIANTS:
        for a in CORPORA:
            for k in KS:
                prefix=0
                runs=1 if variant=='naive' else 3
                notes=dict(train_prefix_kib=prefix,train_runs=runs,train_stat='single' if runs==1 else 'median3',
                           train_bytes=131072 if prefix else 8,train_sha256=digest,merges_sha256=f'{a}-{k}-{prefix}',
                           m_actual=3,payload_bytes=6,mem_scope='compress_decompress_pretrained',mem_test_bytes=8,mem_training_included='false')
                audit['models'][f'{a}|{k}|{variant}']=dict(train_ms_runs=[5] if runs==1 else [4,5,6],train_sha256=notes['train_sha256'],merges_sha256=notes['merges_sha256'])
                for b in CORPORA:
                    row=dict(rq='3',dataset=b,file=f'{b.lower()}_test_1mib.txt',state='original',codec='bpe',train_variant=variant,k_merges=k,train_corpus=a,test_corpus=b,
                             orig_bytes=8,comp_bytes=37,ratio_tokens_only=.75,n_tokens=4,train_ms=5,comp_ms=2,decomp_ms=3,peak_mem_kib=10,output_check=digest[:16],roundtrip_ok=True, status="ok",notes=notes_text(notes))
                    rows.append({c:_fmt(finalize_row(row).get(c)) for c in COLUMNS})
                    audit['rows'][key(row)]=dict(comp_ms_runs=[1,2,3],decomp_ms_runs=[2,3,4],output_sha256=digest)
    for b in CORPORA:
        row=dict(rq='3',dataset=b,file=f'{b.lower()}_test_1mib.txt',state='original',codec='lzw',test_corpus=b,orig_bytes=8,comp_bytes=20,comp_ms=2,decomp_ms=3,peak_mem_kib=10,output_check=digest[:16],roundtrip_ok=True, status="ok",notes='mem_test_bytes=8')
        rows.append({c:_fmt(finalize_row(row).get(c)) for c in COLUMNS})
        audit['rows'][key(row)]=dict(comp_ms_runs=[1,2,3],decomp_ms_runs=[2,3,4])
    return rows,audit,manifest


def test_checker_accepts_complete_approved_matrix():
    checks=check_rows(*fixture_matrix())
    assert all(passed for _,passed,_ in checks),checks


@pytest.mark.parametrize('field,value', [('ratio','99'),('bytes_per_token','99'),('ratio_tokens_only','99'),('comp_bytes','999'),('roundtrip_ok','false'),('output_check','0'*16),('train_ms','99'),('comp_ms','99')])
def test_checker_rejects_corruption(field,value):
    rows,audit,manifest=fixture_matrix();rows[0][field]=value
    assert not all(ok for _,ok,_ in check_rows(rows,audit,manifest))


def test_checker_rejects_duplicate_or_missing_cell():
    rows,audit,manifest=fixture_matrix();rows[-1]=rows[0].copy()
    assert not check_rows(rows,audit,manifest)[0][1]


def test_checker_rejects_unapproved_naive_training_scope():
    rows,audit,manifest=fixture_matrix()
    target=next(r for r in rows if r['train_variant']=='naive' and r['k_merges']=='3840')
    target['notes']=target['notes'].replace('train_prefix_kib=0','train_prefix_kib=128')
    assert not all(ok for _,ok,_ in check_rows(rows,audit,manifest))


def test_roundtrip_failure_stops_before_traced_pass():
    with pytest.raises(ValueError,match='SHA-256'):
        measure(lambda data:data,lambda blob:b'corrupt',b'original',repeats=1)


def test_guard_rejects_over_300_seconds():
    with pytest.raises(SystemExit,match='>300s'):
        guard('test only',301)
