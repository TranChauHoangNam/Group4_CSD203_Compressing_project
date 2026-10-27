"""Traceable RQ3 tables, plots and draft; no inferred causes presented as facts."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from rq3.run_rq3 import parse_notes

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'rq3/out'
SOURCE=ROOT/'results/results_rq3.csv'


def read_csv(path):
    with path.open(newline='',encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def as_csv(rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return stream.getvalue()


def as_md(rows):
    fields=list(rows[0])
    return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r[f]) for f in fields)+' |\n' for r in rows)


def tables():
    records=read_csv(SOURCE)
    for line,r in enumerate(records,2): r['csv_line']=line
    bpes=[r for r in records if r['codec']=='bpe']
    ratio=[];tokens=[];overhead=[];training=[];gaps=[]
    seen=set()
    for r in bpes:
        notes=parse_notes(r['notes'])
        common=dict(csv_line=r['csv_line'],variant=r['train_variant'],train=r['train_corpus'],test=r['test_corpus'],K=r['k_merges'],train_prefix_kib=notes['train_prefix_kib'])
        ratio.append(dict(common,orig_bytes=r['orig_bytes'],comp_bytes=r['comp_bytes'],ratio=r['ratio'],ratio_tokens_only=r['ratio_tokens_only']))
        tokens.append(dict(common,n_tokens=r['n_tokens'],bytes_per_token=r['bytes_per_token']))
        orig=int(r['orig_bytes']);m=int(notes['m_actual'])
        overhead.append(dict(common,m=m,header_bytes=22,merge_table_bytes=3*m,
                             overhead_ratio=f"{(22+3*m)/orig:.9g}",merge_table_ratio=f"{3*m/orig:.9g}",
                             ratio_minus_tokens_only=f"{float(r['ratio'])-float(r['ratio_tokens_only']):.9g}"))
        ident=(r['train_variant'],r['train_corpus'],r['k_merges'])
        if ident not in seen:
            seen.add(ident)
            training.append(dict(csv_line=r['csv_line'],variant=r['train_variant'],train=r['train_corpus'],K=r['k_merges'],
                                 train_prefix_kib=notes['train_prefix_kib'],train_bytes=notes['train_bytes'],m=m,
                                 train_runs=notes['train_runs'],train_ms=r['train_ms']))
        if r['train_corpus']!=r['test_corpus']:
            same=next(q for q in bpes if q['train_variant']==r['train_variant'] and q['k_merges']==r['k_merges'] and q['train_corpus']==q['test_corpus']==r['test_corpus'])
            delta=int(r['comp_bytes'])/int(r['orig_bytes'])-int(same['comp_bytes'])/int(same['orig_bytes'])
            gaps.append(dict(cross_csv_line=r['csv_line'],same_csv_line=same['csv_line'],variant=r['train_variant'],
                             train=r['train_corpus'],test=r['test_corpus'],K=r['k_merges'],train_prefix_kib=notes['train_prefix_kib'],
                             cross_ratio=r['ratio'],same_test_corpus_ratio=same['ratio'],delta_ratio=f"{delta:.9g}"))
    baselines=[dict(csv_line=r['csv_line'],test=r['test_corpus'],orig_bytes=r['orig_bytes'],comp_bytes=r['comp_bytes'],ratio=r['ratio'],comp_ms=r['comp_ms'],decomp_ms=r['decomp_ms'],peak_mem_kib=r['peak_mem_kib']) for r in records if r['codec']=='lzw']
    memory=read_csv(OUT/'train_mem.csv')
    mem_table=[dict(train_mem_csv_line=i,**r) for i,r in enumerate(memory,2)]
    return dict(ratio=ratio,tokens=tokens,overhead=overhead,cross_gap=gaps,training=training,lzw=baselines,training_memory=mem_table)


def extended_sections():
    """Generate comparisons from CSV rows; explicitly cite raw-text/Phase 3 inputs."""
    rows = read_csv(SOURCE)
    for line, row in enumerate(rows, 2):
        row['csv_line'] = line

    def bpe(variant, train, test, k):
        return next(r for r in rows if r['codec'] == 'bpe'
                    and (r['train_variant'], r['train_corpus'], r['test_corpus'], int(r['k_merges']))
                    == (variant, train, test, k))

    def baseline(test):
        return next(r for r in rows if r['codec'] == 'lzw' and r['test_corpus'] == test)

    def fmt(value):
        return f'{value:.9g}'

    text = '\n## inc ratio matrices (full training)\n\n'
    for k in (256, 1024, 3840):
        matrix = []
        for train in ('V1', 'E1'):
            entry = {'train / test': train}
            for test in ('V1', 'E1'):
                r = bpe('inc', train, test, k)
                entry[test] = f"{r['ratio']} (CSV line {r['csv_line']})"
            matrix.append(entry)
        text += f'\n### K={k}\n\n' + as_md(matrix)

    speeds = []
    for train in ('V1', 'E1'):
        for k in (256, 1024, 3840):
            inc = bpe('inc', train, train, k)
            entry = dict(train=train, K=k, inc_csv_line=inc['csv_line'], inc_train_ms=inc['train_ms'])
            ni = parse_notes(inc['notes'])
            for variant in ('naive', 'noheap'):
                r = bpe(variant, train, train, k)
                nr = parse_notes(r['notes'])
                comparable = (ni['train_prefix_kib'] == nr['train_prefix_kib'] == '0'
                              and ni['train_sha256'] == nr['train_sha256']
                              and ni['train_bytes'] == nr['train_bytes'])
                entry[variant + '_csv_line'] = r['csv_line']
                entry[variant + '/inc'] = (fmt(float(r['train_ms']) / float(inc['train_ms']))
                                          if comparable else 'not comparable (prefix vs full)')
            speeds.append(entry)
    text += '\n## Training-speed ratios\n\nRatios above one mean inc was faster. Only identical full training inputs are compared. naive uses one run; inc/noheap use medians of three. Duplicate test rows reuse a training measurement and are not additional repetitions.\n\n' + as_md(speeds)

    inflation = []
    counts = []
    for test, other in (('V1', 'E1'), ('E1', 'V1')):
        first = bpe('inc', test, test, 256)
        path = ROOT / 'data/wiki' / first['file']
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest[:16] == first['output_check'], f'Test file does not match CSV: {path}'
        assert len(raw) == int(first['orig_bytes'])
        decoded = raw.decode('utf-8', errors='replace')
        chars, words = len(decoded), len(decoded.split())
        counts.append(dict(test=test, csv_line=first['csv_line'], file=path.relative_to(ROOT).as_posix(),
                           sha256=digest, characters=chars, whitespace_words=words))
        for k in (256, 1024, 3840):
            same, cross = bpe('inc', test, test, k), bpe('inc', other, test, k)
            ns, nc = int(same['n_tokens']), int(cross['n_tokens'])
            inflation.append(dict(test=test, K=k, same_csv_line=same['csv_line'], other_csv_line=cross['csv_line'],
                                  same_n_tokens=ns, other_n_tokens=nc, other_over_same=fmt(nc/ns),
                                  same_tokens_per_character=fmt(ns/chars), other_tokens_per_character=fmt(nc/chars),
                                  same_tokens_per_word=fmt(ns/words), other_tokens_per_word=fmt(nc/words)))
    text += '\n## Token inflation (inc, full training)\n\nCharacter counts are Unicode code points, including whitespace, after UTF-8 decoding with errors replaced; words are decoded_text.split() whitespace-separated units, not linguistic words. Counts come from the raw files below, linked to the CSV output_check and orig_bytes; token numerators come from the cited CSV lines. Corpora are non-parallel; these comparisons are correlational, not controlled language effects.\n\n' + as_md(counts) + '\n' + as_md(inflation)

    comparison, performance = [], []
    for test in ('V1', 'E1'):
        lzw = baseline(test)
        lr = int(lzw['comp_bytes']) / int(lzw['orig_bytes'])
        for k in (256, 1024, 3840):
            same = bpe('inc', test, test, k)
            br = int(same['comp_bytes']) / int(same['orig_bytes'])
            comparison.append(dict(test=test, K=k, bpe_csv_line=same['csv_line'], lzw_csv_line=lzw['csv_line'],
                                   bpe_ratio=fmt(br), lzw_ratio=fmt(lr), relative_difference_pct=fmt(100*(br/lr-1))))
            for train in ('V1', 'E1'):
                r = bpe('inc', train, test, k)
                notes = parse_notes(r['notes'])
                entry = dict(train=train, test=test, K=k, bpe_csv_line=r['csv_line'], lzw_csv_line=lzw['csv_line'],
                             overhead_ratio=fmt((int(r['comp_bytes'])-int(notes['payload_bytes']))/int(r['orig_bytes'])))
                for metric in ('comp_ms', 'decomp_ms', 'peak_mem_kib'):
                    entry['bpe_'+metric] = r[metric]
                    entry['lzw_'+metric] = lzw[metric]
                performance.append(entry)
    text += '\n## Same-language BPE versus LZW\n\nBPE is inc with full same-language training. Ratios are recomputed from integer byte counts. Relative difference = 100 * (BPE ratio / LZW ratio - 1); negative means smaller BPE output.\n\n' + as_md(comparison)
    text += '\n## inc compression/decompression and memory versus LZW\n\nAll inc train/test combinations are shown. LZW has no training corpus or K; its same-test baseline is repeated for comparison. Times exclude training. Peak memory covers compress+decompress using learned merges on the full test file. overhead_ratio = (comp_bytes - payload_bytes) / orig_bytes = (22 + 3*m) / orig_bytes, not a subtraction of rounded ratios.\n\n' + as_md(performance)

    phase_path = OUT / 'phase3_measurements.json'
    cells = json.loads(phase_path.read_text(encoding='utf-8'))['cells']
    scaling = []
    for variant in ('naive', 'noheap', 'inc'):
        for size in (16, 32, 64, 128):
            selected = []
            for k in (64, 256):
                index, cell = next((i, c) for i, c in enumerate(cells) if c['scope'] == 'prefix'
                                   and c['corpus'] == 'V1' and c['variant'] == variant
                                   and c['raw_bytes'] == size*1024 and c['k'] == k)
                selected.append((index, cell))
            (i, low), (j, high) = selected
            scaling.append(dict(variant=variant, prefix_kib=size, source_cells=f'cells[{i}], cells[{j}]',
                                unique_bytes=low['unique_bytes'], m_K64=low['m'], m_K256=high['m'],
                                ms_K64=fmt(low['train_ms']), ms_K256=fmt(high['train_ms']),
                                time_256_over_64=fmt(high['train_ms']/low['train_ms'])))
    text += '\n## Discussion skeleton\n\n### Heap speedup\n\nUse the full-scope training-speed ratios above as observed associations. [GIAI THICH - can kiem chung] Heap selection may reduce scanning costs; separate profiling is needed to isolate selection from index updates and allocation costs.\n\n### K-scaling in Phase 3\n\nThe following are single-run V1 prefix measurements from rq3/out/phase3_measurements.json, with zero-based JSON cell indices (not results_rq3.csv, which does not contain these prefix experiments). Increasing requested K from 64 to 256 multiplies K by four; actual learned m is shown. These are fixed-prefix comparisons, not full-corpus extrapolations.\n\n' + as_md(scaling)
    text += '\n[GIAI THICH - can kiem chung] A roughly linear dependence on K is a working expectation for naive full recount over unique weighted segments, not a fitted law: sequence shrinkage and timing noise can change the observed factor. [GIAI THICH - can kiem chung] noheap scaling may reflect scanning the changing pair table as well as incremental updates. [GIAI THICH - can kiem chung] inc scaling may reflect heap maintenance, lazy invalidation and affected-segment updates rather than K alone. These mechanisms need profiling and repeated measurements.\n\n### Cross-language gap\n\nRead the ratio matrices together with same-test token-inflation ratios. The corpora are non-parallel, so topic, text composition and language are confounded. [GIAI THICH - can kiem chung] Differences in segment and pair frequencies may contribute to the gap; controlled parallel corpora and frequency analysis are needed before attributing it to language.\n'
    return text


def draft(t):
    text="""# RQ3 report draft - approved mixed training scopes

## Method

Byte-level BPE follows D1-D8: regex pre-tokenization, weighted unique segments,
overlapping pair counts and left-to-right replacement, deterministic tie-break,
and fixed 12-bit codes. Compressed size includes the 22-byte fixed overhead,
3 bytes per actual merge, and the zero-padded token payload.

inc/noheap train on the full V1/E1 corpora at K=256/1024/3840; train_ms is the
median of 3 runs. naive uses full training data only at K=256 and 128 KiB prefixes
at K=1024/3840; train_ms is a single run, explicitly labelled in notes.
All variants compress/decompress FULL test files. Times are medians of 3 untraced
runs using time.perf_counter. Training is timed separately and reused for both
test corpora. Every restored result is checked against full SHA-256 before CSV.

peak_mem_kib is a separate tracemalloc pass over compress+decompress with the
already-learned table, on FULL test data for every variant. It excludes training
and allocations made before tracing. Separate training-memory measurements use
the SAME 128 KiB prefix, K=256, one traced run per corpus/variant (train_mem.csv).
Traced elapsed times are not timing benchmarks and are not substituted for train_ms.

## Comparability and limitations

At K=256 all three variants use identical training input and must give identical
merges, n_tokens and comp_bytes. At higher K only inc/noheap use identical input;
naive prefix-trained results must not be interpreted as a pure algorithm effect.
The naive curve changes training scope at K=1024. Plots label this explicitly.
Timing and memory are machine/load dependent; the single naive run has no
repeatability estimate. No full naive K=3840 was run.

Every table row identifies its source line in results/results_rq3.csv (header is
line 1). The training-memory table instead identifies train_mem.csv lines.
Overhead is 22+3*m bytes; ratio-ratio_tokens_only includes the fixed header,
so it is not solely the merge-table cost. Cross-corpus gaps compare against
same-language training on the SAME test corpus, variant and K.

## Measured observations

"""
    for a in ('V1','E1'):
        for b in ('V1','E1'):
            rows=[r for r in t['ratio'] if r['variant']=='inc' and r['train']==a and r['test']==b]
            rows.sort(key=lambda r:int(r['K']))
            first,last=rows[0],rows[-1]
            text+=f"- inc {a}->{b}: ratio {first['ratio']} at K={first['K']} to {last['ratio']} at K={last['K']} (CSV lines {first['csv_line']}, {last['csv_line']}).\n"
    for row in t['training']:
        if int(row['m']) < int(row['K']):
            text+=f"- Early stop: {row['variant']} {row['train']} train_prefix_kib={row['train_prefix_kib']}, requested K={row['K']}, actual m={row['m']} (CSV line {row['csv_line']}).\n"
    text+='\n[GIAI THICH - can kiem chung] A mismatch between training and test segment frequencies may contribute to cross-corpus gaps; the measurements do not isolate this cause.\n'
    text+='[GIAI THICH - can kiem chung] Heap-based pair selection may reduce training time relative to scanning, but this experiment does not separately profile selection and index-update costs.\n'
    for title,name in [('Compression ratios','ratio'),('Tokens and bytes per token','tokens'),('Header and merge-table overhead','overhead'),('Cross-corpus gap','cross_gap'),('Training time and scope','training'),('LZW baselines','lzw'),('Separate training-memory: 128 KiB, K=256','training_memory')]:
        text+='\n## '+title+'\n\n'+as_md([{key: value for key, value in row.items() if key != 'ratio_minus_tokens_only'} for row in t[name]])
    text += extended_sections()
    text+='\n## Figures\n\n'
    for name in ('rq3_ratio','rq3_bytes_per_token','rq3_overhead','rq3_cross_gap','rq3_train_ms','rq3_training_memory'):
        text+=f"![{name}](out/{name}.png)\n\n"
    return text


def plots(t):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    styles={'inc':('o','-'),'noheap':('s','--'),'naive':('^',':')}
    for name,source,metric,label in [('rq3_ratio','ratio','ratio','Compressed / original bytes'),('rq3_bytes_per_token','tokens','bytes_per_token','Original bytes / token'),('rq3_overhead','overhead','overhead_ratio','(22 + 3*m) / original bytes')]:
        fig,axes=plt.subplots(2,2,figsize=(11,8))
        for ax,(a,b) in zip(axes.flat,[(a,b) for a in ('V1','E1') for b in ('V1','E1')]):
            for variant,(marker,line) in styles.items():
                rows=sorted([r for r in t[source] if r['variant']==variant and r['train']==a and r['test']==b],key=lambda r:int(r['K']))
                ax.plot([int(r['K']) for r in rows],[float(r[metric]) for r in rows],marker=marker,linestyle=line,label=variant+(' (128 KiB train for K>256)' if variant=='naive' else ' (full train)'))
            if name=='rq3_ratio':
                baseline=next(r for r in t['lzw'] if r['test']==b)
                ax.axhline(float(baseline['ratio']),color='black',linestyle='-.',label='LZW full test')
            ax.set(title=f'{a} train -> {b} test',xlabel='Requested K',ylabel=label,xticks=[256,1024,3840]);ax.grid(alpha=.25);ax.legend(fontsize=7)
        fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,b in zip(axes,('V1','E1')):
        for variant,(marker,line) in styles.items():
            rows=sorted([r for r in t['cross_gap'] if r['test']==b and r['variant']==variant],key=lambda r:int(r['K']))
            ax.plot([int(r['K']) for r in rows],[float(r['delta_ratio']) for r in rows],marker=marker,linestyle=line,label=variant+(' (prefix for K>256)' if variant=='naive' else ''))
        ax.axhline(0,color='black',linewidth=.7);ax.set(title=f'Test {b}: cross minus same corpus',xlabel='K',ylabel='Ratio difference');ax.legend(fontsize=8);ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(OUT/'rq3_cross_gap.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,a in zip(axes,('V1','E1')):
        for variant,(marker,line) in styles.items():
            rows=sorted([r for r in t['training'] if r['train']==a and r['variant']==variant],key=lambda r:int(r['K']))
            ax.plot([int(r['K']) for r in rows],[float(r['train_ms']) for r in rows],marker=marker,linestyle=line,label=variant+(' single; prefix K>256' if variant=='naive' else ' median3; full'))
        ax.set(title=f'Train {a}',xlabel='K',ylabel='train_ms (log scale)',yscale='log');ax.legend(fontsize=8);ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(OUT/'rq3_train_ms.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    rows=t['training_memory'];ax.bar([r['corpus']+'/'+r['variant'] for r in rows],[float(r['peak_train_mem_kib']) for r in rows])
    ax.set(title='Training only: same 128 KiB prefix, K=256, one traced run',ylabel='Peak KiB');fig.tight_layout();fig.savefig(OUT/'rq3_training_memory.png',dpi=160);plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('--report-only',action='store_true', help='Generate/check only the report; preserve CSVs and figures');args=ap.parse_args()
    t=tables();artifacts={}
    for name,rows in t.items():
        artifacts[OUT/f'rq3_{name}.csv']=as_csv(rows)
        artifacts[OUT/f'rq3_{name}.md']=as_md(rows)
    artifacts[ROOT/'rq3/RQ3_report_draft.md']=draft(t)
    if args.report_only:
        artifacts = {ROOT/'rq3/RQ3_report_draft.md': artifacts[ROOT/'rq3/RQ3_report_draft.md']}
    if args.check:
        for path,expected in artifacts.items():
            assert path.read_text(encoding='utf-8')==expected,f'Traceability mismatch: {path}'
        print(f'PASS: {len(artifacts)} artifacts regenerate exactly from cited sources')
    else:
        for path,text in artifacts.items():path.write_text(text,encoding='utf-8')
        if not args.report_only:
            plots(t)
        print('Generated report only; CSVs and figures unchanged' if args.report_only else f'Generated {len(t)} tables (CSV+MD), 6 PNG figures and report')


if __name__=='__main__': main()
