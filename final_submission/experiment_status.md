# Experiment status — revised submission

| Component | Current primary artifacts | Status |
|---|---|---|
| RQ1 | results/results_rq1.csv, rq1/out/ | 150 historical same-machine rows; unchanged metrics. Memory-pass hash checking is fixed for future runs and regression-tested. |
| RQ2 | results_rq2_all.csv, rq2/out/ | 45 historical rows; numeric results retained. Huffman/LZW decoder validation was hardened after collection. |
| RQ3 | results/results_rq3.csv, rq3/out/rq3_run_audit.json | 38 rows; all variants train on full manifest inputs at all K. Four actual full-naive training timings imported with input/merge hashes; eight test rows newly measured. |
| Historical archive | results/archive/mixed_scope/ | Original CSV, audit and edge records preserved as evidence, excluded from primary analysis. |
| Edge | results/results_edge.csv | 15 original non-BPE rows preserved byte-for-byte; 18 BPE rows regenerated with singleton merges enabled. |
| Training memory | rq3/out/train_mem.csv | Six historical 128 KiB/K=256 traced runs; separate, explicitly labelled scope. |
| Report | CSD203_DA4_Report_Revised.md/.docx/.html | New report, six authors supplied by the user, six source-generated tables and seven current figures. No PDF is listed as a deliverable. |

The four full-corpus naive timings originate in naive_full_experiment.json.
The migration checks measured input hashes, merge hashes, merge count and positive
elapsed time against fresh inc training before importing. It does not invent
training measurements or copy inc timings as naive timings. The corresponding
compression/decompression/memory test rows were measured again.

Reproduction: see the repository README, rq3/README.md, and validation_report.md.
The historical RQ1 memory pass did not check the restored hash; the corrected
runner does. Passing new regression tests is not retroactive proof of that old
pass, and historical times are not described as fresh measurements.
