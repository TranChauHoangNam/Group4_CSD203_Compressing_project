"""Aggregation and artifact checks use only small synthetic records."""
import csv

import pytest

from rq1.analyze_rq1 import METRICS, summarize, generate, compare_outputs, main


@pytest.fixture
def source(tmp_path):
    path = tmp_path/'measurements.csv'
    rows = []
    for seed, value in enumerate((1, 9, 2), 1):
        row = dict(dataset='C1', size_kib=256, codec='rle', seed=seed)
        row.update({metric: value*(index+1) for index, metric in enumerate(METRICS)})
        rows.append(row)
    row = dict(dataset='V1', size_kib=256, codec='lzw', seed='')
    row.update({metric: 7*(index+1) for index, metric in enumerate(METRICS)})
    rows.append(row)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path, rows


def test_median_extrema_singleton_and_source_lines(source):
    _, rows = source
    result = summarize(rows)
    assert len(result) == 2
    assert result[0]['n_samples'] == 3
    assert result[0]['source_csv_lines'] == '2,3,4'
    assert result[1]['n_samples'] == 1
    for index, metric in enumerate(METRICS, 1):
        assert result[0][metric+'_median'] == 2*index
        assert result[0][metric+'_min'] == index
        assert result[0][metric+'_max'] == 9*index
        assert result[1][metric+'_median'] == result[1][metric+'_min'] == result[1][metric+'_max'] == 7*index


@pytest.fixture
def artifacts(source, tmp_path):
    path, _ = source
    out = tmp_path/'out'
    generate(path, out)
    return path, out


def test_tables_figures_and_check_mode(artifacts):
    source, out = artifacts
    for name in ('ratio', 'throughput', 'memory'):
        assert (out/f'rq1_{name}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        assert (out/f'rq1_{name}.md').stat().st_size > 0
        with (out/f'rq1_{name}.csv').open(encoding='utf-8', newline='') as stream:
            assert len(list(csv.DictReader(stream))) == 2
    assert main(['--csv', str(source), '--out-dir', str(out), '--check']) == 0


def test_check_rejects_modified_numeric_cell(artifacts, tmp_path):
    source, out = artifacts
    regenerated = tmp_path/'regenerated'
    generate(source, regenerated)
    path = out/'rq1_ratio.csv'
    path.write_text(path.read_text().replace(',2,1,9', ',20,1,9'), encoding='utf-8')
    with pytest.raises(ValueError, match='Table differs'):
        compare_outputs(out, regenerated)


def test_check_rejects_empty_figure(artifacts, tmp_path):
    source, out = artifacts
    regenerated = tmp_path/'regenerated'
    generate(source, regenerated)
    (out/'rq1_memory.png').write_bytes(b'')
    with pytest.raises(ValueError, match='Missing or empty figure'):
        compare_outputs(out, regenerated)
