"""Archive mixed-scope measurements and import verified full-corpus training.

The supplement records actual naive training, not an estimated time. Its merge
hash is checked against a newly trained full-corpus inc model. Compression and
memory of the eight replaced test rows are measured afresh by run_rq3 results.
"""
import csv
import json
from pathlib import Path

from common.results_schema import COLUMNS
from rq3 import bpe
from rq3.run_rq3 import ROOT, RESULTS, AUDIT, OUT, digest, key, save, read_rows
from rq3.phase3_feasibility import load_corpus


def main():
    audit=json.loads(AUDIT.read_text())
    if audit.get('scope_version')=='full_1mib':
        print('Already upgraded; use run_rq3 results to resume any missing rows.')
        return
    supplement=ROOT/'final_submission/naive_full_experiment.json'
    cells=json.loads(supplement.read_text())['cells']
    expected={(c,k) for c in ('V1','E1') for k in (1024,3840)}
    assert {(c['corpus'],c['k']) for c in cells}==expected and len(cells)==4
    replacements={}
    for cell in cells:
        corpus,k=cell['corpus'],cell['k']
        data=load_corpus(corpus,'train')
        merges=bpe.train(data,k,'inc')
        merge_hash=digest(json.dumps(merges).encode())
        assert cell['matches_full_inc'] is True
        assert cell['raw_bytes']==len(data) and cell['input_sha256']==digest(data)
        assert cell['m_actual']==len(merges)==k and cell['merges_sha256']==merge_hash
        assert cell['train_ms']>0 and cell['train_runs']==1
        peer=audit['models'][f'{corpus}|{k}|inc']
        assert peer['merges_sha256']==merge_hash and peer['train_sha256']==digest(data)
        replacements[f'{corpus}|{k}|naive']=dict(
            merges=merges,train_ms_runs=[cell['train_ms']],train_ms=cell['train_ms'],
            train_runs=1,train_prefix_kib=0,train_bytes=len(data),train_sha256=digest(data),
            merges_sha256=merge_hash,m_actual=k,k=k,
            training_source='final_submission/naive_full_experiment.json',
            training_source_sha256=digest(supplement.read_bytes()),
            verification='current inc merge list equals measured naive merge hash')
    archive=ROOT/'results/archive/mixed_scope'
    archive.mkdir(parents=True,exist_ok=True)
    for path in (RESULTS,AUDIT,ROOT/'results/results_edge.csv'):
        target=archive/path.name
        if target.exists():
            raise FileExistsError(f'Archive exists; refusing to overwrite: {target}')
        target.write_bytes(path.read_bytes())
    rows=read_rows(RESULTS)
    kept=[]
    for row in rows:
        if row['train_variant']=='naive' and int(row['k_merges'])>256:
            audit['rows'].pop(key(row),None)
        else:
            kept.append(row)
    audit['models'].update(replacements)
    audit['scope_version']='full_1mib'
    audit['migration_archive']='results/archive/mixed_scope'
    # BPE edge outputs change under the corrected singleton merge rule.
    edge=ROOT/'results/results_edge.csv'
    original=edge.read_bytes()[:audit['edge_original_bytes']]
    assert digest(original)==audit['edge_original_sha256']
    edge.write_bytes(original)
    with RESULTS.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=COLUMNS)
        writer.writeheader();writer.writerows(kept)
    save(audit)
    print('Archived originals; imported four measured training cells; eight test rows need measurement.')


if __name__=='__main__': main()
