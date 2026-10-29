# BẢNG PHÂN CÔNG NHIỆM VỤ VÀ MINH BẠCH ĐÓNG GÓP
## Đồ án Nhóm môn CSD203 — Cấu trúc Dữ liệu và Giải thuật với Python
### Lớp: AI21B — Học kỳ: Fall 2026 (FA26) — Nhóm 4
**Đề tài 4:** Nén văn bản và Tokenizer mô hình ngôn ngữ lớn (Byte Pair Encoding - BPE)

---

## 1. Thông tin Chung về Nhóm

| STT | Họ và Tên | Mã Sinh Viên (MSSV) | Vai trò trong Nhóm | Cặp Chuyên trách | Phụ trách Nghiên cứu |
|:---:|---|:---:|---|:---:|:---:|
| 1 | **Trần Châu Hoàng Nam** | **QE210145** | **Nhóm trưởng (Leader)** | Cặp 2 | **RQ2** (Độ nhạy Điều kiện) |
| 2 | **Hoàng Đức Khánh** | **SE180114** | Thành viên | Cặp 2 | **RQ2** (Độ nhạy Điều kiện) |
| 3 | **Nguyễn Trí Viễn** | **QE210041** | Thành viên | Cặp 1 | **RQ1** (Định luật Tải) |
| 4 | **Phạm Minh Tiến** | **QE210079** | Thành viên | Cặp 1 | **RQ1** (Định luật Tải) |
| 5 | **Trương Đình Tân** | **QE210065** | Thành viên | Cặp 3 | **RQ3** (Ablation Study BPE) |
| 6 | **Dương Quốc Thịnh** | **QE210121** | Thành viên | Cặp 3 | **RQ3** (Ablation Study BPE) |

---

## 2. Phân công Chi tiết theo Từng Cặp (Pair Programming)

Quy định thực hiện: Mỗi cặp gồm 2 thành viên phụ trách trọn vẹn một module và câu hỏi nghiên cứu (RQ). Vai trò Cài đặt (Implementer) và Kiểm thử / Đánh giá (Tester/Reviewer) được phân định rõ ràng và luân phiên trách nhiệm.

### Cặp 1: Phụ trách RQ1 (Định luật Tải — Scalability của RLE, Huffman, LZW)
* **Câu hỏi nghiên cứu:** Đánh giá độ phức tạp thời gian tiệm cận $O(\cdot)$, tỷ lệ nén và đỉnh bộ nhớ của các thuật toán giáo trình khi quy mô dữ liệu $N$ tăng dần từ $256\text{ KiB}$ đến $4096\text{ KiB}$.

| Thành viên | Vai trò chính | Nhiệm vụ kỹ thuật cụ thể | File / Module phụ trách |
|---|---|---|---|
| **Nguyễn Trí Viễn**<br>(QE210041) | **Implementer**<br>(Cài đặt thuật toán) | • Cài đặt thuật toán nén và giải nén Run-Length Encoding (RLE) theo byte run.<br>• Cài đặt thuật toán LZW (Lempel–Ziv–Welch) Pure Python với từ điển cố định 4096 mã 12-bit.<br>• Cài đặt định dạng đóng gói luồng byte nhị phân trong `container.py`. | • `rle.py`<br>• `lzw.py`<br>• `container.py` |
| **Phạm Minh Tiến**<br>(QE210079) | **Tester / Reviewer & Benchmark Lead** | • Xây dựng bộ sinh dữ liệu tổng hợp C1 (Uniform), C2 (Binomial), C3 (Periodic) với 3 seed ngẫu nhiên qua 5 kích thước.<br>• Thiết lập pipeline đo đạc tự động `run_rq1.py` độc lập tiến trình.<br>• Viết unit test kiểm tra round-trip SHA-256 cho RLE và LZW; tổng hợp và xử lý dữ liệu CSV RQ1. | • `gen_synthetic.py`<br>• `run_rq1.py`<br>• `rq1/analyze_rq1.py`<br>• `results/results_rq1.csv` |

---

### Cặp 2: Phụ trách RQ2 (Độ nhạy Điều kiện — Condition Sensitivity & Huffman Chính tắc)
* **Câu hỏi nghiên cứu:** Giữ cố định quy mô $1\text{ MiB}$ trên ngữ liệu Canterbury R1, thay đổi cấu trúc dữ liệu qua 3 trạng thái (gốc, gom run, xáo trộn ngẫu nhiên) để so sánh hiệu năng nén của Huffman so với mốc entropy lý thuyết Shannon $H_0$.

| Thành viên | Vai trò chính | Nhiệm vụ kỹ thuật cụ thể | File / Module phụ trách |
|---|---|---|---|
| **Hoàng Đức Khánh**<br>(SE180114) | **Implementer**<br>(Cài đặt thuật toán) | • Cài đặt giải thuật Huffman chính tắc (Canonical Huffman) 2 lượt: lượt 1 đếm tần suất và tính độ dài bit mã, lượt 2 ghi bitstream.<br>• Thiết kế cấu trúc header chuẩn: magic `HUF1`, 8 byte kích thước gốc, và bảng 256 byte độ dài mã (dựng lại bảng mã trực tiếp từ độ dài, không cần serialize cây nhị phân).<br>• Đảm bảo mã nguồn Pure Python, không sử dụng thư viện sort có sẵn. | • `rq2/huffman.py`<br>• `huffman.py` (chuyển tiếp)<br>• `rq2/tests/test_huffman.py` |
| **Trần Châu Hoàng Nam**<br>(QE210145)<br>*(Leader)* | **Tester / Reviewer & Theory/Ablation Lead** | • Cài đặt module tính entropy bậc 0: $H_0 = -\sum p_i \log_2 p_i$ trên histogram byte.<br>• Cài đặt 2 công cụ đảo thứ tự byte bảo toàn histogram: Counting Sort (gom byte thành run) và Fisher–Yates Shuffle (xáo trộn ngẫu nhiên).<br>• Thiết kế runner `run_rq2.py` chạy Huffman và các codec đối chứng trên 3 trạng thái của R1; phân tích đối chiếu tỷ lệ nén so với mốc $H_0$. | • `rq2/h0.py`<br>• `rq2/reorder.py`<br>• `rq2/run_rq2.py`<br>• `rq2/analyze_rq2.py`<br>• `results/results_rq2.csv` |

---

### Cặp 3: Phụ trách RQ3 (Ablation Study BPE Tokenizer họ GPT)
* **Câu hỏi nghiên cứu:** Đánh giá thuật toán BPE Tokenizer hiện đại trên ngữ liệu song ngữ Anh - Việt (E1/V1); bóc tách đóng góp của các kỹ thuật tối ưu hóa qua 3 biến thể huấn luyện (`naive`, `noheap`, `inc`).

| Thành viên | Vai trò chính | Nhiệm vụ kỹ thuật cụ thể | File / Module phụ trách |
|---|---|---|---|
| **Dương Quốc Thịnh**<br>(QE210121) | **Implementer**<br>(Tokenizer & Pre-tokenization) | • Cài đặt cơ chế Pre-tokenization bằng biểu thức chính quy byte `rb" ?[^\s]+|\s+"` theo chuẩn GPT.<br>• Thiết kế tách từ thành các phân đoạn (segments) độc lập có trọng số tần suất.<br>• Cài đặt định dạng đóng gói file bảng merges 12-bit và payload nén BPE; viết bộ test ca biên (edge cases) cho tokenizer. | • `rq3/bpe.py` (Tokenizer)<br>• `common/tests/test_edge_*.py`<br>• `docs/manifest.json` |
| **Trương Đình Tân**<br>(QE210065) | **Implementer & Benchmark Lead**<br>(Training Variants & Cache) | • Cài đặt 3 biến thể huấn luyện BPE phục vụ Ablation Study: `naive` ($O(N \cdot K)$), `noheap` (danh sách liên kết kép + inverted index), và `inc` (bộ đếm tăng dần + Max-Heap lazy update).<br>• Cài đặt cơ chế mã hóa có bộ nhớ đệm (cache token) để tăng tốc độ nén.<br>• Thiết lập kịch bản đo đạc tự động `run_rq3.py` ma trận $2 \times 2$ (huấn luyện trên V1/E1, kiểm tra trên V1/E1) với các mức $K \in \{256, 1024, 3840\}$. | • `rq3/bpe.py` (Huấn luyện)<br>• `rq3/run_rq3.py`<br>• `rq3/tests/test_variants.py`<br>• `results/results_rq3.csv` |

---

## 3. Cơ chế Review Chéo và Trách nhiệm Chéo (Cross-Review)

Nhằm đảm bảo tính khách quan và tuân thủ Mục 4 Quy chế Đồ án, các cặp thực hiện review chéo mã nguồn và bộ kiểm thử lẫn nhau:
* **Cặp 1 review Cặp 2:** Phạm Minh Tiến và Nguyễn Trí Viễn kiểm tra tính bảo toàn histogram của các hàm hoán vị trong `rq2/reorder.py` và kiểm thử độ dài bit của `rq2/huffman.py`.
* **Cặp 2 review Cặp 3:** Trần Châu Hoàng Nam và Hoàng Đức Khánh review độc lập thuật toán heap lazy update trong `rq3/bpe.py`, kiểm tra tính thuần Python (Pure Python không dùng `list.sort()`) và xây dựng công cụ kiểm tra độc lập `tools/verify_row.py`.
* **Cặp 3 review Cặp 1:** Trương Đình Tân và Dương Quốc Thịnh chạy kiểm thử đối chiếu giữa bộ sinh `gen_synthetic.py` và các ca biên đặc biệt của LZW và RLE.

---

## 4. Tóm tắt Đóng góp theo Commit Log

Toàn bộ các đóng góp kỹ thuật đã được tích hợp thông qua các Pull Request chính thức trên Git:
* **PR #1 (`rq2-pair2`):** Cặp 2 hoàn thiện module $H_0$, thuật toán hoán vị Fisher-Yates / Counting Sort, và thuật toán Huffman chính tắc 2 lượt không serialize cây.
* **PR #2 & #3 (`rq3-pair3`):** Cặp 3 hoàn thiện pre-tokenization regex GPT, 3 biến thể huấn luyện BPE (`naive`, `noheap`, `inc`), định dạng container 12-bit và bộ runner RQ3 ma trận song ngữ.
* **PR #4, #5, #6, #7 (`polish-rq1`):** Cặp 1 và nhóm trưởng hoàn thiện dữ liệu đo đạc cùng máy cho 150 cấu hình RQ1, bộ sinh C1-C3 và báo cáo RQ1.
* **PR #8 (`reg-no-lib-sort`):** Loại bỏ toàn bộ lời gọi `sort/sorted` thư viện khỏi Huffman và BPE, bổ sung bài kiểm tra AST guard tự động `test_no_library_sort.py`.
* **PR #9 (`reg-status-column`):** Chuẩn hóa schema cột `status` (`ok`, `timeout`, `crash`) và phát triển công cụ tự động tái lập thực nghiệm `tools/verify_row.py`.

---

## 5. Xác nhận của Thành viên Nhóm

Các thành viên cam kết nội dung phân công phản ánh trung thực quá trình làm việc thực tế, đảm bảo 100% mã nguồn được cài đặt bằng Python thuần và nắm vững kiến thức để tham gia buổi vấn đáp độc lập trước Giảng viên.

*Ngày hoàn thành tài liệu: 29/10/2026*

| Thành viên | Chữ ký xác nhận |
|---|:---:|
| **Trần Châu Hoàng Nam** (Leader) | *(Đã ký)* |
| **Hoàng Đức Khánh** | *(Đã ký)* |
| **Nguyễn Trí Viễn** | *(Đã ký)* |
| **Phạm Minh Tiến** | *(Đã ký)* |
| **Trương Đình Tân** | *(Đã ký)* |
| **Dương Quốc Thịnh** | *(Đã ký)* |

