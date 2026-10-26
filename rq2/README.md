# CSD203 – Đề tài 4: phần việc Cặp 2

- `h0.py`: **bản chính của người dùng**, histogram 256 byte, entropy H0 (bit/byte), mốc tỷ lệ H0/8.
- `reorder.py`: **bản chính của người dùng**, counting sort bằng histogram tạo các run tăng dần, không gọi `sorted()`; Fisher–Yates tự cài đặt với `random.Random(seed)`. Hai hàm tạo kết quả `bytes` từ bộ đệm riêng, giữ nguyên đầu vào, histogram và H0. Python có thể tái sử dụng đối tượng `bytes` rỗng bất biến.
- `huffman.py`: **bản chính của partner**, Huffman tĩnh hai lượt, mã chính tắc; giữ `Node`, `build_code_lengths`, `generate_canonical_codes`, `huffman_compress`, `huffman_decompress`. API chung `compress(data: bytes) -> bytes` / `decompress(blob: bytes) -> bytes` gọi hai hàm tương ứng của partner. Giữ `MAGIC`, `HEADER_SIZE`, `histogram` và `output_check` (16 ký tự hex đầu của SHA-256) để tương thích.
- `tests/`: kiểm tra các ca biên, SHA-256 đầy đủ, định dạng nhị phân, Kraft, giới hạn entropy, tính tái lập, luồng sai/cắt cụt và round-trip 1 MiB.
- `tests/reference/`: chỉ dùng trong test, **không dùng cho thực nghiệm RQ2**. `huffman_alt.py` là Huffman độc lập trước khi merge; `partner_original.py` giữ bản partner bỏ demo, dùng đối chiếu H0 và đảo byte. H0 và đảo byte của partner không được đưa vào module Huffman chính.
- [MERGE_NOTES.md](MERGE_NOTES.md): thay đổi cụ thể, giới hạn giữ nguyên và kết quả kiểm thử của lần merge.
- `run_rq2.py`: runner đo RQ2, hỗ trợ Huffman và nạp RLE/LZW tùy chọn; ghi CSV qua `common/results_schema.py`.
- [WORK_NOTES.md](WORK_NOTES.md): thay đổi và kết quả kiểm tra runner/schema.

## Chạy test

Chạy tại thư mục cha của `rq2/` (thư mục gốc dự án), dùng Python 3.9 trở lên:

```console
python -m pip install pytest
python -m pytest -q
```

Các module chỉ dùng thư viện chuẩn. `pytest` là phụ thuộc dành riêng cho kiểm thử. Test cũ trong `test_huffman.py` vẫn dùng `os.urandom` cho mẫu 64 KiB; test đối chiếu mới trong `test_cross_check.py` dùng `random.Random(203)` để tái lập dữ liệu, không dùng `os.urandom`.

Test đối chiếu bao gồm dữ liệu rỗng, 1 byte, 64 KiB cùng byte, đủ 256 giá trị byte, `ABABABA`, văn bản lặp và 64 KiB ngẫu nhiên. Hai bản Huffman phải giải nén chéo đúng và có cùng kích thước file nén; không yêu cầu blob giống từng byte. H0 có sai số tuyệt đối dưới `1e-12`; counting sort phải cho cùng byte; hai Fisher–Yates phải bảo toàn histogram.

File `pytest.ini` tại thư mục gốc giới hạn việc tìm test trong `rq2/tests`, tránh nhận thư mục gốc từ project khác ở cấp cha. Cache tùy chọn của pytest được tắt để chạy được trong môi trường hạn chế quyền ghi cache.

Ví dụ sử dụng từ thư mục gốc:

```python
import hashlib

from rq2.h0 import entropy_h0, h0_ratio
from rq2.huffman import compress, decompress, output_check
from rq2.reorder import counting_sort_runs, fisher_yates

data = b"banana bread" * 100
blob = compress(data)
restored = decompress(blob)
assert hashlib.sha256(restored).digest() == hashlib.sha256(data).digest()
assert entropy_h0(fisher_yates(data, seed=203)) == entropy_h0(data)
print(h0_ratio(data), output_check(restored), len(blob))
```

## Định dạng HUF1

| Offset | Kích thước | Nội dung |
| --- | --- | --- |
| 0 | 4 byte | Magic `b"HUF1"` |
| 4 | 8 byte | Độ dài gốc, số nguyên không dấu big-endian |
| 12 | 256 byte | Độ dài mã của từng byte 0–255; 0 nghĩa là không xuất hiện |
| 268 | Còn lại | Payload MSB first; đệm bit 0 ở byte cuối |

Lượt 1 dùng cách dựng cây `heapq` của partner; khi cùng tần suất, `Node.__lt__` so sánh `(symbol or 0)`, tức nút trong có `symbol=None` được coi như 0. Quy tắc này được giữ nguyên. Độ dài được chuyển thành mã chính tắc theo thứ tự `(độ dài, giá trị byte)` tăng dần. Lượt 2 ghép chuỗi bit, đệm 0 rồi đóng gói bằng `bytearray`. Giải mã tạo chuỗi bit của payload và bảng tra `chuỗi mã -> byte` từ header, đọc MSB first và dừng khi đủ độ dài gốc.

Dữ liệu rỗng có header 268 byte và payload rỗng. Một loại byte có mã 0 dài 1 bit. `decompress` và `huffman_decompress` báo `ValueError` khi magic sai, blob ngắn hơn 268 byte hoặc số byte giải ra không khớp độ dài gốc (ví dụ payload bị cắt cụt). Hai kiểm tra độ dài được thêm khi merge; kiểm tra magic đã có trong bản partner.

Bản chính giữ hành vi partner: không kiểm tra riêng bảng vượt Kraft, padding khác 0 hoặc byte thừa khi đã đủ độ dài gốc; độ dài gốc bằng 0 trả dữ liệu rỗng ngay sau kiểm tra header. Bản đối chứng `huffman_alt.py` kiểm tra nghiêm ngặt hơn các trường hợp này. Test cũ tương ứng giữ kiểm tra từ chối ở bản đối chứng và xác nhận hành vi hiện tại của bản chính. Định dạng không chứa checksum nên không phát hiện được mọi thay đổi bit; SHA-256 được đối chiếu bên ngoài trong test.

Khi so sánh với H0, độ dài mã trung bình bằng tổng `tần suất × độ dài mã` chia số byte gốc. Kích thước payload thực tế còn tối đa 7 bit đệm; tổng file còn 268 byte header. Test văn bản mẫu kiểm tra cả độ dài mã trung bình và payload gồm đệm đều thuộc `[H0, H0 + 1)`. Giới hạn trên nghiêm ngặt này không áp dụng cho trường hợp duy nhất một loại byte vì quy ước mã dài 1 bit.

## Quy ước tích hợp CSV

Áp dụng [common/csv_schema.md](../common/csv_schema.md) do người dùng cung cấp, đã chuyển nguyên nội dung sang thư mục chung. Tệp này quy định đủ **28 cột theo đúng thứ tự**, dùng chung cho ba cặp. [results_schema.py](../common/results_schema.py) được lưu nguyên nội dung người dùng cung cấp, gồm `COLUMNS`, `sha16`, `finalize_row`, `validate_row`, `append_row`. Các mục `[ĐX]` vẫn mang ý nghĩa đề xuất của tài liệu, không phải yêu cầu gốc của đề.

Runner mặc định ghi kết quả Cặp 2 vào `results_rq2.csv`; `results_edge.csv` là quy ước riêng cho ca biên, runner hiện tại chỉ ghi RQ2. Dùng UTF-8 không BOM, dấu phẩy, xuống dòng LF và dấu chấm thập phân. Giữ đủ các cột; ô không áp dụng để trống, không thay bằng `NA`, `0` hay `-`.

Ánh xạ các hàm hiện có vào một dòng RQ2, với `data` là dữ liệu **sau khi áp dụng trạng thái** và `blob = compress(data)`:

| Cột | Giá trị / cách tính |
| --- | --- |
| `rq`, `dataset`, `codec` | `2`, `R1`, `huffman` |
| `file` | Tên file dữ liệu đang đo |
| `state` | `original`: giữ nguyên; `runs`: `counting_sort_runs`; `shuffled`: `fisher_yates` |
| `seed` | Seed thực sự truyền vào Fisher–Yates khi `shuffled`; hai trạng thái còn lại để trống |
| `orig_bytes` | `len(data)` |
| `comp_bytes` | `len(blob)`, **gồm cả header 268 byte** |
| `ratio` | `len(blob) / len(data)`; để trống nếu đầu vào rỗng |
| `h0_bits`, `h0_ratio` | `entropy_h0(data)`, `h0_ratio(data)`; bắt buộc cho RQ2 |
| `output_check` | `output_check(restored)`, với `restored = decompress(blob)` |
| `roundtrip_ok` | Ghi `true` chỉ sau khi SHA-256 đầy đủ của `restored` và `data` bằng nhau |

RQ2 để trống `size_kib` và các trường BPE: `train_variant`, `k_merges`, `train_corpus`, `test_corpus`, `ratio_tokens_only`, `n_tokens`, `bytes_per_token`, `train_ms`. Huffman ghi `notes=ratio_no_header=<giá trị>`, với giá trị là `(comp_bytes - 268) / orig_bytes`, cố định 6 chữ số sau dấu chấm; khi file rỗng ghi `ratio_no_header=` vì tỷ lệ không xác định. Codec khác để `notes` trống. Các số thực ở cột khác do schema định dạng bằng 6 chữ số có nghĩa (`.6g`), không phải 6 chữ số thập phân.

`comp_ms` và `decomp_ms` đo riêng lời gọi nén/giải nén bằng `time.perf_counter`, đổi sang mili giây và lấy trung vị của `--repeats` lượt (mặc định 3); không tính đọc file, reorder, entropy hoặc kiểm tra hash vào thời gian codec. `tracemalloc` chỉ bật trong một lượt nén + giải nén riêng sau các lượt thời gian; `peak_mem_kib = peak / 1024`. Số này đo cấp phát được Python theo dõi, không phải toàn bộ RSS của tiến trình. `comp_kibs = (orig_bytes / 1024) / (comp_ms / 1000)`; `decomp_kibs` dùng cùng số byte gốc và thời gian giải nén. `append_row` gọi `finalize_row` để tính tỷ lệ và throughput. Đầu vào rỗng để trống tỷ lệ và hai cột throughput. Cách đo này vẫn cần nhóm thống nhất trước khi so sánh kết quả giữa các cặp.

Kiểm tra round-trip bằng **toàn bộ SHA-256** trước khi ghi bất kỳ dòng kết quả nào; 16 ký tự `output_check` chỉ là giá trị lưu trong CSV. Với `runs`/`shuffled`, so sánh với dữ liệu đã reorder đưa vào codec, vì thay đổi thứ tự byte làm thay đổi SHA-256 dù histogram và H0 giữ nguyên.

Lưu ý cách đếm ở mục RQ2 của schema: mỗi file có `3 trạng thái × 3 codec = 9` lượt; **3 file R1 × 3 trạng thái × 3 codec = 27** lượt khi không lặp seed. Nếu chạy thêm seed cho `shuffled`, tổng số dòng tăng tương ứng. Các số trong dòng ví dụ của schema chỉ minh họa định dạng.

## Chuẩn bị dữ liệu và chạy RQ2

Đặt các file sau trong thư mục `data/` ở gốc project (đã được `.gitignore` bỏ qua):

```text
data/
  alice29.txt
  kennedy.xls
  v1_test_1mib.txt
```

`alice29.txt` và `kennedy.xls` lấy từ Canterbury Corpus; `v1_test_1mib.txt` là đầu ra pipeline V1 do Cặp 1 cung cấp. Runner đọc nguyên byte, không đổi encoding hay chuẩn hóa nội dung. Dữ liệu thật chưa có trong project; test dùng dữ liệu tổng hợp trong thư mục tạm.

Chạy từ gốc, tự thử import `rle` và `lzw`:

```console
python -m rq2.run_rq2
```

Khi chỉ có Huffman và đủ ba file, runner ghi **9 dòng**. Module RLE/LZW chưa có sẽ được cảnh báo và bỏ qua. File thiếu cũng được cảnh báo theo tên; nếu thiếu cả ba file, runner thoát mã khác 0 và hướng dẫn đặt dữ liệu.

Ví dụ chọn thư mục, ba seed và số lượt đo:

```console
python -m rq2.run_rq2 --data-dir data --out results_rq2_seeds.csv --seeds 1 2 3 --repeats 3
```

Ví dụ cắm module của Cặp 1 (thay tên module cho đúng nơi nhóm bàn giao):

```console
python -m rq2.run_rq2 --codec rle=pair1.rle lzw=pair1.lzw --out results_rq2_all.csv
python -m rq2.run_rq2 --codec rle=pair1.rle lzw=pair1.lzw --seeds 1 2 3 --repeats 5 --out results_rq2_all_seeds.csv
```

Mỗi module phải import được từ gốc và cung cấp `compress(data: bytes) -> bytes`, `decompress(blob: bytes) -> bytes`. Runner luôn dùng Huffman từ `rq2.huffman`; không có cài đặt RLE/LZW thay thế trong repo. Module không import được bị bỏ qua; module import được nhưng thiếu hai hàm hoặc trả sai kiểu làm runner báo lỗi.

Mỗi file sinh `original`, `runs` và một `shuffled` cho mỗi seed, luôn xuất phát từ cùng dữ liệu gốc. Mặc định seed `[1]`; chỉ dòng `shuffled` điền seed. Tổng số dòng kỳ vọng là **số file có × (2 + số seed) × số codec nạp được**: đủ ba file và ba codec cho 27 dòng với một seed, 45 dòng với ba seed. Các lượt `--repeats` không tạo thêm dòng CSV.

Runner kiểm tra toàn bộ SHA-256 sau mỗi lần giải nén, kể cả lượt bộ nhớ. Khi sai, dừng toàn bộ, báo codec/file/trạng thái/seed và không ghi dòng lỗi; các dòng hợp lệ đã ghi trước đó được giữ lại. Cuối lượt chạy in số dòng thực tế/kỳ vọng cùng danh sách codec đã chạy và file/codec bị bỏ qua.

Nếu file đầu ra đã tồn tại, runner từ chối ghi. Chỉ dùng `--overwrite` khi muốn thay kết quả cũ:

```console
python -m rq2.run_rq2 --out results_rq2.csv --overwrite
```

Việc thay file cũ bắt đầu sau khi phép đo đầu tiên thành công; `--out` trùng một file đầu vào luôn bị từ chối. Runner không nối vào kết quả của lần chạy trước.

## Phạm vi bàn giao

Cặp 1 sẽ cung cấp RLE, LZW và pipeline V1. Runner và test tổng hợp đã có; chưa chạy thực nghiệm trên R1 thật vì chưa có dữ liệu và hai codec còn lại. Bốn điểm CSV trong mục 5 của [schema](../common/csv_schema.md) vẫn cần nhóm chốt: tệp riêng/chung, seed, phương pháp đo bộ nhớ/số lần lặp, và tên file R1. Các mặc định hiện tại phục vụ runner theo yêu cầu, không thay cho quyết định chung của nhóm.
