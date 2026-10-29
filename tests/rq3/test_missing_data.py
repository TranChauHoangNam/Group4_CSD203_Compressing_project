"""Missing corpora are unchecked; actual validation failures take precedence."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

import rq3.check_results_rq3 as checker

SOURCE_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('missing,corruption,expected', [
    ((), '', 0),
    (('V1',), '', 2),
    (('V1', 'E1'), '', 2),
    (('V1',), 'memory', 1),
    (('V1',), 'ratio', 1),
    ((), 'input_hash', 1),
])
def test_checker_exit_status_and_missing_message(tmp_path, monkeypatch, capsys, missing, corruption, expected):
    for relative in ('results/results_rq3.csv', 'results/results_edge.csv',
                     'rq3/out/rq3_run_audit.json', 'docs/manifest.json'):
        target = tmp_path/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE_ROOT/relative, target)
    source = SOURCE_ROOT/'rq3/out/train_mem.csv'
    with source.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, memory = reader.fieldnames, list(reader)
    for corpus, byte in (('V1', b'a'), ('E1', b'b')):
        data = byte*131072
        path = tmp_path/'data/wiki'/f'{corpus.lower()}_train_1mib.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        if corpus not in missing:
            path.write_bytes(data if corruption != 'input_hash' else b'x'*131072)
        for row in memory:
            if row['corpus'] == corpus:
                row['train_sha256'] = hashlib.sha256(data).hexdigest()
    if corruption == 'memory':
        memory[0]['peak_train_mem_kib'] = '-1'
    with (tmp_path/'rq3/out/train_mem.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(memory)
    if corruption == 'ratio':
        path = tmp_path/'results/results_rq3.csv'
        with path.open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        rows[0]['ratio'] = '99'
        with path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    monkeypatch.setattr(checker, 'ROOT', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['check_results_rq3'])
    assert checker.main() == expected
    output = capsys.readouterr().out
    assert 'SUMMARY:' in output
    assert 'Traceback' not in output
    if expected == 2:
        assert 'CH\u01afA KI\u1ec2M' in output
        assert '1 unchecked' in output
        assert "see README 'Data' section" in output
    if expected == 0:
        assert '7/7 checks passed' in output
