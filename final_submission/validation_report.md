# Validation report — 2026-10-27 revision

## Executed checks

| Check | Result |
|---|---|
| Focused regression suite | 609 passed in 28.95 s |
| Complete pytest suite | **761 passed in 28.26 s** |
| RQ1 report verification | 1080/1080 numeric cells matched; quantitative draft assertions passed |
| RQ2 result checker | 9/9 passed |
| RQ2 mechanism checker | All three inputs processed |
| RQ2 report verifier | 119 trace rows and three tables matched |
| RQ3 result checker | 7/7 passed, with full train required for all primary variants/K |
| Shared edge compatibility | 33/33 accepted |
| RQ3 analysis regeneration | 15 text artifacts reproduced exactly |
| Revised report source check | Text, six tables and input SHA-256 manifest reproduced exactly |
| DOCX conversion check | Six tables equal Markdown; six supplied authors; seven current figures; two-column sections |
| Word rendering | Opened read-only in hidden Microsoft Word; 9 pages; all-page contact sheet and detailed selected pages inspected |

The complete suite command was:
`python -m pytest -q --basetemp <system-temp>/group4-fixes-20261027-full`.
It ran outside the sandbox with approval because Windows sandbox permissions
prevented pytest temporary-directory access in the earlier audit. No assertions
were bypassed to work around that permission issue.

Re-run read-only validation with:

```powershell
python -m rq1.verify_rq1_report
python -m rq2.check_results
python -m rq2.check_mechanism
python -m rq2.verify_report
python -m rq3.check_results_rq3
python tools/check_edge_compat.py
python -m rq3.analyze_rq3 --check
python -m final_submission.generate_report --check
python -m final_submission.validate_submission
```

## Corrections verified

- RQ1 checks full SHA-256 in the separate memory pass and stops tracing on exceptions.
  A regression codec that fails only in the memory pass now raises an error.
- LZW rejects nonzero low-nibble padding; all 15 invalid padding values are tested.
- Huffman rejects oversubscribed code lengths, nonzero padding, trailing payload
  and nonempty tables/payload for an empty stream. Tests now require rejection
  by the production decoder, not only the independent reference implementation.
- BPE merges count-one pairs and stops only at K or when no within-segment pair
  remains. Hand-checked singleton/overlap examples and independent occurrence
  oracles cover the revised rule; the assignment K=3 example remains unchanged.
- Full naive training timings for V1/E1 at K=1024/3840 were imported only after
  validating source input size/hash and merge hash against fresh inc training.
  Eight associated test rows were newly measured; all primary RQ3 training
  scopes are now full corpus. Old mixed-scope records are archived separately.
- Eighteen BPE edge rows were regenerated; the original 15 non-BPE CSV rows are
  preserved byte-for-byte. Full-data compression sizes match across variants.
- RQ3 tables and figures were regenerated. The new report includes both BPE
  ratios and LZW for every K/train/test combination, the 2×2 tokenizer matrix,
  training complexity and measured speedups with consistent units.
- The three superseded CSD203_DA4_IEEE_Final files (MD/DOCX/HTML) were deleted
  after the replacement's data and Word rendering were checked.

## Scope and remaining scientific limitations

Report source hashes use UTF-8 text with canonical LF line endings so Git
checkout conversion between LF and CRLF does not invalidate the report manifest.
Corpus and measured output hashes remain hashes of the original raw bytes.

RQ1/RQ2 CSV measurements were not rerun: they remain historical observations,
including the former unverified RQ1 memory-pass restoration. New tests do not
retroactively prove that pass; the revised report states this provenance.
Naive training has one timing per cell; training-memory data are only
128 KiB/K=256; V1/E1 are non-parallel. These are disclosed experimental limits,
not claims that additional experiments were performed.

The report uses a two-column academic layout with spanning tables/figures.
No instructor-specific IEEE template was supplied. The six author names/MSSVs
were supplied by the user; no instructor identity was invented.
No PDF is claimed or included as a deliverable. Word preview PNGs are temporary
inspection artifacts outside the project; DOCX/Markdown/HTML are the report outputs.
