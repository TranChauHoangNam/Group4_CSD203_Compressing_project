"""Đối chiếu từng số trong bảng truy vết và văn xuôi với CSV/output cơ chế."""
import argparse
import csv
from pathlib import Path
import re
from statistics import mean

from rq2.analyze_rq2 import (RATIO_COLUMNS, SPEED_COLUMNS, COMPARISON_COLUMNS,
                             compare_codecs, summarize, table_markdown)


def section(report, name):
    return report.split(f'<!-- BEGIN:{name} -->\n', 1)[1].split(f'<!-- END:{name} -->', 1)[0].strip()


def verify(csv_path, report_path, mechanism_path):
    with csv_path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    report = report_path.read_text(encoding='utf-8')
    mechanism = mechanism_path.read_text(encoding='utf-8').splitlines()
    messages, ok = [], True
    entries = [line.strip('| ').split(' | ') for line in section(report, 'trace').splitlines()[2:]]
    seen = set()
    for ident, label, scope, source, operation, quoted in entries:
        try:
            if ident in seen:
                raise ValueError('ID trùng')
            seen.add(ident)
            if source.startswith('CSV:'):
                selected = [rows[int(n) - 2] for n in source[4:].split(',')]
                aggregate, metric = re.fullmatch(r'(mean|min|max)\(([^)]+)\)', operation).groups()
                values = []
                for row in selected:
                    if metric == 'ratio-h0_ratio':
                        value = float(row['ratio']) - float(row['h0_ratio'])
                    elif metric == 'ratio_no_header':
                        value = float(row['notes'].split('=')[1])
                    else:
                        value = float(row[metric])
                    values.append(value)
                    for actual, expected in zip((row['file'], row['codec'], row['state']), scope.split('/')):
                        if expected != '*' and actual != expected:
                            raise ValueError('Nguồn không khớp file/codec/state')
                calculated = {'mean': mean, 'min': min, 'max': max}[aggregate](values)
                expected = str(int(calculated)) if metric in ('comp_bytes', 'orig_bytes') else f'{calculated:.6g}'
            elif source.startswith('MECH:'):
                line = mechanism[int(source[5:]) - 1]
                begin, end = map(int, re.fullmatch(r'slice\((\d+),(\d+)\)', operation).groups())
                expected = line[begin:end]
            else:
                raise ValueError('Nguồn không được hỗ trợ')
            prose = report.split('## Truy vết số liệu')[0]
            values_in_prose = re.findall(r'\*\*([^*]+)\*\* \[' + re.escape(ident) + r'\]', prose)
            passed = quoted == expected and values_in_prose == [quoted]
            messages.append(f"{'KHỚP' if passed else 'LỆCH'} {ident}: {label}; {scope}; {quoted} / nguồn {expected} ({source}, {operation})")
            ok &= passed
        except (ValueError, IndexError, KeyError, AttributeError) as exc:
            ok = False
            messages.append(f'LỆCH {ident}: {exc}')
    referenced = set(re.findall(r'\[(T\d+)\]', report.split('## Truy vết số liệu')[0]))
    if referenced != seen:
        ok = False
        messages.append('LỆCH: mã truy vết thiếu hoặc thừa')
    ratio_rows, speed_rows = summarize(rows)
    for name, data, columns in [('ratio', ratio_rows, RATIO_COLUMNS), ('speed', speed_rows, SPEED_COLUMNS),
                                ('comparison', compare_codecs(ratio_rows), COMPARISON_COLUMNS)]:
        passed = section(report, name) == table_markdown(data, columns).strip()
        messages.append(f"{'KHỚP' if passed else 'LỆCH'} bảng {name}: sinh lại trực tiếp từ CSV")
        ok &= passed
    messages.append(f"{'KHỚP' if ok else 'LỆCH'} tổng: {len(entries)} dòng truy vết; 3 bảng định lượng")
    return ok, messages


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=Path('results_rq2_all.csv'))
    parser.add_argument('--report', type=Path, default=Path('rq2/RQ2_report_draft.md'))
    parser.add_argument('--mechanism-output', type=Path, default=Path('rq2/out/mechanism_output.txt'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    ok, messages = verify(args.csv, args.report, args.mechanism_output)
    output = '\n'.join(messages) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    print(output, end='')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
