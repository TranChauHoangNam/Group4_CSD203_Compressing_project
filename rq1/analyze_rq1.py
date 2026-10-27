"""Median/min/max RQ1 tables and figures derived solely from the recorded CSV."""
import argparse
import csv
import io
import math
from pathlib import Path
from statistics import median
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('C1', 'C2', 'C3', 'V1')
CODECS = ('rle', 'huffman', 'lzw')
METRICS = ('ratio', 'comp_kibs', 'decomp_kibs', 'peak_mem_kib')
STYLES = {
    'rle': dict(color='#0072B2', marker='o', linestyle='-'),
    'huffman': dict(color='#E69F00', marker='s', linestyle='--'),
    'lzw': dict(color='#CC79A7', marker='^', linestyle='-.'),
}
SIZES = (256, 512, 1024, 2048, 4096)
TABLES = {'ratio': ('ratio',), 'throughput': ('comp_kibs', 'decomp_kibs'),
          'memory': ('peak_mem_kib',)}
CONDITIONS = (
    'Measurement conditions: all 150 source rows were collected in one run on the same '
    'Intel Core i7-13650HX, 24 GB RAM, Windows 11, Python 3.13.2 (owner-reported). '
    'The owner read the output file several times to check progress; light interference '
    'is possible but unquantified. Three retained rows have comp_ms and decomp_ms above '
    '1.3 times their three-seed group median: C1_4194304_s3.bin/huffman, '
    'C1_4194304_s3.bin/lzw, C2_1048576_s1.bin/rle. '
    'The center uses the seed median, reducing sensitivity to a single extreme value; '
    'the min-max band retains it. Different seeds have different inputs, so flags do not prove noise.'
)
CAPTION = (
    'Same-machine run: i7-13650HX, 24 GB RAM, Windows 11, Python 3.13.2. Median line; min-max band.\n'
    'Timing flags (>1.3x seed median), retained: C1_4194304_s3 / Huffman and LZW; C2_1048576_s1 / RLE.\n'
    'Reading progress may add interference. Seed inputs differ; flags do not establish noise. Median reduces sensitivity.'
)


def read_rows(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'dataset', 'size_kib', 'codec', 'seed', *METRICS}
        if not required <= set(reader.fieldnames or ()):
            raise ValueError('Missing analysis columns')
        return list(reader)


def summarize(rows):
    groups = {}
    for line, row in enumerate(rows, 2):
        group = (row['dataset'], int(row['size_kib']), row['codec'])
        if group[0] not in DATASETS or group[2] not in CODECS:
            raise ValueError(f'Unsupported group at CSV line {line}: {group}')
        for metric in METRICS:
            if not math.isfinite(float(row[metric])) or float(row[metric]) <= 0:
                raise ValueError(f'Invalid {metric} at CSV line {line}')
        groups.setdefault(group, []).append((line, row))
    if not groups:
        raise ValueError('Empty results CSV')
    result = []
    for (dataset, size, codec), items in sorted(groups.items(), key=lambda item:
            (DATASETS.index(item[0][0]), item[0][1], CODECS.index(item[0][2]))):
        entry = dict(dataset=dataset, size_kib=size, codec=codec, n_samples=len(items),
                     source_csv_lines=','.join(str(line) for line, _ in items))
        for metric in METRICS:
            values = [float(row[metric]) for _, row in items]
            entry.update({metric+'_median': median(values), metric+'_min': min(values),
                          metric+'_max': max(values)})
        result.append(entry)
    return result


def table_rows(summary, metrics):
    fields = ['dataset', 'size_kib', 'codec', 'n_samples', 'source_csv_lines']
    fields += [metric+'_'+stat for metric in metrics for stat in ('median', 'min', 'max')]
    return [{field: (format(row[field], '.12g') if isinstance(row[field], float) else row[field])
             for field in fields} for row in summary]


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def markdown(rows, source):
    fields = list(rows[0])
    return (f'# RQ1 {source} summary\n\n'+CONDITIONS+
            '\n\nSource: results/results_rq1.csv; source_csv_lines counts the header as line 1. '
            'Statistics are over seed rows at each (dataset, size_kib, codec); V1 has one row. '
            'Values use 12 significant digits. Ratio is dimensionless; throughput is KiB/s; peak memory is KiB.\n\n'+
            '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+
            ''.join('| '+' | '.join(str(row[field]) for field in fields)+' |\n' for row in rows))


def figures(summary, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    def draw(ax, dataset, metric, ylabel, log_y=False):
        for codec in CODECS:
            rows = [r for r in summary if r['dataset'] == dataset and r['codec'] == codec]
            if not rows:
                continue
            x = [r['size_kib'] for r in rows]
            style = STYLES[codec]
            ax.plot(x, [r[metric+'_median'] for r in rows], label=codec, **style)
            ax.fill_between(x, [r[metric+'_min'] for r in rows],
                            [r[metric+'_max'] for r in rows], color=style['color'], alpha=.16)
        ax.set_xscale('log', base=2)
        ax.set_xticks(SIZES, labels=[str(size) for size in SIZES])
        if log_y:
            ax.set_yscale('log')
        ax.set(title=dataset, xlabel='Input size (KiB)', ylabel=ylabel)
        ax.grid(alpha=.2)

    for name, metric, ylabel in [('ratio', 'ratio', 'Compressed / original bytes'),
                                  ('memory', 'peak_mem_kib', 'Peak compress+decompress memory (KiB)')]:
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))
        for ax, dataset in zip(axes.flat, DATASETS):
            draw(ax, dataset, metric, ylabel)
            if name == 'ratio':
                ax.axhline(1, color='black', linestyle=':', linewidth=1, label='ratio = 1')
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.suptitle('RQ1 compression ratio' if name == 'ratio' else 'RQ1 peak memory')
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .96), ncol=4)
        if name == 'memory':
            fig.text(.5, .015, CAPTION, ha='center', va='bottom', fontsize=8)
        fig.tight_layout(rect=(0, .09 if name == 'memory' else 0, 1, .91))
        fig.savefig(out/f'rq1_{name}.png', dpi=200)
        plt.close(fig)
    fig, axes = plt.subplots(4, 2, figsize=(13, 15))
    for pair, dataset in zip(axes, DATASETS):
        for ax, metric, direction in zip(pair, ('comp_kibs', 'decomp_kibs'), ('compress', 'decompress')):
            draw(ax, dataset, metric, 'Throughput (KiB/s, log scale)', log_y=True)
            ax.set_title(f'{dataset}: {direction}')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.suptitle('RQ1 throughput')
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .975), ncol=3)
    fig.text(.5, .012, CAPTION, ha='center', va='bottom', fontsize=8)
    fig.tight_layout(rect=(0, .065, 1, .95))
    fig.savefig(out/'rq1_throughput.png', dpi=200)
    plt.close(fig)


def generate(source, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize(read_rows(source))
    rendered = {}
    for name, metrics in TABLES.items():
        rows = table_rows(summary, metrics)
        rendered[name] = markdown(rows, name)
        (out/f'rq1_{name}.csv').write_text(csv_text(rows), encoding='utf-8')
        (out/f'rq1_{name}.md').write_text(rendered[name], encoding='utf-8')
    figures(summary, out)
    return rendered


def compare_outputs(expected, actual):
    for name in TABLES:
        csv_name = f'rq1_{name}.csv'
        with (expected/csv_name).open(encoding='utf-8', newline='') as stream:
            left = list(csv.reader(stream))
        with (actual/csv_name).open(encoding='utf-8', newline='') as stream:
            right = list(csv.reader(stream))
        if left != right:
            raise ValueError(f'Table differs from regenerated source: {csv_name}')
        md_name = f'rq1_{name}.md'
        if (expected/md_name).read_text(encoding='utf-8') != (actual/md_name).read_text(encoding='utf-8'):
            raise ValueError(f'Markdown differs: {md_name}')
        for directory in (expected, actual):
            path = directory/f'rq1_{name}.png'
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f'Missing or empty figure: {path}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT/'results/results_rq1.csv')
    parser.add_argument('--out-dir', type=Path, default=ROOT/'rq1/out')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory(prefix='rq1-analysis-check-') as temporary:
                regenerated = Path(temporary)
                generate(args.csv, regenerated)
                compare_outputs(args.out_dir, regenerated)
            print('PASS: 3 CSV/Markdown tables regenerate exactly; 3 PNG figures exist and are nonempty')
        else:
            rendered = generate(args.csv, args.out_dir)
            for table in rendered.values():
                print(table)
            print('Generated 3 CSV/Markdown tables and 3 PNG figures')
        return 0
    except (OSError, ValueError) as exc:
        print(f'FAIL: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
