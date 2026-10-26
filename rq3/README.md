# RQ3 — khung BPE cho Cặp 3

Chưa cài thuật toán BPE. Năm hàm trong `bpe.py` chỉ có chữ ký,
docstring và `raise NotImplementedError`. Cấu trúc merges/tokens chưa chốt.
`compress` khi cài đặt phải dùng `container.pack_header(b"BPE1", len(data))`.
Biến thể: `inc`, `noheap`, `naive`; K thực nghiệm: 256, 1024, 3840.

## Test

Từ thư mục gốc chạy `python -m pytest -q`.
Test BPE đánh dấu `xfail(reason="chưa cài BPE")`, chỉ chấp nhận
`NotImplementedError`; lỗi khác vẫn làm test thất bại. Gồm bytes rỗng,
`A`, `ABABABA`, ví dụ `aaabdaaabac` với K=3 và file ngắn tạo trong tmp_path.
K=3 gọi trực tiếp train/encode/decode, không ghi CSV.

Việc cần làm sau: cần cho phép k_merges=3 khi rq == edge trong common/results_schema.py.
Scaffold này chưa nới quy tắc K của schema.

## CSV chung

Mã BPE chỉ dùng `common.results_schema`, không import schema trong `tools/`.
Ghi bằng `from common.results_schema import append_row, sha16`, rồi
`append_row(path, row)` sau khi kiểm tra round-trip. Thư mục cha của CSV
phải tồn tại trước khi gọi.

Đặt `rq="3"`, `codec="bpe"`, dataset hợp lệ, `state="original"`, tên `file`,
`orig_bytes`, `comp_bytes`, `output_check=sha16(decoded)` và `roundtrip_ok=True`.
Các cột RQ3 phải được điền theo phép đo:

| Cột | Nội dung |
| --- | --- |
| train_variant | inc / noheap / naive |
| k_merges | 256 / 1024 / 3840 |
| train_corpus | Corpus dùng huấn luyện, ví dụ V1 hoặc E1 |
| test_corpus | Corpus dùng đánh giá, ví dụ V1 hoặc E1 |
| ratio | comp_bytes / orig_bytes; cần chốt phần bảng merge bên dưới |
| ratio_tokens_only | Số byte phần tokens / orig_bytes, loại bảng merge và header |
| n_tokens | Số token sau encode |
| bytes_per_token | orig_bytes / n_tokens (schema có thể tự tính) |
| train_ms | Thời gian huấn luyện tính bằng ms |

Không chia cho 0 với dữ liệu rỗng; để trống các tỷ lệ không xác định.
`dataset` chỉ được trống/None/không có khi `rq="edge"`.

Câu hỏi còn mở: cách tính kích thước bảng merge cho `ratio` là gì?
Cần chốt định dạng tuần tự hóa và chi phí bảng merge khi dùng chung giữa
train/test trước khi báo cáo số liệu; scaffold chưa quyết định thay nhóm.

## Bản Cặp 1 và bất tương thích

Nguồn: `.pair1-review-fsd1o4mc/pair1_ready/`. Bốn file Python trong `tools/`
được copy nguyên văn; không đổi import. `requirements-wiki.txt` được tạo lại
từ import ngoài thư viện chuẩn (`datasets`), không ghim phiên bản.

- `tools/run_edge.py:10,26` import và khởi tạo `CsvWriter`.
- Trong nguồn, `run_rq1.py:17,50` và `test_pair1.py:14,145` cũng dùng
  `CsvWriter`; hai file này không được copy.
- `tools/results_schema.py:74` định nghĩa `CsvWriter`; dòng 53 định dạng
  float bằng `.6f` (6 chữ số sau dấu thập phân).
- `common/results_schema.py` dùng `append_row`, tự điền các cột dẫn xuất,
  và `.6g` (6 chữ số có nghĩa). Hai API không thay thế trực tiếp cho nhau.
- Schema Cặp 1 cho dataset trống với mọi rq và state trống; schema chung
  chỉ cho dataset trống với edge, không cho state trống. Cặp 1 không kiểm
  tra tập K/size như schema chung, và yêu cầu roundtrip_ok là bool True.
- CsvWriter tạo thư mục cha, kiểm tra header CSV hiện có; append_row không
  làm hai việc này. Không trộn hai writer mà chưa thống nhất hợp đồng.

`run_edge.py` dùng import cục bộ `measure`/`results_schema`; `measure.py`
còn import `container` ở gốc repo. Khi chạy script trực tiếp cần đưa gốc
repo vào PYTHONPATH (PowerShell, từ gốc):

```powershell
$env:PYTHONPATH = (Get-Location).Path
python tools/run_edge.py --codecs rle lzw
```

Module `huffman.py` ở gốc hiện chuyển tiếp `compress`/`decompress` sang
`rq2.huffman`; run_edge có thể chạy cả rle, huffman và lzw.

## Tái tạo Wikipedia

`docs/manifest.json` là manifest nguyên văn từ nguồn, chứa phiên bản và hash.
Không copy các file văn bản dữ liệu. Từ thư mục gốc:

```powershell
python -m pip install -r tools/requirements-wiki.txt
python tools/prepare_wiki.py --data-dir data/wiki
```

Pipeline dùng wikimedia/wikipedia 20231101, chuẩn hóa NFC/UTF-8 và cắt tại
ranh giới ký tự. Đối chiếu hash và số byte trong manifest sau khi tạo lại.
Chưa tải dữ liệu hoặc cài dependency trong tác vụ dựng khung này.
