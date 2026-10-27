"""Tests for verify_rq1_report on full draft, quantitative claims, and small synthetic records."""
import csv
from pathlib import Path
import pytest

from rq1.analyze_rq1 import METRICS, generate
from rq1.verify_rq1_report import verify, main, ROOT


def test_verify_real_report():
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    out_dir = ROOT / 'rq1/out'
    csv_path = ROOT / 'results/results_rq1.csv'
    ok, messages, total_numeric, total_cells = verify(report_path, out_dir, csv_path)
    assert ok is True
    assert total_numeric == 1080
    assert total_cells == 1620
    assert any("ĐẠT kiểm tra 3 bảng tổng hợp" in m for m in messages)
    assert any("ĐẠT kiểm tra định lượng (a)" in m for m in messages)
    assert any("ĐẠT kiểm tra định lượng (b)" in m for m in messages)
    assert any("ĐẠT kiểm tra định lượng (c)" in m for m in messages)
    assert any("ĐẠT TỔNG THỂ" in m for m in messages)
    assert not any("KHÔNG ĐẠT" in m for m in messages)


def test_main_real_report():
    ret = main([])
    assert ret == 0


def test_verify_detects_modified_table_cell(tmp_path):
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    content = report_path.read_text(encoding='utf-8')
    tampered_content = content.replace('| 0.062256 |', '| 0.999999 |', 1)
    tampered_path = tmp_path / 'tampered_report.md'
    tampered_path.write_text(tampered_content, encoding='utf-8')

    ok, messages, _, _ = verify(tampered_path, ROOT / 'rq1/out', ROOT / 'results/results_rq1.csv')
    assert ok is False
    assert any("LỆCH bảng ratio" in m and "0.999999" in m for m in messages)
    assert any("KHÔNG ĐẠT" in m for m in messages)
    assert main(['--report', str(tampered_path)]) == 1


def test_verify_detects_missing_table(tmp_path):
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    content = report_path.read_text(encoding='utf-8')
    tampered_content = content.replace(
        content.split('<!-- BEGIN:ratio -->')[1].split('<!-- END:ratio -->')[0],
        '\n\n'
    )
    tampered_path = tmp_path / 'missing_table_report.md'
    tampered_path.write_text(tampered_content, encoding='utf-8')

    ok, messages, _, _ = verify(tampered_path, ROOT / 'rq1/out', ROOT / 'results/results_rq1.csv')
    assert ok is False
    assert any("Thiếu bảng ratio" in m for m in messages)
    assert any("KHÔNG ĐẠT" in m for m in messages)


def test_verify_detects_modified_lzw_throughput_claim(tmp_path):
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    content = report_path.read_text(encoding='utf-8')
    # Falsify claim: claim decompression is faster on 15/15 rows for C3
    tampered_content = content.replace(
        "decompression is slower on 15/15 rows",
        "decompression is faster on 15/15 rows"
    )
    tampered_path = tmp_path / 'tampered_lzw_claim.md'
    tampered_path.write_text(tampered_content, encoding='utf-8')

    ok, messages, _, _ = verify(tampered_path, ROOT / 'rq1/out', ROOT / 'results/results_rq1.csv')
    assert ok is False
    assert any("KHÔNG ĐẠT kiểm tra định lượng (a)" in m for m in messages)
    assert main(['--report', str(tampered_path)]) == 1


def test_verify_detects_modified_huffman_throughput_claim(tmp_path):
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    content = report_path.read_text(encoding='utf-8')
    # Falsify claim: change 50/50 to 45/50
    tampered_content = content.replace("(50/50 rows)", "(45/50 rows)")
    tampered_path = tmp_path / 'tampered_huff_claim.md'
    tampered_path.write_text(tampered_content, encoding='utf-8')

    ok, messages, _, _ = verify(tampered_path, ROOT / 'rq1/out', ROOT / 'results/results_rq1.csv')
    assert ok is False
    assert any("KHÔNG ĐẠT kiểm tra định lượng (b)" in m for m in messages)
    assert main(['--report', str(tampered_path)]) == 1


def test_verify_detects_modified_huffman_memory_claim(tmp_path):
    report_path = ROOT / 'rq1/RQ1_report_draft.md'
    content = report_path.read_text(encoding='utf-8')
    # Falsify claim: change range 67.0 to 68.0 to 20.0 to 30.0
    tampered_content = content.replace("67.0 to 68.0", "20.0 to 30.0").replace("67.0452 and 67.9862", "20.1234 and 29.5678")
    tampered_path = tmp_path / 'tampered_mem_claim.md'
    tampered_path.write_text(tampered_content, encoding='utf-8')

    ok, messages, _, _ = verify(tampered_path, ROOT / 'rq1/out', ROOT / 'results/results_rq1.csv')
    assert ok is False
    assert any("KHÔNG ĐẠT kiểm tra định lượng (c)" in m for m in messages)
    assert main(['--report', str(tampered_path)]) == 1


def test_synthetic_small_dataset(tmp_path):
    src_csv = tmp_path / 'small_results.csv'
    rows = []
    for seed, value in enumerate((1, 9, 2), 1):
        row = dict(dataset='C1', size_kib=256, codec='rle', seed=seed)
        row.update({metric: value * (idx + 1) for idx, metric in enumerate(METRICS)})
        rows.append(row)
    row = dict(dataset='V1', size_kib=256, codec='lzw', seed='')
    row.update({metric: 7 * (idx + 1) for idx, metric in enumerate(METRICS)})
    rows.append(row)

    with src_csv.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    out_dir = tmp_path / 'out'
    rendered = generate(src_csv, out_dir)

    draft_path = tmp_path / 'small_draft.md'
    draft_content = (
        "# Small Draft\n\n"
        "## Results\n\n"
        f"### Ratio\n\n<!-- BEGIN:ratio -->\n{rendered['ratio']}\n<!-- END:ratio -->\n\n"
        f"### Throughput\n\n<!-- BEGIN:throughput -->\n{rendered['throughput']}\n<!-- END:throughput -->\n\n"
        f"### Memory\n\n<!-- BEGIN:memory -->\n{rendered['memory']}\n<!-- END:memory -->\n\n"
    )
    draft_path.write_text(draft_content, encoding='utf-8')

    ok, messages, total_numeric, total_cells = verify(draft_path, out_dir, src_csv)
    assert ok is True
    assert total_numeric == (5 + 8 + 5) * 2  # 36 numeric cells
    assert total_cells == (8 + 11 + 8) * 2   # 54 total cells
    assert any("ĐẠT" in m for m in messages)

    tampered_content = draft_content.replace('2,3,4', '999,999', 1)
    draft_path.write_text(tampered_content, encoding='utf-8')

    ok_tampered, messages_tampered, _, _ = verify(draft_path, out_dir, src_csv)
    assert ok_tampered is False
    assert any("LỆCH bảng ratio" in m and "999,999" in m for m in messages_tampered)
    assert any("KHÔNG ĐẠT" in m for m in messages_tampered)
