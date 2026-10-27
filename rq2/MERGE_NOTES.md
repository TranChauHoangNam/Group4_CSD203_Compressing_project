> Hồ sơ lịch sử của lần merge ban đầu. Các mô tả decoder chấp nhận padding/bảng mã sai bên dưới đã được thay thế trong đợt sửa 2026-10-27; xem README hiện tại và các regression test. Không dùng các giới hạn lịch sử này làm đặc tả hiện hành.

## 1. Files thêm mới (đường dẫn + lý do)

- `.gitignore`: bỏ qua `__pycache__/`, `*.pyc`, `pytest-cache-files-*/`, `.pytest_cache/`.
- `rq2/tests/reference/__init__.py`: đánh dấu package đối chứng chỉ dùng trong test.
- `rq2/tests/reference/partner_original.py`: copy bản partner, thêm docstring đúng yêu cầu, bỏ comment mở đầu demo và khối `if __name__ == "__main__":` (dòng 191–220 của file gốc). Giữ nguyên imports và logic tất cả hàm; chỉ dùng đối chiếu H0 và đảo byte trong test.
- `rq2/tests/test_cross_check.py`: thêm 32 test: 7 ca × 4 nhóm đối chiếu (Huffman, H0, counting sort, histogram Fisher–Yates), cộng 2 ca lỗi × 2 API giải nén. Mẫu ngẫu nhiên 64 KiB dùng seed 203, không dùng `os.urandom`; test Fisher–Yates của partner lưu/khôi phục trạng thái RNG toàn cục.
- `rq2/MERGE_NOTES.md`: lưu báo cáo merge này.

## 2. Files đã sửa (đường dẫn + mô tả thay đổi + hàm bị ảnh hưởng)

- `rq2/huffman.py`: dựng lại từ phần Huffman của partner sau khi di chuyển bản cũ. Chỉ chứa phần Huffman, API bọc và tiện ích tương thích; không chứa `calculate_h0`, `counting_sort_bytes`, `fisher_yates_shuffle` hay demo.
- `rq2/tests/reference/huffman_alt.py`: sau di chuyển, thay docstring bằng “Cài đặt Huffman độc lập, chỉ dùng để đối chứng với bản chính của partner”; đổi `from .h0 import histogram` thành `from rq2.h0 import histogram` để import đúng từ vị trí mới. Không đổi hàm hay thuật toán.
- `rq2/tests/test_huffman.py`: thêm import `huffman_alt`; sửa docstring của `test_ties_and_determinism` vì mô tả tie-break cũ không còn đúng cho bản chính. Điều chỉnh `test_invalid_table` và `test_invalid_payload_and_padding`: giữ toàn bộ ca kiểm tra từ chối trên bản đối chứng, thêm xác nhận hành vi bản chính; không bỏ test. Bảng `[1, 1, 1]` cho A/B/C được bản chính giải thành `BAB`; bảng rỗng với độ dài gốc khác 0 vẫn phải báo lỗi. Payload không giải được đủ byte vẫn báo lỗi; padding khác 0 và byte thừa được partner bỏ qua sau khi đủ độ dài gốc.
- `rq2/README.md`: cập nhật sở hữu (Huffman: partner; H0 và đảo byte: người dùng), API, cách chạy test từ gốc, vai trò `tests/reference/`, thuật toán thực tế của partner, phạm vi kiểm tra lỗi và seed trong test đối chiếu. Không dùng đường dẫn tuyệt đối; không có hàm mã nguồn bị ảnh hưởng.

Chi tiết từng dòng/hàm thay đổi so với phần Huffman trong `Thuật toán Canonical Huffman.py` (số dòng đích thuộc `rq2/huffman.py`):

| Dòng gốc → dòng đích | Thay đổi thực tế |
| --- | --- |
| Thêm dòng 1, 3 | Docstring module và `from __future__ import annotations` để hoãn đánh giá type hint. |
| Thêm dòng 5, 7, 9–10 | `import hashlib`, tái xuất `histogram` từ `.h0`, `MAGIC = b"HUF1"`, `HEADER_SIZE = 4 + 8 + 256`. Không đổi literal header trong code partner. |
| `Node`, thêm dòng 16 | Thêm docstring lớp. |
| 36 → 18, `Node.__init__` | Thêm hint `symbol: int \| None`, `freq: int`, `-> None`; giữ nguyên thân hàm. |
| 42 → 24, `Node.__lt__` | Thêm hint `other: Node`, `-> bool`; giữ nguyên phép so sánh. |
| 47 → 29, `build_code_lengths` | Đổi hint kết quả `list` thành `list[int]`; giữ nguyên thân hàm, kể cả hàm lồng `get_lengths`. |
| 100 → 82, `generate_canonical_codes` | Đổi hint `lengths: list` thành `list[int]`, kết quả `dict` thành `dict[int, str]`; giữ nguyên thân hàm. |
| `huffman_decompress`, thêm dòng 139–141 | Trước đọc độ dài gốc, thêm `if len(compressed_data) < HEADER_SIZE:` và `raise ValueError("Truncated Huffman header")`. Dòng 141 là dòng trống. |
| `huffman_decompress`, thêm dòng 172–174 | Trước trả kết quả, thêm `if len(decoded_bytes) != original_length:` và `raise ValueError("Decoded length does not match original length (truncated Huffman payload)")`. Dòng 174 là dòng trống. |
| Thêm dòng 178–185 | Hai hàm bọc có type hint/docstring: `compress` gọi `huffman_compress`; `decompress` gọi `huffman_decompress`. |
| Thêm dòng 188–190 | Khôi phục `output_check` từ API cũ: SHA-256, lấy 16 ký tự hex đầu; có type hint/docstring. |

`huffman_compress` giữ nguyên toàn bộ chữ ký, docstring và thân hàm. Kiểm tra magic và thông điệp lỗi của `huffman_decompress` giữ nguyên. Các hàm công khai khác của partner vốn đã có docstring nên giữ lại. Không đổi tên biến, cấu trúc cây, quy tắc phá hòa, tạo mã hay đóng gói bit. Các thay đổi logic duy nhất trong phần Huffman của partner là hai kiểm tra độ dài trên; đã đối chiếu AST để xác nhận.

API được test cũ import trước merge và vẫn dùng được:

- `rq2.huffman`: `HEADER_SIZE`, `compress`, `decompress`, `output_check`.
- `rq2.h0`: `entropy_h0`, `h0_ratio`, `histogram`.
- `rq2.reorder`: `counting_sort_runs`, `fisher_yates`.

Ngoài danh sách import thực tế, vẫn giữ `rq2.huffman.MAGIC` và `rq2.huffman.histogram`; các tiện ích/hằng số này không có trong bản partner nên được bổ sung để tương thích. `rq2/h0.py`, `rq2/reorder.py`, `rq2/tests/test_h0.py`, `rq2/tests/test_reorder.py`, `pytest.ini` và file partner gốc không bị sửa; đã kiểm tra SHA-256 so với trước merge.

## 3. Files đã xóa hoặc di chuyển

- Di chuyển `rq2/huffman.py` cũ sang `rq2/tests/reference/huffman_alt.py`, rồi tạo bản chính mới tại đường dẫn cũ. Không xóa bản Huffman độc lập.
- Xóa các thư mục cache và nội dung: `rq2/__pycache__/`, `rq2/tests/__pycache__/`, `rq2/tests/reference/__pycache__/`, `pytest-cache-files-09iq1wxj/`. Thư mục cuối cần chạy lại với quyền ngoài sandbox sau lỗi truy cập; đã xóa thành công.
- Không xóa file nguồn nào. File `Thuật toán Canonical Huffman.py` gốc được giữ nguyên, gồm cả demo; demo chỉ bị bỏ trong bản copy đối chứng và không đưa vào bản chính.
- Không tìm thấy `results_schema.py` trong project, nên không di chuyển và không tạo `common/` hay `common/__init__.py`.

## 4. Lỗi tìm thấy và cách sửa

- Partner, `huffman_decompress`: header thiếu có thể trả dữ liệu rỗng hoặc phát sinh lỗi ngoài ý muốn khi đọc bảng mã. Thêm kiểm tra đủ 268 byte, báo `ValueError` trước khi đọc độ dài gốc. Test mọi độ dài 0–267 cho cả hai API giải nén.
- Partner, `huffman_decompress`: payload bị cắt có thể trả dữ liệu ngắn mà không báo lỗi. Thêm kiểm tra số byte giải mã khớp header; test hồi quy cắt 30 byte cuối cho cả hai API. Các test cắt từng prefix và thiếu byte cuối cũ vẫn chạy.
- Partner, magic: **đã đúng, chỉ thêm test** qua các ca header thiếu mới; giữ test magic sai cũ và không đổi kiểm tra magic.
- Người dùng, H0: **đã đúng, chỉ thêm test** đối chiếu sai số tuyệt đối dưới `1e-12` trên cả 7 ca.
- Người dùng, counting sort: **đã đúng, chỉ thêm test** đối chiếu đầu ra. Đã đọc mã xác nhận sử dụng histogram 256 ô, không gọi `sorted()`.
- Người dùng, Fisher–Yates: **đã đúng, chỉ thêm test** bảo toàn histogram trên 7 ca. Hàm đã nhận `seed` và dùng `random.Random(seed)`; test cũ xác nhận tái lập và không tác động RNG toàn cục.
- Hai test cũ đòi hành vi từ chối dữ liệu hỏng nghiêm ngặt hơn partner: điều chỉnh như mục 2, giữ kiểm tra trên bản đối chứng và ghi nhận hành vi bản chính. Không thêm kiểm tra ngoài phạm vi Bước 3 vào thuật toán partner.

## 5. Điểm đáng ngờ đã ghi nhận nhưng KHÔNG sửa

- `Node.__lt__` coi `symbol=None` và byte 0 cùng là 0; các nút trong cùng tần suất không có khóa phụ phân biệt. Giữ nguyên theo yêu cầu sở hữu.
- Partner không kiểm tra bảng độ dài vượt Kraft. Test bảng A/B/C đều dài 1 cho thấy có thể trả dữ liệu sai nhưng đủ độ dài, nên kiểm tra độ dài mới không phát hiện trường hợp này.
- Partner không xác thực padding khác 0 hay byte thừa sau khi đủ độ dài gốc; header có độ dài gốc 0 trả `b""` mà không kiểm tra bảng mã/payload còn lại. Không tự thêm kiểm tra.
- Comment trong `build_code_lengths` nhắc độ dài tối đa thường 16 hoặc 32 bit, nhưng code không áp giới hạn đó; giữ nguyên comment và thuật toán.
- Partner tạo toàn bộ chuỗi ký tự bit khi nén/giải nén, có thể tốn bộ nhớ với dữ liệu lớn; không tối ưu lại.
- `partner_original.counting_sort_bytes` thực tế gọi `sorted()`, và `fisher_yates_shuffle` dùng RNG toàn cục, không nhận seed. Giữ nguyên để đối chứng; thực nghiệm dùng bản chính của người dùng.

## 6. Khác biệt giữa bản chính và bản đối chứng

- Huffman: bản chính dùng heap các `Node` và so `(freq, symbol or 0)` thông qua `__lt__`; bản đối chứng dùng tuple `(tần suất, byte nhỏ nhất trong cây con, chỉ số nút)`. Tie-break có thể cho bảng độ dài khác nhau; test chỉ đòi giải nén chéo đúng và kích thước bằng nhau, không đòi blob giống từng byte.
- Hai bản cùng tạo mã chính tắc theo `(độ dài, giá trị byte)`. Bản chính biểu diễn mã bằng chuỗi bit; bản đối chứng dùng số nguyên và độ dài, đóng gói qua bộ đệm bit.
- Định dạng giữ nguyên: `HUF1` 4 byte + độ dài gốc 8 byte big-endian + bảng 256 byte + payload MSB first, đệm 0 ở byte cuối. Không thêm byte padding-info. Rỗng có header 268 byte; một loại byte có mã 0 dài 1 bit ở cả hai bản.
- Bản đối chứng kiểm tra Kraft, mã không hợp lệ, padding và byte thừa nghiêm ngặt hơn bản chính; chi tiết hành vi giữ nguyên ở mục 5.
- H0: bản chính dùng histogram 256 ô, bản đối chứng dùng `Counter`; thứ tự cộng số thực khác nhau, kiểm tra sai số tuyệt đối dưới `1e-12`.
- Đảo byte: bản chính counting sort dùng histogram, đối chứng dùng `sorted()` nhưng đầu ra phải giống hệt. Fisher–Yates chính dùng RNG riêng có seed; đối chứng dùng RNG toàn cục. Chỉ so histogram hai kết quả, không yêu cầu cùng hoán vị.
- Các file trong `tests/reference/` chỉ được import từ test; thực nghiệm sử dụng `rq2.huffman`, `rq2.h0`, `rq2.reorder`.

## 7. Kết quả test trước và sau (số test đạt)

- Trước merge, `python -m pytest -q`: **41 passed**.
- Trong bước dựng file có một lần lỗi collection do lệnh tạo file gặp lỗi mã hóa tiếng Việt qua PowerShell trước khi tạo xong `rq2/huffman.py`; đã khắc phục cách truyền Unicode và hoàn tất file.
- Sau dựng bản chính, trước điều chỉnh test: **39 passed, 2 failed**; hai lỗi là `test_invalid_table` và `test_invalid_payload_and_padding`, do khác hành vi nêu ở mục 2, không do định dạng HUF1 hay giải mã chéo.
- Chạy riêng ba file test cũ sau điều chỉnh: **41 passed**, không bỏ hoặc skip test.
- Chạy toàn bộ cuối cùng từ gốc với `python -m pytest -q`: **73 passed** = 41 test cũ + 32 test mới. Đặt `PYTHONDONTWRITEBYTECODE=1` cho lần chạy cuối để không tạo lại cache vừa dọn.
- Kiểm tra bổ sung: AST bản đối chứng partner giữ nguyên phần thực thi ngoài demo; AST phần Huffman chính giữ nguyên ngoài type hint/docstring và hai kiểm tra được cho phép. Bản Huffman cũ chỉ đổi docstring/import sau di chuyển. SHA-256 xác nhận các file được giữ nguyên như mục 2.

## 8. Việc còn lại chưa làm (script chạy 27 lượt RQ2 cần RLE, LZW và V1 từ Cặp 1)

- Chưa viết/chạy script thực nghiệm 27 lượt RQ2 (`3 file R1 × 3 trạng thái × 3 codec`), chưa đo hiệu năng hay ghi CSV kết quả; cần RLE, LZW và V1 từ Cặp 1.
- Không chạy `git commit` hoặc `git push`; thay đổi nằm trong cây làm việc.
