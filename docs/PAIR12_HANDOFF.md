# Bàn giao Cặp 1 và Cặp 2

Nguồn Cặp 1: `.pair1-review-fsd1o4mc/pair1_ready/`.
`run_rq1.py`, `gen_synthetic.py` được copy nguyên văn vào gốc.
Runner dùng `measure` và `results_schema` nguyên văn trong `tools/`.
`huffman.py` chuyển tiếp hai hàm byte tới `rq2.huffman`.
Không sửa `rle.py`, `lzw.py`, `container.py`.

## Chạy từ thư mục gốc bằng PowerShell

```powershell
$env:PYTHONPATH = "$PWD;$PWD\tools"
$env:PYTHONIOENCODING = "utf-8"
python gen_synthetic.py --out-dir data/synthetic
python -m pip install -r tools/requirements-wiki.txt
python tools/prepare_wiki.py --data-dir data/wiki
python run_rq1.py --help
python run_rq1.py --data-dir data --codecs rle huffman lzw --out results/results_rq1.csv
python tools/run_edge.py --codecs rle huffman lzw --out results/results_edge.csv
python tools/check_edge_compat.py
python -m pytest -q
python rq2/check_results.py
python rq2/verify_report.py
```

RQ1 mặc định đo trung vị 3 lần và thêm một lượt đo bộ nhớ.
Runner bỏ qua khóa `(file, codec)` có sẵn: chọn CSV mới nếu muốn đo lại.
run_edge ghi nối: chọn CSV mới nếu đã có kết quả để tránh trùng dòng.
Các phép đo thời gian phụ thuộc máy và tải hệ thống.

## Dữ liệu và nguồn CSV

Đã sinh mới 45 file C1/C2/C3, 5 kích thước, 3 seed.
`gen_synthetic.ensure_file` không ghi đè file đã tồn tại: khi tái tạo bộ lỗi,
cần chuyển bộ cũ sang nơi lưu riêng trước rồi mới chạy bộ sinh.
`docs/synthetic_manifest.json` lưu kích thước và SHA-256 của 45 file.
`C1_262144_s2.bin` có 262144 byte, sha16 `7e9dbc6007a58ecf`.

| S (KiB) | Byte/file | C1 (seed 1–3) | C2 (seed 1–3) | C3 (seed 1–3) |
| --- | ---: | --- | --- | --- |
| 256 | 262144 | 3/3 đúng | 3/3 đúng | 3/3 đúng |
| 512 | 524288 | 3/3 đúng | 3/3 đúng | 3/3 đúng |
| 1024 | 1048576 | 3/3 đúng | 3/3 đúng | 3/3 đúng |
| 2048 | 2097152 | 3/3 đúng | 3/3 đúng | 3/3 đúng |
| 4096 | 4194304 | 3/3 đúng | 3/3 đúng | 3/3 đúng |

Không có file tổng hợp lệch kích thước. File lỗi 517426 byte được mô tả
trong yêu cầu không còn ở đường dẫn nguồn `data/synthetic` đã kiểm tra.

Năm file V1 RQ1 được copy vào `data/wiki/` từ nguồn, không đưa vào Git.
Đối chiếu dữ liệu V1 với `docs/manifest.json`; pipeline tái tạo ở trên.
V1 được cắt ở ranh giới UTF-8 nên có thể nhỏ hơn kích thước danh nghĩa.

## Current RQ1 measurement provenance

`results/results_rq1.csv` now contains the complete same-machine resample:
150 rows, 50 each for RLE, Huffman and LZW. It replaces the earlier dataset
that retained 100 Pair 1 RLE/LZW rows and added 50 Pair 2 Huffman rows from
a different machine. That mixed-machine limitation describes the superseded
measurements, not the current primary RQ1 CSV.

The owner reports Intel Core i7-13650HX, 24 GB RAM, Windows 11, Python 3.13.2,
and total wall time of 1160.0407191 seconds. The resample validation found no
duplicate keys, all round trips true, all rows schema-valid, and identical
comp_bytes/output_check for all 150 keys compared with the superseded CSV.

Limitations: the owner read the output file several times to check progress,
which may have introduced light interference; its impact has not been measured.
Six timing cells in three rows exceeded 1.3 times their corresponding three-seed
group median: compression and decompression for C1_4194304_s3.bin/Huffman,
C1_4194304_s3.bin/LZW and C2_1048576_s1.bin/RLE. All rows are retained.
Different seeds contain different inputs, so these flags do not establish noise.
Same-machine collection does not remove load, thermal or execution-order effects.

## Schema và test

Edge được ghi bằng `tools/results_schema.CsvWriter`, sau đó đọc nguyên
giá trị chuỗi CSV và kiểm tra bằng `common.results_schema.validate_row`.
Không nới schema. BPE tiếp tục chỉ dùng schema trong `common/`.
Khác biệt CsvWriter/append_row và .6f/.6g được ghi ở `rq3/README.md`.

Test cơ chế dùng `pytest.importorskip("rle")` để bỏ qua khi module vắng mặt.
`rq2.run_rq2.load_codecs` đã bắt ImportError cho rle/lzw, giữ nguyên;
test monkeypatch hiện có kiểm tra hành vi này.

`data/`, `*.xls`, `*.zip`, `.pair1-review-*/` được bỏ qua bởi `.gitignore`.
Không tạo nhánh, stage, commit hay push trong tác vụ này.

## Historical handoff checks (before the RQ1 resample and completed BPE)

The following is the original handoff record, not a description of the current
CSV provenance, edge-row count or current test suite.

## Kết quả kiểm tra ngày 2026-10-27

- `results/results_rq1.csv`: 150 dòng, mỗi codec 50; đúng toàn bộ ma trận
  50 file × 3 codec, không trùng khóa, mọi dòng roundtrip_ok=true.
  100 dòng gốc được giữ nguyên từng byte; mọi hash và orig_bytes khớp dữ liệu.
- `results/results_edge.csv`: 15 dòng, mỗi codec 5; 15/15 qua schema chung,
  không dòng nào bị từ chối. Cả ba codec từ chối magic sai.
- `results_rq2_all.csv`: giữ nguyên 45 dòng, mỗi codec 15.
- `python -m pytest -q`: 135 passed, 31 xfailed (BPE chưa cài).
  Chạy ngoài sandbox vì thư mục tạm của pytest bị hạn chế quyền trong sandbox.
- `python rq2/check_results.py`: đạt 9/9 mục.
- `python rq2/verify_report.py`: khớp 119 dòng truy vết và 3 bảng.
- Hash rle.py/lzw.py/container.py không đổi; runner và bộ sinh trùng nguồn.

Ví dụ RQ1 cho `C1_262144_s2.bin` (orig_bytes=262144):

| Codec | comp_bytes | ratio | roundtrip_ok |
| --- | ---: | ---: | --- |
| rle | 16704 | 0.063721 | true |
| lzw | 60675 | 0.231457 | true |
| huffman | 261838 | 0.998833 | true |

## 2026-10-29: explicit result status (schema v2)

Section 6 of the course rules requires ok/timeout/crash/oom/wrong. The active
raw CSVs now have 29 columns, with mandatory status after notes. Both writers
share validation and reject appending to a legacy header. Runners emit ok only
after successful round-trip validation; automatic failure capture is deferred.

Migration adds ok to the 266 existing successful rows (RQ1 150, RQ2 45, RQ3 38,
edge 33), preserving all 28 original cell strings. The migration tool backs up
original bytes outside the repository and is byte-idempotent. Historical ok
does not assert that the run used a 60-second subprocess timeout. No measurement
is rerun or reclassified based on its historical duration.

Archives, derived tables and training-memory CSVs retain their original schemas.
The edge audit retains its original SHA-256 and 2,482-byte length. A versioned
projection removes status and serializes the original header plus 15 rows in
legacy column order, UTF-8/LF, before checking the original digest. Historical
source hashes in the audit remain unchanged; report_sources.json is refreshed
for the new CSV/audit bytes without changing report numbers.
