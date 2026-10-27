# RQ3 - approved Phase 4 experiments

Implemented: naive, noheap and inc training over unique frequency-weighted
segments, cached linked-list/heap encoding per segment, decode, compress,
compress_with_merges and decompress. All three variants must pass the same
round-trip and merge/token equivalence tests; there are no pending BPE xfails.

Mandatory pre-tokenization: `re.findall(rb" ?[^\s]+|\s+", data)`.
Training and encoding never merge across segment boundaries. All overlapping
adjacent positions are counted inside a segment; replacement is left-to-right,
non-overlapping. Count ties use lexicographically smallest pair. Stop when the
highest weighted count is less than two. See DESIGN.md D1-D8.

## Fixed 12-bit format

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 4 | BPE1 |
| 4 | 8 | original length, big-endian |
| 12 | 2 | K field stores actual merge count m |
| 14 | 3*m | merge table: two 12-bit ids per entry, MSB-first |
| 14+3*m | 8 | token count, big-endian |
| 22+3*m | ceil(12*n_tokens/8) | 12-bit tokens, MSB-first, zero-padded |

Fixed overhead: 22 bytes. ratio includes all bytes; ratio_tokens_only includes
only payload bytes. bytes_per_token = orig_bytes/n_tokens. Undefined ratios
for empty data stay blank. D7 retains exactly the required merges/tokens and
now occupies 39 bytes: 14 + 9 + 8 + 8. Empty input occupies 22 bytes.
The previous variable-width experimental format is superseded.

## Tests and remaining work

From the repository root in PowerShell:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m pytest -q
```

encode_reference is a test-only per-segment sequential oracle. Tests also compare
weighted unique training to an independent per-occurrence recount. There is no
public raw-text training mode. API K accepts integers 0..3840 for small tests;
CSV limits remain 256/1024/3840, with 3 allowed only for rq=edge.
Phase 2 equivalence is covered by 200 random segmented inputs, edge cases and
64 KiB prefixes of V1/E1 train at K=256. The corpus tests require the verified
data files; they fail rather than silently skip when data are missing.
Phase 3 feasibility and Phase 4 measurements are stored separately in rq3/out.
Phase 4 follows the approved mixed full/prefix training plan below.

Future RQ3 CSV writers must use common.results_schema.append_row with rq=3,
codec=bpe and train_variant/k_merges/train_corpus/test_corpus/ratio/
ratio_tokens_only/n_tokens/bytes_per_token/train_ms plus shared measurement
and round-trip fields. Do not use tools.results_schema.CsvWriter (.6f);
the shared schema uses append_row (.6g). Pair 1 copies are unchanged.

Wikipedia data remain ignored in data/wiki and are checked against
SHA-256/sizes in docs/manifest.json. Recreate with tools/prepare_wiki.py
and its requirements-wiki.txt dependencies, then verify the manifest.


## Training variants

- naive: recount all pairs in all unique segments on every iteration.
- noheap: linked lists, pair-position and pair-to-segments indexes, weighted
  incremental edge updates; select a pair by scanning the count dictionary.
- inc: the same incremental state, but select using a lazy heap (-count, a, b).

All selections share the lexicographic tie-break rule. Both incremental variants
remove old adjacent edges before replacement and add new edges afterward,
including overlapping occurrences in their counts. See DESIGN.md for details.

Hardening tests cover K field >3840, self/future/out-of-range merge references,
payload length versus the 64-bit count, decoded length in both directions,
every truncated D7 prefix, invalid magic and nonzero padding.


## Approved Phase 4 plan and reproduction

Run from the repository root with PYTHONIOENCODING=utf-8:

```powershell
python -m rq3.phase4_preflight
python -m rq3.run_rq3 results
python -m rq3.run_rq3 edge
python -m rq3.run_rq3 train-memory
python -m rq3.check_results_rq3
python -m rq3.analyze_rq3
python -m rq3.analyze_rq3 --check
python -m pytest -q
```

Preflight measures E1 train prefixes 16/32/64/128 KiB, K=64/256, all variants,
one run per cell. Its naive full K=256 estimate uses E1's own measurements.
One-run preflight and training-memory stages refuse to overwrite existing output.
The results stage reuses audited trained models and skips already written keys;
it does not silently repeat completed measurements. To intentionally repeat the
experiment, first archive its CSV and matching audit together outside these paths.

The result matrix has 38 rows: 36 BPE (3 variants x 2 train x 2 test x 3 K)
and 2 LZW full-test baselines. inc/noheap use full train corpora, train_ms median
of 3 runs. naive uses full train only for K=256 (single run); K=1024/3840 use
128 KiB train prefixes (single run; notes include train_prefix_kib=128).
No full naive K=3840 is authorized or executed.

Compression/decompression always use the FULL test corpus, timed 3 times with
already-learned merges. peak_mem_kib is a separate tracemalloc pass over
compress+decompress on FULL test data, excluding training for ALL variants.
Its notes state mem_scope=compress_decompress_pretrained and mem_test_bytes.
Separate training-only memory is in out/train_mem.csv: V1/E1 x 3 variants,
SAME 128 KiB train prefixes, K=256, one traced run per cell. Do not compare this
column to peak_mem_kib as if they measured the same operation.

The audit preserves raw timing samples, actual m, training input hashes and merge
hashes. SHA-256 round-trip mismatch stops before writing a row. Edge appends 18
BPE rows, including D7 at K=3 for each variant, preserving the earlier CSV bytes.
The checker compares variants only when their training input hashes match:
all three at K=256, inc/noheap at K=1024/3840. Naive prefix rows are explicitly
separate provenance, not an exception to the algorithm's equivalence contract.

Tables carry source CSV line numbers. Figures label the naive scope change;
header-plus-table overhead includes the fixed 22 bytes. Report statements about
unverified causes use [GIAI THICH - can kiem chung].
