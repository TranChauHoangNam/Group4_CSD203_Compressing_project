# Lược đồ CSV chung – CSD203 Đề tài 4 (AI21B – FA26)

Mục tiêu: cả ba cặp ghi kết quả theo **cùng một header**, để gộp thành một bảng duy nhất cho báo cáo.

Ký hiệu: **[ĐỀ]** = đề bài quy định. **[ĐX]** = đề xuất của mình, cần cả nhóm đồng ý.

## 1. Quy ước tệp

- Mỗi cặp ghi file riêng, cùng header: `results_rq1.csv` (Cặp 1), `results_rq2.csv` (Cặp 2), `results_rq3.csv` (Cặp 3). Ca biên ghi vào `results_edge.csv`. Khi cần thì nối các file lại (một header). [ĐX]
- UTF-8 không BOM, phân cách dấu phẩy, xuống dòng LF, có dòng header. [ĐX]
- Số thực dùng dấu chấm. Ô không áp dụng để **trống** (không ghi NA, 0 hay "-"). [ĐX]
- Mỗi dòng là **một lượt đo** (một file × một codec × một cấu hình). [ĐX]
- Chỉ ghi dòng khi round-trip đúng. Nếu SHA-256 không khớp thì dừng và sửa lỗi, không ghi số liệu. [ĐX, dựa trên yêu cầu Oracle của đề]

## 2. Các cột (đúng thứ tự)

| # | Cột | Kiểu | Giá trị / ý nghĩa | Dùng cho |
|---|---|---|---|---|
| 1 | `rq` | text | `1`, `2`, `3` hoặc `edge` | tất cả |
| 2 | `dataset` | text | `C1`, `C2`, `C3`, `V1`, `E1`, `R1` [ĐỀ] | tất cả |
| 3 | `file` | text | Tên file dữ liệu, ví dụ `C2_1048576_s1.bin`, `alice29.txt`, `kennedy.xls`, `v1_test_1mib.txt` | tất cả |
| 4 | `state` | text | `original`, `runs` (counting sort), `shuffled` (Fisher–Yates) [ĐỀ]. RQ1, RQ3 luôn là `original` | tất cả |
| 5 | `size_kib` | int | Kích thước danh nghĩa S: 256, 512, 1024, 2048, 4096 [ĐỀ] | RQ1 (còn lại để trống) |
| 6 | `seed` | int | Seed của dữ liệu tổng hợp hoặc của Fisher–Yates. Đề yêu cầu 3 seed; đề xuất dùng 1, 2, 3 [ĐX] | C1–C3, RQ2 `shuffled` |
| 7 | `codec` | text | `rle`, `huffman`, `lzw`, `bpe` (đúng cột "Tên CSV" của đề) [ĐỀ] | tất cả |
| 8 | `train_variant` | text | `inc`, `noheap`, `naive` (tương ứng `bpe (inc)`, `bpe (noheap)`, `bpe (naive)` của đề) | RQ3 (codec = bpe) |
| 9 | `k_merges` | int | Số lượt merge K: 256, 1024, 3840 [ĐỀ] | BPE |
| 10 | `train_corpus` | text | `V1` hoặc `E1` (ngữ liệu huấn luyện) | RQ3 |
| 11 | `test_corpus` | text | `V1` hoặc `E1` (ngữ liệu kiểm tra) | RQ3 |
| 12 | `orig_bytes` | int | Kích thước dữ liệu đưa vào nén (byte) | tất cả |
| 13 | `comp_bytes` | int | Kích thước file nén, gồm cả header [ĐỀ] | tất cả |
| 14 | `ratio` | float | `comp_bytes / orig_bytes` (nhỏ hơn là tốt hơn) [ĐỀ]. Với BPE, đây là tỷ lệ **tính cả Header và Bảng Merge** | tất cả |
| 15 | `ratio_tokens_only` | float | BPE: tỷ lệ chỉ tính chuỗi token [ĐỀ] | BPE |
| 16 | `h0_bits` | float | H₀ tính bằng bit/byte của dữ liệu đưa vào nén | RQ2 (nên có cả RQ1) |
| 17 | `h0_ratio` | float | `h0_bits / 8`, mốc để so với `ratio` | RQ2 (nên có cả RQ1) |
| 18 | `n_tokens` | int | Số token sau mã hóa BPE | BPE |
| 19 | `bytes_per_token` | float | `orig_bytes / n_tokens` [ĐỀ] | BPE |
| 20 | `comp_ms` | float | Thời gian nén (ms), đo bằng `time.perf_counter` [ĐX] | tất cả |
| 21 | `decomp_ms` | float | Thời gian giải nén (ms) | tất cả |
| 22 | `comp_kibs` | float | Thông lượng nén: `(orig_bytes/1024) / (comp_ms/1000)` [ĐỀ: đơn vị KiB/s] | tất cả |
| 23 | `decomp_kibs` | float | Thông lượng giải nén, cùng công thức, theo `orig_bytes` | tất cả |
| 24 | `train_ms` | float | Thời gian huấn luyện tokenizer, đo riêng với `comp_ms` [ĐỀ] | BPE |
| 25 | `peak_mem_kib` | float | Bộ nhớ đỉnh (KiB), đề xuất đo bằng `tracemalloc` (nén + giải nén), cả nhóm dùng cùng một cách [ĐX] | RQ1 (nên có cả RQ2, RQ3) |
| 26 | `output_check` | text | 16 ký tự hex đầu của SHA-256 dữ liệu **sau khi giải nén** (bằng SHA-256 dữ liệu gốc) [ĐỀ] | tất cả |
| 27 | `roundtrip_ok` | bool | `true` nếu SHA-256 sau giải nén bằng SHA-256 trước khi nén [ĐX] | tất cả |
| 28 | `notes` | text | Ghi chú tự do (tránh dấu phẩy, hoặc đặt trong ngoặc kép) | tuỳ chọn |

## 3. Ví dụ dòng

```
rq,dataset,file,state,size_kib,seed,codec,train_variant,k_merges,train_corpus,test_corpus,orig_bytes,comp_bytes,ratio,ratio_tokens_only,h0_bits,h0_ratio,n_tokens,bytes_per_token,comp_ms,decomp_ms,comp_kibs,decomp_kibs,train_ms,peak_mem_kib,output_check,roundtrip_ok,notes
2,R1,alice29.txt,shuffled,,1,huffman,,,,,152089,87000,0.572,,4.57,0.571,,,310.2,280.4,478.8,529.7,,2100.5,9f86d081884c7d65,true,
```

(Các con số trong ví dụ chỉ để minh họa định dạng, không phải kết quả thật.)

## 4. Quy tắc riêng từng RQ

- **RQ1**: `dataset` ∈ {C1, C2, C3, V1}; `size_kib` điền S; `seed` điền cho C1–C3 (V1 để trống); `codec` ∈ {rle, huffman, lzw}.
- **RQ2**: `dataset = R1`; mỗi file × 3 `state` × 3 `codec` = 27 dòng nếu không lặp seed. Với `state = shuffled` điền `seed`. `h0_bits` và `h0_ratio` bắt buộc.
- **RQ3**: `codec` ∈ {bpe, lzw}. Dòng BPE cần `train_variant`, `k_merges`, `train_corpus`, `test_corpus`, `ratio` và `ratio_tokens_only`, `n_tokens`, `bytes_per_token`, `train_ms`. Dòng LZW dùng để so với BPE (cùng ngân sách 4.096 ký hiệu 12-bit).
- **edge**: ca biên (file rỗng, 1 byte, 64 KiB cùng byte, 256 giá trị, `ABABABA`, `aaabdaaabac` K=3). Khi `orig_bytes = 0` thì để trống `ratio` và các cột throughput.

## 5. Các điểm cần cả nhóm xác nhận

1. Mỗi cặp một file hay cả nhóm một file chung (đề xuất: mỗi cặp một file, cùng header).
2. Giá trị seed (đề xuất 1, 2, 3).
3. Cách đo bộ nhớ đỉnh (đề xuất `tracemalloc`) và số lần lặp mỗi lượt đo (đề không quy định; nên chốt, ví dụ lấy trung vị của vài lần).
4. Tên file chuẩn cho R1 (đề xuất: `alice29.txt`, `kennedy.xls`, `v1_test_1mib.txt`).

Module `results_schema.py` đi kèm chứa danh sách cột, hàm tính các cột dẫn xuất và hàm ghi dòng có kiểm tra, để cả ba cặp dùng chung.
