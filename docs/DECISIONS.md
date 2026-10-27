# Project decisions

These decisions were approved by the project owner. They document the current implementation;
no codec, measurement script or recorded result is changed by this document.

## D-1. Fixed 12-bit BPE codes

**Decision:** Use fixed 12-bit token IDs for every BPE K, matching LZW's budget of 4096 symbols.
The BPE merge table stores two 12-bit IDs per entry. See [BPE design](../rq3/DESIGN.md) and `rq3/bpe.py`.

**Rationale:** Keep the token-code budget comparable with the 12-bit LZW implementation.
This controls code width, not every source of format or training overhead.

**Effect on results:** At requested K=256 and K=1024, variable-width codes for the same learned
vocabulary could use fewer bits than 12 (at most 9 and 11 bits respectively).
For identical merges/tokens, fixed width therefore costs at least as many payload bytes after rounding;
the merge table also retains its fixed three bytes per entry. This is a format consequence,
not a measured variable-width experiment. Published ratios include all container and table bytes.

## D-2. Pre-tokenization and weighted unique segments

**Decision:** Use the byte regex `re.findall(rb" ?[^\s]+|\s+", data)` in `rq3/bpe.py`.
It matches a non-whitespace run with an optional preceding literal ASCII space, or a whitespace run.
The bytes regex uses ASCII whitespace classes; it does not perform Unicode word segmentation,
normalization, or whitespace removal. Matches retain the original bytes in order.
Train on each unique raw segment weighted by its occurrence frequency. Count all adjacent
positions, including overlaps, inside segments only; replace left-to-right without overlap.
No merge crosses a segment boundary. Encoding caches each unique segment's token list within
one encode call and concatenates these lists in original segment order.

**Rationale:** see DESIGN.md. The design specifies this as mandatory D8 but does not provide
an independent rationale for choosing this segmentation rule.

**Effect on results:** With nonempty input, each segment produces at least one token, so
n_tokens is at least the number of segments. bytes_per_token is orig_bytes/n_tokens;
ratio_tokens_only is ceil(12*n_tokens/8)/orig_bytes, and ratio adds 22+3*m bytes before division.
Segmentation restricts available merges and can change the learned table and these metrics.
There is no controlled unsegmented baseline here, so no numerical effect or unconditional
ratio improvement/degradation is claimed. The cache avoids repeated encoding work; it does
not remove duplicate segment occurrences from the output. Empty-input ratios remain undefined.

## D-3. Experimental conventions and verified exceptions

**Decision:** Use seeds 1, 2 and 3 where seeded datasets or shuffles apply. Use three untraced
compression/decompression repetitions and report their separate median times. Measure peak
compress/decompress allocation with tracemalloc in a separate pass. Store container lengths
in big-endian order.

**Rationale:** Make input generation repeatable, reduce sensitivity to individual timing samples,
and avoid including tracing overhead in the reported untraced times. Specify byte order explicitly.

**Effect on results:** `gen_synthetic.py` and `run_rq1.py` default to seeds 1/2/3;
RQ1 defaults to repeats=3, and `tools/measure.py` uses time.perf_counter, statistics.median,
and a separate tracemalloc pass. `rq2/run_rq2.py` implements median timing and a separate
trace, but its default seed list is only [1]: explicitly pass `--seeds 1 2 3`.
RQ3 compression/decompression also uses median-of-three timing and a separate trace with
pretrained merges. Its approved training exceptions remain: naive training is one run;
inc/noheap training is median-of-three. Separate training-memory measurements are one
traced run on 128 KiB prefixes at K=256. Thus the three-repeat convention does not apply
to every training or feasibility measurement. `container.py` uses to_bytes/from_bytes
with "big"; BPE's additional integer fields are also big-endian. The Huffman header uses
its own big-endian original-length field. These checks document code behavior, not proof
that historical timings were collected under identical hardware/load conditions.

## D-4. Shared schema, Huffman shim and RQ1 provenance

**Decision:** `common/results_schema.py` accepts an empty dataset only for rq=edge.
The root `huffman.py` exposes compress/decompress from `rq2.huffman`.
Preserve `results/results_rq1.csv`; any same-machine rerun must use the new
`results/results_rq1_resample.csv` and be reviewed before replacement.

**Rationale:** Edge examples need not belong to a corpus; the shim supplies the codec API
expected by Pair 1's runner. Separate rerun output preserves the original experiment record.

**Effect on results:** The original CSV remains unchanged: its 50 Huffman rows were
measured on a different machine from the 100 RLE/LZW rows, according to the owner.
The owner has now completed all 150 rows in `results/results_rq1_resample.csv` on one
machine: Intel Core i7-13650HX, 24 GB RAM, Windows 11, Python 3.13.2 (owner-reported).
Owner-reported total wall time is 1160.0407191 seconds (19.334011985 minutes).
Validation found 150 rows, 50 per codec, the expected header, no duplicate (file, codec)
keys, all roundtrip_ok=true and all rows accepted by common.results_schema.validate_row.
The key sets match the original CSV exactly. All comp_bytes and output_check values
match for all 150 keys; no deterministic-output discrepancies were found.
Neither CSV has been edited or promoted to replace the other.

**Limitations:** The owner read the output file several times to check progress during
measurement; this may have introduced light interference, but no causal effect has been
quantified. One machine removes the known mixed-machine provenance problem but does not
eliminate load, thermal or execution-order effects. Existing per-row times are already
medians of three repetitions. The following screening rule compares different input
seeds, not repeated observations of identical input, and cannot establish noise by itself.

For each of the 45 (family, size, codec) groups in C1/C2/C3, compute the median of its
three seeds separately for comp_ms and decomp_ms. Flag a cell only if value/median > 1.3
(the slow side, not values below median/1.3). V1 has no three-seed groups and is excluded.
Six cells in three rows are flagged; all are retained:

| Resample CSV line | File | Codec | Metric | Value (ms) | Seed median (ms) | Value/median |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 45 | C1_4194304_s3.bin | huffman | comp_ms | 1278.5728 | 715.4919 | 1.786984 |
| 45 | C1_4194304_s3.bin | huffman | decomp_ms | 4673.7635 | 2261.5424 | 2.066627 |
| 46 | C1_4194304_s3.bin | lzw | comp_ms | 581.1987 | 326.5984 | 1.779552 |
| 46 | C1_4194304_s3.bin | lzw | decomp_ms | 197.8015 | 119.1211 | 1.660508 |
| 65 | C2_1048576_s1.bin | rle | comp_ms | 204.0305 | 123.9198 | 1.646472 |
| 65 | C2_1048576_s1.bin | rle | decomp_ms | 207.0010 | 146.9836 | 1.408327 |

Medians below aggregate the 50 recorded rows per codec, rounded to three decimals;
they describe this matrix of input sizes/families, not a size-controlled codec ranking.

| Codec | Old comp KiB/s | New comp KiB/s | Old decomp KiB/s | New decomp KiB/s | Old peak KiB | New peak KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rle | 8681.856 | 8605.784 | 6302.585 | 7111.767 | 4105.687 | 4224.402 |
| huffman | 2853.187 | 5745.700 | 836.696 | 1777.461 | 68671.167 | 68671.167 |
| lzw | 8766.420 | 10024.287 | 17871.674 | 19310.570 | 2705.525 | 2689.238 |

**Recommendation pending owner approval:** Prefer the complete same-machine resample as
the future primary RQ1 dataset, preserving the original as an archive and retaining all
flagged rows with the limitation above. No replacement is authorized by this document.
A second uninterrupted run would help assess reproducibility, especially on the flagged
inputs. Do not take a per-cell minimum across runs as the primary estimate: that selects
optimistically low times and can mix values from different runs into a row that was never
observed. Retain both complete runs and report their spread, or use a predeclared median
across independent runs (preferably three runs); keep compression/decompression and memory
scope explicit. A minimum can only be a separately labelled best-case statistic.

## Preparation and pilot evidence (not a full rerun)

All 45 regenerated synthetic files and five copied V1 prefixes matched manifest byte sizes
and full SHA-256 hashes. All 150 original CSV rows matched input orig_bytes and sha16.
The small pilot used C1_262144_s1.bin with LZW, repeats=3 and the separate memory pass,
writing only to a system-temp CSV. Wall time was 0.5524109999969369 seconds;
median comp_ms=20.340500, decomp_ms=8.041400, peak_mem_kib=783.612305.
The full matrix processes 243793914 input bytes across its rows. Scaling pilot wall time
by 243793914/262144 gives an ESTIMATE of 513.7422173534669 seconds (8.562370289224448 minutes).
This agent-environment/sandbox estimate assumes linear byte scaling and the same per-byte
cost across codecs and data; it includes scaled startup overhead and is not a bound or a
reliable prediction for Huffman, RLE, different corpora or interactive system load.
No full 150-row rerun was performed by the agent.

Observed platform: Windows-11-10.0.26300-SP0; Python 3.13.2;
processor string: Intel64 Family 6 Model 183 Stepping 1, GenuineIntel;
os.cpu_count()=20 logical processors. CPU marketing model and physical RAM are unconfirmed
(the CIM query was denied). Close heavy applications and run no concurrent workloads
when executing the full measurement manually.
