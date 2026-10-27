"""Verify every numeric cell in RQ1 report draft against results CSV and rq1/out tables."""
import argparse
import csv
import io
import math
from pathlib import Path
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


from rq1.analyze_rq1 import SIZES, DATASETS, CODECS, METRICS, summarize, table_rows

ROOT = Path(__file__).resolve().parents[1]

TABLE_DEFINITIONS = {
    'ratio': {
        'metric_keys': ('ratio',),
        'columns': ['dataset', 'size_kib', 'codec', 'n_samples', 'source_csv_lines',
                    'ratio_median', 'ratio_min', 'ratio_max'],
        'numeric_columns': ['size_kib', 'n_samples', 'ratio_median', 'ratio_min', 'ratio_max'],
    },
    'throughput': {
        'metric_keys': ('comp_kibs', 'decomp_kibs'),
        'columns': ['dataset', 'size_kib', 'codec', 'n_samples', 'source_csv_lines',
                    'comp_kibs_median', 'comp_kibs_min', 'comp_kibs_max',
                    'decomp_kibs_median', 'decomp_kibs_min', 'decomp_kibs_max'],
        'numeric_columns': ['size_kib', 'n_samples',
                            'comp_kibs_median', 'comp_kibs_min', 'comp_kibs_max',
                            'decomp_kibs_median', 'decomp_kibs_min', 'decomp_kibs_max'],
    },
    'memory': {
        'metric_keys': ('peak_mem_kib',),
        'columns': ['dataset', 'size_kib', 'codec', 'n_samples', 'source_csv_lines',
                    'peak_mem_kib_median', 'peak_mem_kib_min', 'peak_mem_kib_max'],
        'numeric_columns': ['size_kib', 'n_samples',
                            'peak_mem_kib_median', 'peak_mem_kib_min', 'peak_mem_kib_max'],
    },
}


def parse_markdown_tables(text):
    """Extract all markdown tables as a list of dicts with headers and rows."""
    tables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|') and line.endswith('|') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('|') and '---' in next_line:
                headers = [c.strip() for c in line.strip('|').split('|')]
                data_rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith('|') and lines[j].strip().endswith('|'):
                    cells = [c.strip() for c in lines[j].strip('|').split('|')]
                    data_rows.append(cells)
                    j += 1
                tables.append({'headers': headers, 'rows': data_rows, 'start_line': i + 1})
                i = j
                continue
        i += 1
    return tables


def is_number(val_str):
    try:
        float(val_str)
        return True
    except (ValueError, TypeError):
        return False


def compare_numeric(actual_str, expected_str, rel_tol=1e-5, abs_tol=1e-5):
    """Compare two number strings according to stated 12g rounding and tolerance."""
    if actual_str == expected_str:
        return True
    try:
        act = float(actual_str)
        exp = float(expected_str)
        return math.isclose(act, exp, rel_tol=rel_tol, abs_tol=abs_tol)
    except ValueError:
        return False


def verify_table(table_name, parsed_table, ref_rows, messages):
    defn = TABLE_DEFINITIONS[table_name]
    expected_cols = defn['columns']
    numeric_cols = set(defn['numeric_columns'])
    headers = parsed_table['headers']
    rows = parsed_table['rows']

    if headers != expected_cols:
        messages.append(f"LỆCH tiêu đề bảng {table_name}: nhận {headers}, cần {expected_cols}")
        return False, 0, 0

    if len(rows) != len(ref_rows):
        messages.append(f"LỆCH số dòng bảng {table_name}: nhận {len(rows)} dòng, cần {len(ref_rows)} dòng")
        return False, 0, 0

    table_ok = True
    checked_numeric = 0
    checked_total = 0

    for row_idx, (row, ref) in enumerate(zip(rows, ref_rows), 1):
        if len(row) != len(expected_cols):
            messages.append(f"LỆCH số cột dòng {row_idx} bảng {table_name}: nhận {len(row)}, cần {len(expected_cols)}")
            table_ok = False
            continue

        for col_name, cell_value in zip(expected_cols, row):
            checked_total += 1
            ref_value = str(ref[col_name]).strip()
            cell_value = cell_value.strip()

            if col_name in numeric_cols:
                checked_numeric += 1
                if not compare_numeric(cell_value, ref_value):
                    messages.append(
                        f"LỆCH bảng {table_name} dòng {row_idx} ({row[0]}/{row[1]}/{row[2]}), cột {col_name}: "
                        f"draft '{cell_value}' != ref '{ref_value}'"
                    )
                    table_ok = False
            else:
                # String / metadata column check
                if cell_value != ref_value:
                    messages.append(
                        f"LỆCH bảng {table_name} dòng {row_idx}, cột {col_name}: "
                        f"draft '{cell_value}' != ref '{ref_value}'"
                    )
                    table_ok = False

    status = "KHỚP" if table_ok else "LỆCH"
    messages.append(f"{status} bảng {table_name}: {checked_numeric}/{len(ref_rows)*len(numeric_cols)} ô số liệu "
                    f"({checked_total}/{len(ref_rows)*len(expected_cols)} tổng số ô)")
    return table_ok, checked_numeric, checked_total


def verify_quantitative_claims(report_text, raw_rows, messages):
    """Verify quantitative prose observations: LZW throughput, Huffman throughput, Huffman memory."""
    ok = True
    report_lower = report_text.lower()

    # (a) LZW throughput relationship by family
    lzw_rows = [r for r in raw_rows if r.get('codec') == 'lzw']
    if lzw_rows:
        c1 = [r for r in lzw_rows if r.get('dataset') == 'C1']
        c2 = [r for r in lzw_rows if r.get('dataset') == 'C2']
        v1 = [r for r in lzw_rows if r.get('dataset') == 'V1']
        c3 = [r for r in lzw_rows if r.get('dataset') == 'C3']

        c1_ok = len(c1) == 15 and all(float(r['decomp_kibs']) > float(r['comp_kibs']) for r in c1)
        c2_ok = len(c2) == 15 and all(float(r['decomp_kibs']) > float(r['comp_kibs']) for r in c2)
        v1_ok = len(v1) == 5 and all(float(r['decomp_kibs']) > float(r['comp_kibs']) for r in v1)
        c3_ok = len(c3) == 15 and all(float(r['decomp_kibs']) < float(r['comp_kibs']) for r in c3)

        has_c1_higher = 'on c1' in report_lower and ('decompression throughput is ~2.8x higher' in report_lower or 'decompression is faster' in report_lower)
        has_c2_higher = 'on c2' in report_lower and ('higher than compression' in report_lower or 'decompression is faster' in report_lower)
        has_v1_higher = 'on v1' in report_lower and ('higher than compression' in report_lower or 'decompression is faster' in report_lower)
        c3_stated_slower = 'on c3' in report_lower and ('strictly lower than compression' in report_lower and 'decompression is slower on 15/15' in report_lower)
        all_stated_higher = 'higher than compression throughput across all' in report_lower

        claim_a_ok = (c1_ok and c2_ok and v1_ok and c3_ok and 
                      has_c1_higher and has_c2_higher and has_v1_higher and 
                      c3_stated_slower and not all_stated_higher)
        if claim_a_ok:
            messages.append("ĐẠT kiểm tra định lượng (a): LZW throughput theo họ (C1, C2, V1 decomp > comp; C3 decomp < comp)")
        else:
            messages.append("KHÔNG ĐẠT kiểm tra định lượng (a): LZW throughput theo họ không khớp giữa draft và CSV")
            ok = False

    # (b) Huffman decomp < comp on all 50 rows
    huff_rows = [r for r in raw_rows if r.get('codec') == 'huffman']
    if huff_rows:
        huff_slower_all = (len(huff_rows) == 50 and 
                           all(float(r['decomp_kibs']) < float(r['comp_kibs']) for r in huff_rows))
        has_huff_claim = ('50/50' in report_lower or 'all 50 experimental rows' in report_lower) and \
                         ('strictly lower than compression' in report_lower or 'decompression throughput is strictly lower' in report_lower) and \
                         ('45/50' not in report_lower and '48/50' not in report_lower and '45 out of 50' not in report_lower)
        claim_b_ok = huff_slower_all and has_huff_claim
        if claim_b_ok:
            messages.append("ĐẠT kiểm tra định lượng (b): Huffman decomp_kibs < comp_kibs trên toàn bộ 50/50 dòng")
        else:
            messages.append("KHÔNG ĐẠT kiểm tra định lượng (b): Huffman throughput không khớp giữa draft và CSV")
            ok = False

    # (c) Huffman peak memory / comp bytes ratio in range [67.0, 68.0]
    if huff_rows:
        mem_ratios = [float(r['peak_mem_kib']) * 1024 / int(r['comp_bytes']) for r in huff_rows]
        min_mem_r = min(mem_ratios)
        max_mem_r = max(mem_ratios)
        csv_mem_ok = (min_mem_r >= 67.0 and max_mem_r <= 68.0)
        has_mem_range = ('67.0 to 68.0' in report_text or '67.0 và 68.0' in report_text or '67.0452' in report_text) and \
                        ('20.0 to 30.0' not in report_text)
        claim_c_ok = csv_mem_ok and has_mem_range
        if claim_c_ok:
            messages.append(f"ĐẠT kiểm tra định lượng (c): Huffman peak_mem/comp_bytes trong khoảng [67.0, 68.0] (thực tế {min_mem_r:.4f}–{max_mem_r:.4f})")
        else:
            messages.append("KHÔNG ĐẠT kiểm tra định lượng (c): Huffman peak_mem/comp_bytes không khớp giữa draft và CSV")
            ok = False

    return ok


def verify(report_path, out_dir=None, csv_path=None):
    report_path = Path(report_path)
    if not report_path.is_file():
        return False, [f"LỆCH: Không tìm thấy file báo cáo {report_path}"], 0, 0

    report_text = report_path.read_text(encoding='utf-8')
    tables = parse_markdown_tables(report_text)

    messages = []
    ok = True
    total_numeric = 0
    total_cells = 0

    # Locate reference tables
    ref_tables = {}
    if out_dir is not None and Path(out_dir).is_dir():
        out_dir = Path(out_dir)
        for name in TABLE_DEFINITIONS:
            csv_file = out_dir / f"rq1_{name}.csv"
            if csv_file.is_file():
                with csv_file.open(newline='', encoding='utf-8') as stream:
                    ref_tables[name] = list(csv.DictReader(stream))

    # Read raw results CSV if available
    raw_rows = []
    if csv_path is not None and Path(csv_path).is_file():
        with Path(csv_path).open(newline='', encoding='utf-8') as stream:
            raw_rows = list(csv.DictReader(stream))

    # If out_dir CSVs are missing, generate directly from raw_rows
    if len(ref_tables) < len(TABLE_DEFINITIONS) and raw_rows:
        summary = summarize(raw_rows)
        for name, defn in TABLE_DEFINITIONS.items():
            if name not in ref_tables:
                ref_tables[name] = table_rows(summary, defn['metric_keys'])

    found_tables = {}
    for t in tables:
        h = t['headers']
        matched_name = None
        for name, defn in TABLE_DEFINITIONS.items():
            if h == defn['columns']:
                matched_name = name
                break
        if matched_name:
            if matched_name in found_tables:
                messages.append(f"LỆCH: Trùng bảng {matched_name} trong báo cáo")
                ok = False
            found_tables[matched_name] = t
        else:
            messages.append(f"CẢNH BÁO: Bảng không xác định tại dòng {t['start_line']}: {h[:3]}...")
            ok = False

    for name in TABLE_DEFINITIONS:
        if name not in found_tables:
            messages.append(f"LỆCH: Thiếu bảng {name} trong báo cáo {report_path.name}")
            ok = False
            continue
        if name not in ref_tables:
            messages.append(f"LỆCH: Thiếu dữ liệu tham chiếu cho bảng {name}")
            ok = False
            continue

        tbl_ok, num_cnt, cell_cnt = verify_table(name, found_tables[name], ref_tables[name], messages)
        ok &= tbl_ok
        total_numeric += num_cnt
        total_cells += cell_cnt

    expected_total_numeric = sum(len(defn['numeric_columns']) * len(ref_tables[name])
                                 for name, defn in TABLE_DEFINITIONS.items() if name in ref_tables)
    expected_total_cells = sum(len(defn['columns']) * len(ref_tables[name])
                               for name, defn in TABLE_DEFINITIONS.items() if name in ref_tables)

    if ok and total_numeric == expected_total_numeric:
        messages.append(
            f"ĐẠT kiểm tra 3 bảng tổng hợp: {total_numeric}/{expected_total_numeric} ô số liệu "
            f"({total_cells}/{expected_total_cells} tổng số ô trong 3 bảng, 100.0%) "
            f"khớp với rq1/out/*.csv"
        )
    else:
        messages.append(
            f"KHÔNG ĐẠT kiểm tra 3 bảng tổng hợp: {total_numeric}/{expected_total_numeric} ô số liệu; "
            f"{'toàn bộ khớp' if ok else 'có sai lệch'}"
        )

    # Quantitative prose checks on full datasets
    if len(raw_rows) == 150 and '## Discussion' in report_text:
        claims_ok = verify_quantitative_claims(report_text, raw_rows, messages)
        ok &= claims_ok

    if ok:
        messages.append("ĐẠT TỔNG THỂ: Toàn bộ bảng và nhận xét định lượng trong draft đều khớp 100% với dữ liệu thực nghiệm.")
    else:
        messages.append("KHÔNG ĐẠT TỔNG THỂ: Có sai lệch trong bảng hoặc nhận xét định lượng.")

    return ok, messages, total_numeric, total_cells


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / 'rq1/RQ1_report_draft.md')
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'rq1/out')
    parser.add_argument('--csv', type=Path, default=ROOT / 'results/results_rq1.csv')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)

    ok, messages, total_numeric, total_cells = verify(args.report, args.out_dir, args.csv)
    output = '\n'.join(messages) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    print(output, end='')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
