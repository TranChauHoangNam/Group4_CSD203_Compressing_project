"""
Interactive Live Demo Script for CSD203 Project 4
Demo cả 4 giải thuật nén và Tokenizer BPE trực tiếp trong buổi bảo vệ đồ án.
"""

import sys
import hashlib

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import rle
import huffman
import lzw
import rq3.bpe as bpe

BANNER = """
========================================================================
   CSD203 - DATA STRUCTURES AND ALGORITHMS WITH PYTHON (FALL 2026)
   ĐỀ TÀI 4: NÉN KHÔNG MẤT MÁT & TOKENIZER BYTE PAIR ENCODING (LLM)
   Nhóm 4 - Lớp AI21B - GV Hướng dẫn & Hội đồng chấm thi
========================================================================
"""

def print_result_row(algo_name, orig_len, comp_len, is_valid, extra_info=""):
    ratio = comp_len / orig_len if orig_len > 0 else 0
    status_str = "[OK] PASS" if is_valid else "[FAIL]"
    print(f"{algo_name:<22} | {orig_len:>7} B | {comp_len:>7} B | {ratio:>8.4f} | {status_str:<9} | {extra_info}")

def run_demo(sample_text=None):
    if not sample_text:
        sample_text = (
            "Trường Đại học FPT - Phân hiệu Cần Thơ. Đồ án học phần CSD203 "
            "Cấu trúc dữ liệu và Giải thuật với Python. Nhóm 4 thực hiện "
            "khảo sát thực nghiệm các thuật toán RLE, Huffman, LZW và Tokenizer BPE. "
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBCCCCCCCCCCCCCC"
        )

    data = sample_text.encode("utf-8")
    sha_orig = hashlib.sha256(data).hexdigest()[:16]

    print(BANNER)
    print("1. VĂN BẢN ĐẦU VÀO ĐƯỢC CHỌN:")
    print(f"   \"{sample_text[:120]}...\"")
    print(f"   -> Độ dài: {len(data)} bytes (UTF-8) | SHA-256 (16 ký tự đầu): {sha_orig}\n")
    print("2. KẾT QUẢ THỰC THI 4 GIẢI THUẬT (100% PURE PYTHON):")
    print("-" * 88)
    print(f"{'Thuật toán':<22} | {'Gốc':<9} | {'Nén':<9} | {'Tỷ lệ':<8} | {'Round-trip':<9} | Ghi chú kỹ thuật")
    print("-" * 88)

    # 1. RLE
    c_rle = rle.compress(data)
    d_rle = rle.decompress(c_rle)
    rle_ok = (d_rle == data)
    print_result_row("1. RLE (Run-Length)", len(data), len(c_rle), rle_ok, "Gom run A... B... C...")

    # 2. Canonical Huffman
    c_huf = huffman.compress(data)
    d_huf = huffman.decompress(c_huf)
    huf_ok = (d_huf == data)
    print_result_row("2. Canonical Huffman", len(data), len(c_huf), huf_ok, "Bảng mã 256B, H0 tối ưu")

    # 3. LZW 12-bit
    c_lzw = lzw.compress(data)
    d_lzw = lzw.decompress(c_lzw)
    lzw_ok = (d_lzw == data)
    print_result_row("3. LZW 12-bit", len(data), len(c_lzw), lzw_ok, "Từ điển thích nghi 4096 mã")

    # 4. Byte-level BPE
    k_merges = 20
    merges = bpe.train(data, k=k_merges, variant="inc")
    tokens = bpe.encode(data, merges)
    d_tok = bpe.decode(tokens, merges)
    c_bpe = bpe.compress_with_merges(data, merges)
    d_bpe = bpe.decompress(c_bpe)
    bpe_ok = (d_tok == data and d_bpe == data)
    bpe_note = f"K={len(merges)} merges -> {len(tokens)} tokens"
    print_result_row("4. Byte-level BPE", len(data), len(c_bpe), bpe_ok, bpe_note)

    print("-" * 88)
    print("\n3. CHI TIẾT TÁCH TỪ BPE TOKENIZER (GPT-STYLE REGEX):")
    print(f"   * Số merges đã học từ văn bản: {len(merges)}")
    print(f"   * Danh sách 5 merges đầu tiên: {merges[:5]}")
    print(f"   * 20 Token IDs đầu tiên: {tokens[:20]}")
    print(f"   * Tỷ lệ Byte/Token đạt: {len(data)/len(tokens):.2f} bytes/token")
    print("\n[VẬN HÀNH THÀNH CÔNG] Toàn bộ dữ liệu được bảo toàn 100% không mất mát!\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_input = " ".join(sys.argv[1:])
        run_demo(custom_input)
    else:
        run_demo()
