# CSD203 Topic 4 - Lossless Compression and BPE

A study of lossless compression with RLE, canonical Huffman coding and LZW, alongside a byte-level BPE tokenizer.
Class: **AI21B, FA26**. Team: **six members working in three pairs**.
RQ1 compares compression on synthetic and Vietnamese text data; RQ2 studies sensitivity to byte order.
RQ3 compares BPE training variants and same-language versus cross-language compression.

## Repository layout

```text
common/           Shared CSV schema and validation tests
rq1/              RQ1 seed summaries, analysis tests and figures
rq2/              Huffman, entropy, byte reordering, RQ2 runner, tests and report
rq3/              BPE variants, RQ3 runner, tests, analysis and report
tools/           Pair 1 measurement, edge-case and Wikipedia preparation tools
docs/            Data manifests and Pair 1/2 handoff notes
results/         RQ1, RQ3 and shared edge-case CSVs
rle.py           RLE codec
lzw.py           LZW codec
huffman.py       Shim exposing rq2.huffman.compress/decompress
container.py     Shared binary header and hash helpers
run_rq1.py       RQ1 experiment runner
gen_synthetic.py Seeded C1/C2/C3 data generator
```

RQ2 results are in `results_rq2_all.csv` at the root. Component documentation:
[Pair 2 README](rq2/README.md) and [Pair 3 README](rq3/README.md).

## Environment and installation

Verified environment: Python **3.13.2**, pytest **9.1.1**, matplotlib **3.11.1**.
The codecs use the standard library. pytest runs the tests; matplotlib renders plots.
Pure Python: thuật toán không dùng sorted/.sort; thư viện chỉ dùng làm Oracle trong tests
The optional `datasets` package is needed for Wikipedia downloads and is **not installed in the audited environment**.

Installation commands below are **not verified in this documentation update**; no packages were installed or upgraded:

```powershell
python -m pip install pytest matplotlib python-docx
python -m pip install -r tools/requirements-wiki.txt
```

Run commands from the repository root. This PowerShell setup was executed successfully:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$($PWD.Path);$($PWD.Path)\tools"
python --version
```

The PYTHONPATH setting is needed by Pair 1 scripts: `run_rq1.py` imports `measure`
from `tools/`, while the tools import root-level codecs and `container`.

## Data: obtain locally, never commit

`data/` is gitignored and **not distributed in Git**, even if a working copy already has local data.
In particular, `kennedy.xls`, corpus text files and downloaded archives are not repository deliverables.

- Obtain `alice29.txt` and `kennedy.xls` from the Canterbury Corpus collection and extract them to `data/`.
  Acquisition/download was not re-tested here. The local inputs were checked against recorded RQ2 sizes and original-state hashes.
- Generate C1 (long runs), C2 (Zipf word distribution), and C3 (uniform random bytes) with `gen_synthetic.py`.
  Defaults: five sizes (256/512/1024/2048/4096 KiB), three seeds (1/2/3), 45 files in `data/synthetic/`.
  Compare with [synthetic manifest](docs/synthetic_manifest.json); do not assume an existing file is regenerated (the generator skips existing paths).
- Prepare V1 (Vietnamese) and E1 (English) with `tools/prepare_wiki.py`: Wikipedia `20231101`, NFC normalization,
  UTF-8, cuts at character boundaries. Output is `data/wiki/`, including four train/test files, V1 size prefixes and a local manifest.
  Download regeneration is not verified here and requires `datasets`; the script also accepts local `--vi-file` and `--en-file` inputs.
  Arbitrary local texts will not reproduce the recorded manifest.
- RQ2 also requires a byte-identical copy of `data/wiki/v1_test_1mib.txt` at `data/v1_test_1mib.txt`.
  RQ3 reads its four corpus files from `data/wiki/`; corpus equivalence tests skip when their inputs are absent.

Corpus-dependent pytest cases skip missing inputs; when inputs exist, size and SHA-256 assertions still run.
The RQ2/RQ3 check scripts print `Missing data file` / `CHƯA KIỂM` and exit 2 when data are unavailable; actual check failures exit 1.
Restore the inputs above for complete validation (exit 0); other checks continue where supported.

[docs/manifest.json](docs/manifest.json) contains expected byte sizes and full SHA-256 hashes for **wiki files only**.
The two Canterbury files are not entries in that manifest. Reference values checked locally:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| alice29.txt | 152089 | 7467306ee0feed4971260f3c87421154a05be571d944e9cb021a5713700c38f0 |
| kennedy.xls | 1029744 | 9af47239ca29dfe20e633f80bbbb9a4cc9783d0803d7b2b5626f42e4c3790420 |

Wiki expectations from the manifest:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| v1_train_1mib.txt | 1048575 | 61633cf2b34d99e4e1893dd84d36d3666feb23aeb618c9b7e2bedf5e3db641a3 |
| v1_test_1mib.txt | 1048576 | 36eacd547e1b271dd7c297e4a800284bb494c371148202f16cf4cbac2388a708 |
| e1_train_1mib.txt | 1048576 | bb8b4684207f9f2fba2f971d8597f3ed061b69872ec0711e6b0188f82bbae93a |
| e1_test_1mib.txt | 1048576 | 091eefa9d1603a2148a6a2c5813e822d499c95a5eaac09ed9e95c44ee0638031 |


Verified CLI discovery commands (help only; these do not generate/download data):

```powershell
python gen_synthetic.py --help
python tools/prepare_wiki.py --help
```

Generation commands: **not verified in this documentation update**:

```powershell
python gen_synthetic.py --out-dir data/synthetic
python tools/prepare_wiki.py --data-dir data/wiki
```

## Running the experiments

The following help commands were executed successfully with the environment above:

```powershell
python run_rq1.py --help
python -m rq2.run_rq2 --help
python -m rq3.run_rq3 --help
python tools/run_edge.py --help
```

Full experiment commands below are **not verified in this documentation update**. Their options were checked against the CLI/code;
existing results were validated instead of rerun. Archive existing outputs before intentionally collecting new measurements.

### RQ1: compression comparison

```powershell
python run_rq1.py --data-dir data --out results/results_rq1.csv --codecs rle huffman lzw --repeats 3
```

Uses C1/C2/C3 and V1 size prefixes; the recorded matrix has 150 rows (50 per codec).
The runner resumes by skipping existing `(file, codec)` keys; it does not remeasure these rows.

### RQ1 analysis

Run the analysis and report verification from the repository root; they read the recorded CSV without modifying it:

```powershell
python -m rq1.analyze_rq1
python -m rq1.analyze_rq1 --check
python -m rq1.verify_rq1_report
```

Outputs in `rq1/out/`: `rq1_ratio.csv`/`.md`, `rq1_throughput.csv`/`.md`,
`rq1_memory.csv`/`.md`, and `rq1_ratio.png`, `rq1_throughput.png`, `rq1_memory.png`.
Tables report seed medians/minima/maxima with source CSV line numbers; V1 has one sample.
All figures use consistent codec colors, markers and line styles. Shading retains the min-max range,
including the three timing-flagged rows. `--check` regenerates into system temp, compares table
content and checks that the three PNGs are present and nonempty.
`python -m rq1.verify_rq1_report` verifies that 100% of the numeric table cells in `rq1/RQ1_report_draft.md`
match `rq1/out/*.csv` and `results/results_rq1.csv`.

### RQ2: byte-order sensitivity

```powershell
python -m rq2.run_rq2 --data-dir data --seeds 1 2 3 --repeats 3 --out results_rq2_all.csv
```

Writes 45 rows for three input files and three codecs: original, sorted runs, and three shuffled seeds.
It refuses an existing output unless explicitly given `--overwrite`; that flag is deliberately omitted above.
The archived successful run in `rq2/run_logs/official.json` took **255.2758126999979 seconds**;
this is a historical measurement, not a runtime guarantee for another machine.

### RQ3: BPE and LZW baselines

```powershell
python -m rq3.run_rq3 results
python -m rq3.run_rq3 train-memory
```

Outputs: `results/results_rq3.csv`, `rq3/out/rq3_run_audit.json`, and `rq3/out/train_mem.csv`.
The results stage resumes audited models and existing rows; training-memory refuses to overwrite an existing output.
The 38-row matrix contains 36 BPE rows and two LZW baselines.
All three variants use full V1/E1 train files at K=256/1024/3840.
inc/noheap report median-of-three training times; naive reports one measured run.
Four high-K naive timings were imported from the verified full-corpus supplement;
the eight associated test rows were measured again. Source hashes and merge lists
are validated before reuse. The prior mixed-scope CSV/audit/edge records are kept
in `results/archive/mixed_scope/` as historical evidence, not primary results.
All test inputs are full files. Compression/decompression times are medians of three.
Memory is measured separately; training-memory uses 128 KiB, K=256, and is labelled.
For a historical checkout, `python -m rq3.upgrade_full` validates and imports the
supplement once; `python -m rq3.run_rq3 results` then completes the eight missing rows.
The normal runner always trains on full inputs and refuses stale prefix models.

### Edge cases

```powershell
python tools/run_edge.py --out results/results_edge.csv --codecs rle huffman lzw
python -m rq3.run_rq3 edge
```

The shared CSV has 15 Pair 1 rows and 18 BPE rows, including the hand-worked K=3 example.
Treat these as generation commands, not read-only checks; do not rerun against published results just to inspect them.

## Tests and read-only validation

The standard test entry point is `python -m pytest -q`. The verified audit invocation additionally disabled cache
and selected an external temporary directory; bytecode was disabled with the environment above:

```powershell
python -m pytest -q -p no:cacheprovider --basetemp <new-directory-in-system-temp>
```

Replace the placeholder with a fresh path outside the repository. The updated suite and independent checks are recorded in [validation_report.md](final_submission/validation_report.md). Historical test counts are not the current acceptance result.
The repository's pytest configuration also disables the cache provider. Do not reuse a valuable directory as pytest's base temp.

These exact check commands were executed:

```powershell
python -m rq2.check_results
python -m rq2.check_mechanism
python -m rq2.verify_report
python -m rq3.check_results_rq3
python tools/check_edge_compat.py
python -m rq3.analyze_rq3 --check
```

Observed status: RQ2 checks passed 9/9; mechanism inspection processed all three inputs;
report verification matched 119 trace rows and three tables; edge schema validation passed 33/33;
RQ3 analysis reproduced 15 artifacts exactly. With all required data present, RQ3 result checking
includes seven checks, including preservation of the original edge CSV bytes. Missing corpus data
are reported as unchecked with exit 2; validation criteria and the recorded CSVs are unchanged.

## Binary containers and CSV

The shared container prefix is a four-byte codec magic plus an eight-byte big-endian original length.
RLE uses `RLE1`, canonical Huffman `HUF1`, LZW `LZW1`, and BPE `BPE1`; payload formats are codec-specific.
BPE adds the actual merge count (two bytes), a three-byte entry per merge, an eight-byte token count,
and fixed 12-bit codes packed MSB-first with zero padding. Its total size includes the header and merge table.
CSV uses the shared 29-column layout (`status` follows `notes`), original/restored SHA-256 checks, and explicit training scope in notes.
See [CSV schema](common/csv_schema.md) and [BPE design D1-D8](rq3/DESIGN.md).
Pair 1's `tools/results_schema.py` uses CsvWriter and six decimal places; the shared writer uses append_row
and six significant digits. Keep this distinction when comparing rounded values.

Status is required: `ok`, `timeout`, `crash`, `oom`, or `wrong`. Only `ok` rows enter
numeric summaries; excluded rows produce a warning. Fixed-matrix reports require all rows to be `ok`.
Failure rows require a reason in `notes` and blank timing/throughput fields.
The runners currently emit `ok` after successful validation; automatic failure capture and a
60-second subprocess timeout are separate work, not implemented by this schema migration.
Historical `ok` means the recorded run completed and passed round-trip checks; it does not
retroactively certify a timeout protocol. No historical metric was recomputed.

Migrate the four active raw CSVs with `python -m tools.migrate_add_status --backup-dir <outside-repo-directory>`.
The command backs up changed sources before writing, preserves all 28 existing cell strings,
and is byte-idempotent on a second run. Archives remain unchanged in the legacy schema;
derived tables and the separate training-memory CSV keep their own schemas.
The edge audit retains its historical hash: verification projects out `status`, serializes
the original 15 rows plus the legacy header as UTF-8/LF, and compares against the original
2,482-byte evidence. The audit records this projection explicitly.

## Selected recorded results

Ratios below are compressed bytes / original bytes, including format overhead; smaller is better.
All BPE entries use inc with full same-language training. Source: [results_rq3.csv](results/results_rq3.csv),
where the header is line 1; the original test files each contain 1048576 bytes.

| Codec | Train -> test | K | Ratio | CSV line |
| --- | --- | ---: | ---: | ---: |
| BPE inc | V1 -> V1 | 256 | 0.605747 | 2 |
| BPE inc | V1 -> V1 | 3840 | 0.332326 | 6 |
| BPE inc | E1 -> E1 | 256 | 0.747497 | 9 |
| BPE inc | E1 -> E1 | 3840 | 0.464467 | 13 |
| LZW | V1 test | - | 0.492817 | 38 |
| LZW | E1 test | - | 0.538014 | 39 |

Tables and figures: [rq1/out/](rq1/out/), [rq2/out/](rq2/out/) and [rq3/out/](rq3/out/).
Draft reports: [RQ1](rq1/RQ1_report_draft.md), [RQ2](rq2/RQ2_report_draft.md) and [RQ3](rq3/RQ3_report_draft.md).
These results describe the measured corpora; the V1/E1 corpora are non-parallel, so cross-language comparisons are correlational.

## Responsibilities and known limitations

| Pair | Responsibility |
| --- | --- |
| Pair 1 | Root RLE/LZW/container, synthetic data, RQ1 runner and tools/ |
| Pair 2 | rq2/: canonical Huffman, entropy, reordering, RQ2 tests and report; root Huffman shim |
| Pair 3 | rq3/: naive/noheap/inc BPE, RQ3 experiments, tests, analysis and report |

- The current `results/results_rq1.csv` contains the 150-row same-machine resample (50 rows per codec), replacing the earlier mixed-machine measurements.
  The owner reports an Intel Core i7-13650HX, 24 GB RAM, Windows 11 and Python 3.13.2; total wall time was 1160.0407191 seconds.
  Progress was checked by reading the output file several times, so light timing interference is possible but unquantified.
  Six timing cells across three rows exceeded 1.3 times their three-seed group median and remain in the data; this screening does not prove noise.
  Same-machine collection does not eliminate load or thermal effects. See [handoff](docs/PAIR12_HANDOFF.md).
- BPE trains until K merges or no within-segment adjacent pairs remain, including singleton pairs.
- All primary RQ3 rows now use the same full training input for a given corpus/K.
  Naive timings have one repetition; no confidence interval is claimed.
- Data and archives must be obtained separately; Git does not supply `data/` or `kennedy.xls`.
- Installation, corpus acquisition and full experiment regeneration were not rerun for this README; their commands are explicitly marked unverified.

## Documentation

Project-owner decisions, implementation checks and RQ1 provenance: [DECISIONS.md](docs/DECISIONS.md).

## Revised submission

The current report is [CSD203_DA4_Report_Revised.docx](final_submission/CSD203_DA4_Report_Revised.docx),
with reproducible Markdown and HTML siblings. Build with
`python -m final_submission.generate_report` then `python -m final_submission.build_submission`.
Verify the report with `python -m final_submission.generate_report --check` and
`python -m final_submission.validate_submission`; DOCX export requires python-docx.
The superseded `CSD203_DA4_IEEE_Final.*` report files have been removed.
RQ1/RQ2 timing CSVs are historical measurements; decoder validation was hardened
after collection, so they are not presented as fresh timing measurements of the revised code.
The RQ1 measurement function now validates SHA-256 in its separate memory pass too.
