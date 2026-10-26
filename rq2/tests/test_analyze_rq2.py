"""Fixture CSV tổng hợp nhỏ chỉ dành cho test, không lấy kết quả thật."""
import csv

import pytest

from rq2.analyze_rq2 import CODECS, read_rows, summarize, write_tables


@pytest.fixture
def synthetic_csv(tmp_path):
    path = tmp_path / "synthetic.csv"
    columns = ("file", "codec", "state", "seed", "ratio", "h0_ratio", "comp_kibs",
               "decomp_kibs", "peak_mem_kib", "roundtrip_ok", "notes")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for file in ("sample-a", "sample-b"):
            for codec in CODECS:
                for state, seed, value in [("original", "", .5), ("runs", "", .2),
                                            ("shuffled", 1, .6), ("shuffled", 2, .9),
                                            ("shuffled", 3, 1.2)]:
                    writer.writerow(dict(file=file, codec=codec, state=state, seed=seed,
                                         ratio=value, h0_ratio=.1, comp_kibs=value * 100,
                                         decomp_kibs=value * 200, peak_mem_kib=value * 10,
                                         roundtrip_ok="true", notes="ratio_no_header=0.123456" if codec == "huffman" else ""))
    return path


def test_seed_mean_min_max_and_speed(synthetic_csv):
    ratios, speeds = summarize(read_rows(synthetic_csv))
    shuffled = next(row for row in ratios if row["file"] == "sample-a" and row["codec"] == "rle" and row["state"] == "shuffled")
    assert shuffled["ratio"] == pytest.approx(.9)
    assert shuffled["ratio_min"] == .6
    assert shuffled["ratio_max"] == 1.2
    assert shuffled["ratio_no_header"] == ""
    speed = next(row for row in speeds if row["file"] == "sample-a" and row["codec"] == "rle" and row["state"] == "shuffled")
    assert speed["comp_kibs"] == pytest.approx(90)
    assert speed["decomp_kibs"] == pytest.approx(180)
    assert speed["peak_mem_kib"] == pytest.approx(9)


def test_tables_have_one_row_per_group_and_are_idempotent(synthetic_csv, tmp_path):
    ratios, speeds = summarize(read_rows(synthetic_csv))
    assert len(ratios) == len(speeds) == 18  # 2 files x 3 codecs x 3 states
    assert next(r for r in ratios if r["codec"] == "huffman")["ratio_no_header"] == .123456
    out = tmp_path / "out"
    write_tables(out, ratios, speeds)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    write_tables(out, ratios, speeds)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    for name in ("rq2_table_ratio", "rq2_table_speed"):
        assert len(read_rows(out / (name + ".csv"))) == 18
        assert len((out / (name + ".md")).read_text(encoding="utf-8").splitlines()) == 20


def test_existing_different_output_not_overwritten(synthetic_csv, tmp_path):
    ratios, speeds = summarize(read_rows(synthetic_csv))
    out = tmp_path / "out"
    out.mkdir()
    target = out / "rq2_table_ratio.csv"
    target.write_bytes(b"preserve existing file")
    with pytest.raises(FileExistsError):
        write_tables(out, ratios, speeds)
    assert target.read_bytes() == b"preserve existing file"


def test_duplicate_seed_rejected(synthetic_csv):
    rows = read_rows(synthetic_csv)
    rows.append(dict(next(row for row in rows if row["state"] == "shuffled")))
    with pytest.raises(ValueError, match="seed"):
        summarize(rows)


def test_h0_gap_and_codec_ties(synthetic_csv):
    from rq2.analyze_rq2 import compare_codecs
    ratios, speeds = summarize(read_rows(synthetic_csv))
    assert ratios[0]['ratio_minus_h0'] == pytest.approx(.4)
    assert all(r['tốt hơn mốc H0/8?'] == 'không' for r in ratios + speeds)
    comparisons = compare_codecs(ratios)
    assert comparisons[0]['codec thắng (ratio nhỏ nhất)'] == 'huffman, rle, lzw'
    rows = read_rows(synthetic_csv)
    next(r for r in rows if r['codec'] == 'rle' and r['state'] == 'original')['ratio'] = '.05'
    ratios, speeds = summarize(rows)
    assert next(r for r in ratios if r['codec'] == 'rle' and r['state'] == 'original')['tốt hơn mốc H0/8?'] == 'có'
    assert compare_codecs(ratios)[0]['codec thắng (ratio nhỏ nhất)'] == 'rle'


@pytest.mark.parametrize('mutation', [None, 'trace', 'prose', 'table'])
def test_report_trace_detects_tampering(synthetic_csv, tmp_path, mutation):
    from rq2.analyze_rq2 import (RATIO_COLUMNS, SPEED_COLUMNS, COMPARISON_COLUMNS,
                                 compare_codecs, table_markdown)
    from rq2.build_report import TRACE_COLUMNS
    from rq2.verify_report import verify
    ratios, speeds = summarize(read_rows(synthetic_csv))
    trace = dict(zip(TRACE_COLUMNS, ('T001', 'ratio', 'sample-a/huffman/original',
                                     'CSV:2', 'mean(ratio)', '0.5')))
    blocks = [('ratio', table_markdown(ratios, RATIO_COLUMNS)),
              ('speed', table_markdown(speeds, SPEED_COLUMNS)),
              ('comparison', table_markdown(compare_codecs(ratios), COMPARISON_COLUMNS)),
              ('trace', table_markdown([trace], TRACE_COLUMNS))]
    text = '**0.5** [T001]\n'
    for name, content in blocks:
        if name == 'trace':
            text += '## Truy vết số liệu\n'
        text += f'<!-- BEGIN:{name} -->\n{content}<!-- END:{name} -->\n'
    if mutation == 'trace':
        text = text.replace('mean(ratio) | 0.5', 'mean(ratio) | 0.6')
    elif mutation == 'prose':
        text = text.replace('**0.5**', '**0.6**')
    elif mutation == 'table':
        text = text.replace('| 0.5 |', '| 0.6 |', 1)
    report = tmp_path / 'report.md'
    report.write_text(text, encoding='utf-8')
    mechanism = tmp_path / 'mechanism.txt'
    mechanism.write_text('', encoding='utf-8')
    ok, messages = verify(synthetic_csv, report, mechanism)
    assert ok is (mutation is None)
    assert ('LỆCH' in '\n'.join(messages)) is (mutation is not None)
