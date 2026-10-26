| ID | Nhận định | file/codec/state | Nguồn | Phép tính | Giá trị |
| --- | --- | --- | --- | --- | --- |
| T001 | Số file | thiết lập/script | MECH:4 | slice(22,23) | 3 |
| T002 | Số state | thiết lập/script | MECH:4 | slice(30,31) | 3 |
| T003 | Số codec | thiết lập/script | MECH:4 | slice(39,40) | 3 |
| T004 | Danh sách seed | thiết lập/script | MECH:4 | slice(56,65) | [1, 2, 3] |
| T005 | Số lần đo theo log | thiết lập/script | MECH:5 | slice(57,58) | 3 |
| T006 | Số dòng CSV | thiết lập/script | MECH:4 | slice(5,7) | 45 |
| T007 | Số cột CSV | thiết lập/script | MECH:4 | slice(14,16) | 28 |
| T008 | Header Huffman | thiết lập/script | MECH:6 | slice(53,56) | 268 |
| T009 | Kích thước file | alice29.txt/huffman/original | CSV:2 | mean(orig_bytes) | 152089 |
| T010 | Kích thước file | kennedy.xls/huffman/original | CSV:17 | mean(orig_bytes) | 1029744 |
| T011 | Kích thước file | v1_test_1mib.txt/huffman/original | CSV:32 | mean(orig_bytes) | 1048576 |
| T012 | Kích thước Huffman bất biến (validator kiểm tra từng dòng) | alice29.txt/huffman/* | CSV:2,5,8,11,14 | mean(comp_bytes) | 87956 |
| T013 | ratio | alice29.txt/huffman/original | CSV:2 | mean(ratio) | 0.578319 |
| T014 | ratio_no_header | alice29.txt/huffman/original | CSV:2 | mean(ratio_no_header) | 0.576557 |
| T015 | Kích thước Huffman bất biến (validator kiểm tra từng dòng) | kennedy.xls/huffman/* | CSV:17,20,23,26,29 | mean(comp_bytes) | 462800 |
| T016 | ratio | kennedy.xls/huffman/original | CSV:17 | mean(ratio) | 0.449432 |
| T017 | ratio_no_header | kennedy.xls/huffman/original | CSV:17 | mean(ratio_no_header) | 0.449172 |
| T018 | Kích thước Huffman bất biến (validator kiểm tra từng dòng) | v1_test_1mib.txt/huffman/* | CSV:32,35,38,41,44 | mean(comp_bytes) | 697307 |
| T019 | ratio | v1_test_1mib.txt/huffman/original | CSV:32 | mean(ratio) | 0.665004 |
| T020 | ratio_no_header | v1_test_1mib.txt/huffman/original | CSV:32 | mean(ratio_no_header) | 0.664748 |
| T021 | ratio | alice29.txt/rle/original | CSV:3 | mean(ratio) | 1.90588 |
| T022 | ratio | alice29.txt/rle/runs | CSV:6 | mean(ratio) | 0.00846873 |
| T023 | ratio | alice29.txt/rle/shuffled | CSV:9,12,15 | mean(ratio) | 1.86267 |
| T024 | ratio | kennedy.xls/rle/original | CSV:18 | mean(ratio) | 1.68177 |
| T025 | ratio | kennedy.xls/rle/runs | CSV:21 | mean(ratio) | 0.00816708 |
| T026 | ratio | kennedy.xls/rle/shuffled | CSV:24,27,30 | mean(ratio) | 1.52551 |
| T027 | ratio | v1_test_1mib.txt/rle/original | CSV:33 | mean(ratio) | 1.98855 |
| T028 | ratio | v1_test_1mib.txt/rle/runs | CSV:36 | mean(ratio) | 0.00808334 |
| T029 | ratio | v1_test_1mib.txt/rle/shuffled | CSV:39,42,45 | mean(ratio) | 1.89491 |
| T030 | Giới hạn count RLE | thiết lập/script | MECH:6 | slice(116,119) | 255 |
| T031 | Header RLE | thiết lập/script | MECH:6 | slice(92,94) | 12 |
| T032 | ratio | alice29.txt/lzw/original | CSV:4 | mean(ratio) | 0.475577 |
| T033 | ratio | alice29.txt/lzw/runs | CSV:7 | mean(ratio) | 0.0326454 |
| T034 | ratio | alice29.txt/lzw/shuffled | CSV:10,13,16 | mean(ratio) | 0.686418 |
| T035 | ratio | alice29.txt/lzw/shuffled | CSV:10,13,16 | min(ratio) | 0.684599 |
| T036 | ratio | kennedy.xls/lzw/original | CSV:19 | mean(ratio) | 0.407137 |
| T037 | ratio | kennedy.xls/lzw/runs | CSV:22 | mean(ratio) | 0.212572 |
| T038 | ratio | kennedy.xls/lzw/shuffled | CSV:25,28,31 | mean(ratio) | 0.544609 |
| T039 | ratio | kennedy.xls/lzw/shuffled | CSV:25,28,31 | min(ratio) | 0.543201 |
| T040 | ratio | v1_test_1mib.txt/lzw/original | CSV:34 | mean(ratio) | 0.492817 |
| T041 | ratio | v1_test_1mib.txt/lzw/runs | CSV:37 | mean(ratio) | 1.04457 |
| T042 | ratio | v1_test_1mib.txt/lzw/shuffled | CSV:40,43,46 | mean(ratio) | 0.820334 |
| T043 | ratio | v1_test_1mib.txt/lzw/shuffled | CSV:40,43,46 | min(ratio) | 0.8184 |
| T044 | Thời gian alice, chỉ để nêu hạn chế | alice29.txt/huffman/original | CSV:2 | mean(comp_ms) | 21.3602 |
| T045 | Tốc độ nén original | kennedy.xls/huffman/original | CSV:17 | mean(comp_kibs) | 4117.9 |
| T046 | Tốc độ nén original | kennedy.xls/rle/original | CSV:18 | mean(comp_kibs) | 5154.22 |
| T047 | Tốc độ nén original | kennedy.xls/lzw/original | CSV:19 | mean(comp_kibs) | 5670.39 |
| T048 | Tốc độ giải nén original | kennedy.xls/huffman/original | CSV:17 | mean(decomp_kibs) | 1690.52 |
| T049 | Tốc độ giải nén original | kennedy.xls/rle/original | CSV:18 | mean(decomp_kibs) | 4345.24 |
| T050 | Tốc độ giải nén original | kennedy.xls/lzw/original | CSV:19 | mean(decomp_kibs) | 9855.05 |
| T051 | Tốc độ nén RLE-runs | kennedy.xls/rle/runs | CSV:21 | mean(comp_kibs) | 15643.9 |
| T052 | Bộ nhớ đỉnh original | kennedy.xls/huffman/original | CSV:17 | mean(peak_mem_kib) | 30272.4 |
| T053 | Bộ nhớ đỉnh original | kennedy.xls/rle/original | CSV:18 | mean(peak_mem_kib) | 3803.72 |
| T054 | Bộ nhớ đỉnh original | kennedy.xls/lzw/original | CSV:19 | mean(peak_mem_kib) | 2697.43 |
| T055 | Tốc độ nén original | v1_test_1mib.txt/huffman/original | CSV:32 | mean(comp_kibs) | 3516.19 |
| T056 | Tốc độ nén original | v1_test_1mib.txt/rle/original | CSV:33 | mean(comp_kibs) | 4497.78 |
| T057 | Tốc độ nén original | v1_test_1mib.txt/lzw/original | CSV:34 | mean(comp_kibs) | 4998.59 |
| T058 | Tốc độ giải nén original | v1_test_1mib.txt/huffman/original | CSV:32 | mean(decomp_kibs) | 1130.2 |
| T059 | Tốc độ giải nén original | v1_test_1mib.txt/rle/original | CSV:33 | mean(decomp_kibs) | 3826.9 |
| T060 | Tốc độ giải nén original | v1_test_1mib.txt/lzw/original | CSV:34 | mean(decomp_kibs) | 7243.36 |
| T061 | Tốc độ nén RLE-runs | v1_test_1mib.txt/rle/runs | CSV:36 | mean(comp_kibs) | 15696.7 |
| T062 | Bộ nhớ đỉnh original | v1_test_1mib.txt/huffman/original | CSV:32 | mean(peak_mem_kib) | 45961.2 |
| T063 | Bộ nhớ đỉnh original | v1_test_1mib.txt/rle/original | CSV:33 | mean(peak_mem_kib) | 4251.85 |
| T064 | Bộ nhớ đỉnh original | v1_test_1mib.txt/lzw/original | CSV:34 | mean(peak_mem_kib) | 2737.01 |
| T065 | Chênh lệch Huffman–H0 nhỏ nhất | */huffman/* | CSV:2,5,8,11,14,17,20,23,26,29,32,35,38,41,44 | min(ratio-h0_ratio) | 0.002748 |
| T066 | Chênh lệch Huffman–H0 lớn nhất | */huffman/* | CSV:2,5,8,11,14,17,20,23,26,29,32,35,38,41,44 | max(ratio-h0_ratio) | 0.007359 |
| T067 | ratio | alice29.txt/lzw/original | CSV:4 | mean(ratio) | 0.475577 |
| T068 | h0_ratio | alice29.txt/huffman/original | CSV:2 | mean(h0_ratio) | 0.57096 |
| T069 | ratio_no_header | alice29.txt/huffman/original | CSV:2 | mean(ratio_no_header) | 0.576557 |
| T070 | ratio | alice29.txt/lzw/shuffled | CSV:10,13,16 | mean(ratio) | 0.686418 |
| T071 | ratio | alice29.txt/huffman/shuffled | CSV:8,11,14 | mean(ratio) | 0.578319 |
| T072 | ratio | kennedy.xls/lzw/original | CSV:19 | mean(ratio) | 0.407137 |
| T073 | h0_ratio | kennedy.xls/huffman/original | CSV:17 | mean(h0_ratio) | 0.446684 |
| T074 | ratio_no_header | kennedy.xls/huffman/original | CSV:17 | mean(ratio_no_header) | 0.449172 |
| T075 | ratio | kennedy.xls/lzw/shuffled | CSV:25,28,31 | mean(ratio) | 0.544609 |
| T076 | ratio | kennedy.xls/huffman/shuffled | CSV:23,26,29 | mean(ratio) | 0.449432 |
| T077 | ratio | v1_test_1mib.txt/lzw/original | CSV:34 | mean(ratio) | 0.492817 |
| T078 | h0_ratio | v1_test_1mib.txt/huffman/original | CSV:32 | mean(h0_ratio) | 0.66091 |
| T079 | ratio_no_header | v1_test_1mib.txt/huffman/original | CSV:32 | mean(ratio_no_header) | 0.664748 |
| T080 | ratio | v1_test_1mib.txt/lzw/shuffled | CSV:40,43,46 | mean(ratio) | 0.820334 |
| T081 | ratio | v1_test_1mib.txt/huffman/shuffled | CSV:38,41,44 | mean(ratio) | 0.665004 |
| T082 | ratio | alice29.txt/lzw/runs | CSV:7 | mean(ratio) | 0.0326454 |
| T083 | ratio | alice29.txt/lzw/original | CSV:4 | mean(ratio) | 0.475577 |
| T084 | Chênh lệch LZW runs-original | alice29.txt/script | MECH:11 | slice(94,103) | -0.442932 |
| T085 | ratio | kennedy.xls/lzw/runs | CSV:22 | mean(ratio) | 0.212572 |
| T086 | ratio | kennedy.xls/lzw/original | CSV:19 | mean(ratio) | 0.407137 |
| T087 | Chênh lệch LZW runs-original | kennedy.xls/script | MECH:17 | slice(160,169) | -0.194565 |
| T088 | Vị trí đầy từ điển runs | kennedy.xls/script | MECH:17 | slice(35,41) | 887662 |
| T089 | Phần trăm vị trí đầy, định dạng script | kennedy.xls/script | MECH:17 | slice(43,45) | 86 |
| T090 | Phần trăm sau khi đầy | kennedy.xls/script | MECH:17 | slice(57,59) | 14 |
| T091 | ratio | v1_test_1mib.txt/lzw/runs | CSV:37 | mean(ratio) | 1.04457 |
| T092 | ratio | v1_test_1mib.txt/lzw/original | CSV:34 | mean(ratio) | 0.492817 |
| T093 | Chênh lệch LZW runs-original | v1_test_1mib.txt/script | MECH:23 | slice(159,167) | 0.551753 |
| T094 | Vị trí đầy từ điển runs | v1_test_1mib.txt/script | MECH:23 | slice(35,41) | 319103 |
| T095 | Phần trăm vị trí đầy, định dạng script | v1_test_1mib.txt/script | MECH:23 | slice(43,45) | 30 |
| T096 | Phần trăm sau khi đầy | v1_test_1mib.txt/script | MECH:23 | slice(57,59) | 70 |
| T097 | Dung lượng từ điển LZW | thiết lập/script | MECH:6 | slice(69,73) | 4096 |
| T098 | Tổng bình phương xác suất byte | alice29.txt/script | MECH:9 | slice(13,19) | 0.0687 |
| T099 | Dự đoán RLE shuffled | alice29.txt/script | MECH:9 | slice(68,74) | 1.8626 |
| T100 | ratio | alice29.txt/rle/shuffled | CSV:9,12,15 | mean(ratio) | 1.86267 |
| T101 | Sai lệch dự đoán RLE shuffled | alice29.txt/script | MECH:9 | slice(99,110) | 8.60558e-05 |
| T102 | Dự đoán RLE original | alice29.txt/script | MECH:10 | slice(54,60) | 1.9058 |
| T103 | ratio | alice29.txt/rle/original | CSV:3 | mean(ratio) | 1.90588 |
| T104 | Sai lệch dự đoán RLE original | alice29.txt/script | MECH:10 | slice(112,123) | 7.48464e-05 |
| T105 | Tổng bình phương xác suất byte | kennedy.xls/script | MECH:15 | slice(13,19) | 0.2369 |
| T106 | Dự đoán RLE shuffled | kennedy.xls/script | MECH:15 | slice(68,74) | 1.5262 |
| T107 | ratio | kennedy.xls/rle/shuffled | CSV:24,27,30 | mean(ratio) | 1.52551 |
| T108 | Sai lệch dự đoán RLE shuffled | kennedy.xls/script | MECH:15 | slice(99,111) | -0.000694301 |
| T109 | Dự đoán RLE original | kennedy.xls/script | MECH:16 | slice(54,60) | 1.6818 |
| T110 | ratio | kennedy.xls/rle/original | CSV:18 | mean(ratio) | 1.68177 |
| T111 | Sai lệch dự đoán RLE original | kennedy.xls/script | MECH:16 | slice(112,123) | 1.41461e-05 |
| T112 | Tổng bình phương xác suất byte | v1_test_1mib.txt/script | MECH:21 | slice(13,19) | 0.0525 |
| T113 | Dự đoán RLE shuffled | v1_test_1mib.txt/script | MECH:21 | slice(68,74) | 1.8950 |
| T114 | ratio | v1_test_1mib.txt/rle/shuffled | CSV:39,42,45 | mean(ratio) | 1.89491 |
| T115 | Sai lệch dự đoán RLE shuffled | v1_test_1mib.txt/script | MECH:21 | slice(99,111) | -0.000134406 |
| T116 | Dự đoán RLE original | v1_test_1mib.txt/script | MECH:22 | slice(55,61) | 1.9885 |
| T117 | ratio | v1_test_1mib.txt/rle/original | CSV:33 | mean(ratio) | 1.98855 |
| T118 | Sai lệch dự đoán RLE original | v1_test_1mib.txt/script | MECH:22 | slice(113,124) | 1.50726e-05 |
| T119 | Ngưỡng đối chiếu RLE | thiết lập/script | MECH:2 | slice(54,58) | 0.05 |
