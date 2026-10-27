# RQ3: full-corpus BPE and LZW

From the repository root:

```powershell
python -m rq3.run_rq3 results
python -m rq3.run_rq3 edge
python -m rq3.check_results_rq3
python -m rq3.analyze_rq3
python -m rq3.analyze_rq3 --check
```

The results command resumes existing models and rows; it validates model input
hashes and refuses historical prefix models. Fresh models always use full
manifest-validated train inputs. Results contain 36 BPE rows and 2 LZW baselines.
All corpus/K combinations have the same training input across inc/noheap/naive.
See [DESIGN.md](DESIGN.md) for merge rules, binary layout and measurement scope.

`python -m rq3.upgrade_full` is a one-time migration for the historical mixed-scope
matrix. It archives the original CSV/audit/edge records, validates four measured
naive training cells from final_submission/naive_full_experiment.json, and
removes eight prefix-trained test rows for fresh measurement by results.
It also removes old BPE edge rows for regeneration under the corrected singleton
merge rule; the original RLE/Huffman/LZW edge bytes are preserved exactly.

`python -m rq3.run_rq3 train-memory` creates the separate 128 KiB/K=256 training
memory experiment and refuses to overwrite its output. This scope is explicit
in tables and figures; it does not replace the 1 MiB training matrix.

The phase3/phase4 preflight JSON files are historical feasibility records.
Their source protection snapshots describe collection-time files, not a ban on
later authorized fixes. The current runner records execution source hashes and
checks that they do not change during a measurement run.

Current analysis: rq3/out/ and RQ3_report_draft.md (generated technical appendix).
Current submission: final_submission/CSD203_DA4_Report_Revised.docx.
