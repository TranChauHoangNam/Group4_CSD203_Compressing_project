"""Huffman chính tắc của partner, bản chính dùng cho thực nghiệm RQ2."""

from __future__ import annotations

import hashlib

from .h0 import histogram

MAGIC = b"HUF1"
HEADER_SIZE = 4 + 8 + 256


# XÂY DỰNG HUFFMAN CÂY VÀ ĐỘ DÀI MÃ

class Node:
    """Nút cây Huffman; giữ nguyên quy tắc phá hòa của partner."""

    def __init__(self, symbol: int | None = None, freq: int = 0) -> None:
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other: Node) -> bool:
        if self.freq == other.freq:
            return (self.symbol or 0) < (other.symbol or 0)
        return self.freq < other.freq

def build_code_lengths(data: bytes) -> list[int]:
    """Lượt 1: Đếm tần suất, dựng cây Huffman và trả về mảng 256 phần tử chứa độ dài mã."""
    import heapq
    freqs = [0] * 256
    for b in data:
        freqs[b] += 1

    # Tạo danh sách các nút ban đầu (chỉ với các ký tự xuất hiện ít nhất 1 lần)
    # Chuẩn hóa đủ 256 độ dài mã cho header.
    # Trường hợp dữ liệu rỗng hoặc chỉ có 1 loại byte.
    if len(data) == 0:
        return [0] * 256

    heap = []
    for i in range(256):
        if freqs[i] > 0:
            heapq.heappush(heap, Node(symbol=i, freq=freqs[i]))

    # Nếu dữ liệu chỉ có đúng 1 loại ký tự duy nhất
    if len(heap) == 1:
        node = heapq.heappop(heap)
        lengths = [0] * 256
        lengths[node.symbol] = 1
        return lengths

    # Dựng cây Huffman
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = Node(freq=left.freq + right.freq)
        parent.left = left
        parent.right = right
        heapq.heappush(heap, parent)

    root = heap[0]
    lengths = [0] * 256

    def get_lengths(node, depth):
        if node is None:
            return
        if node.symbol is not None:
            lengths[node.symbol] = depth
            return
        get_lengths(node.left, depth + 1)
        get_lengths(node.right, depth + 1)

    get_lengths(root, 0)
    
    # Giới hạn độ dài mã tối đa trong Canonical Huffman thường là <= 16 hoặc 32 bit, 
    return lengths

# CANONICAL HUFFMAN: TẠO BẢNG Mã & MÃ HÓA (LƯỢT 2)

def generate_canonical_codes(lengths: list[int]) -> dict[int, str]:
    """Từ mảng độ dài mã (256 byte), dựng lại bảng mã chính tắc (Canonical Huffman Codes)."""
    # Sắp xếp các ký tự theo (độ dài mã tăng dần, sau đó theo giá trị ký tự tăng dần)
    symbols = [(i, lengths[i]) for i in range(256) if lengths[i] > 0]
    symbols.sort(key=lambda x: (x[1], x[0]))

    codes = {}
    current_code = 0
    current_length = symbols[0][1] if symbols else 0

    for symbol, length in symbols:
        # Dịch trái khi độ dài mã tăng lên
        current_code <<= (length - current_length)
        current_length = length
        if current_code >= (1 << length):
            raise ValueError("Oversubscribed Huffman code lengths")
        
        # Biểu diễn mã dưới dạng chuỗi bit (ví dụ: '0101')
        codes[symbol] = format(current_code, f'0{length}b')
        current_code += 1

    return codes

def huffman_compress(data: bytes) -> bytes:
    """Nén dữ liệu dùng Canonical Huffman 2 lượt."""
    if not data:
        return b'HUF1' + (0).to_bytes(8, 'big') + b'\x00' * 256

    #1 Tính độ dài mã cho từng byte
    lengths = build_code_lengths(data)
    code_lengths_bytes = bytes(lengths)

    # Dựng bảng mã chính tắc từ độ dài mã
    canonical_codes = generate_canonical_codes(lengths)

    #2 Duyệt lại dữ liệu để mã hóa thành chuỗi bit
    bit_string = "".join(canonical_codes[b] for b in data)

    # Padding chuỗi bit thành bội số của 8 (để đóng gói thành bytes)
    padding_len = (8 - len(bit_string) % 8) % 8
    bit_string += '0' * padding_len

    # Chuyển chuỗi bit thành byte array
    encoded_bytes = bytearray()
    for i in range(0, len(bit_string), 8):
        byte_chunk = bit_string[i:i+8]
        encoded_bytes.append(int(byte_chunk, 2))

    # Cấu trúc Header: HUF1 (4 bytes) + Độ dài gốc (8 bytes) + Bảng độ dài mã (256 bytes) + Padding info (1 byte tùy chọn hoặc gộp chung)
    # Theo đề: Header gồm HUF1, độ dài gốc 8 byte và bảng 256 byte độ dài mã.
    header = b'HUF1' + len(data).to_bytes(8, 'big') + code_lengths_bytes

    return header + bytes(encoded_bytes)

def huffman_decompress(compressed_data: bytes) -> bytes:
    """Giải nén Canonical Huffman từ định dạng Header chuẩn."""
    if not compressed_data.startswith(b'HUF1'):
        raise ValueError("Invalid format: Missing 'HUF1' magic bytes.")

    if len(compressed_data) < HEADER_SIZE:
        raise ValueError("Truncated Huffman header")

    original_length = int.from_bytes(compressed_data[4:12], 'big')
    if original_length == 0:
        if len(compressed_data) != HEADER_SIZE or any(compressed_data[12:268]):
            raise ValueError("Nonempty table or payload for empty Huffman stream")
        return b''

    code_lengths_bytes = compressed_data[12:268]
    lengths = list(code_lengths_bytes)
    
    body = compressed_data[268:]

    # Chuyển phần body thành chuỗi bit
    bit_string = "".join(format(b, '08b') for b in body)

    # Dựng lại bảng mã chính tắc từ bảng độ dài mã trong header (Không cần cây phức tạp!)
    canonical_codes = generate_canonical_codes(lengths)
    
    # Đảo ngược bảng mã để giải mã (Key: chuỗi bit -> Value: ký tự byte)
    decode_map = {v: k for k, v in canonical_codes.items()}

    # Duyệt chuỗi bit để khôi phục dữ liệu gốc
    decoded_bytes = bytearray()
    current_bits = ""
    
    for position, bit in enumerate(bit_string):
        current_bits += bit
        if current_bits in decode_map:
            decoded_bytes.append(decode_map[current_bits])
            current_bits = ""
            if len(decoded_bytes) == original_length:
                remaining = len(bit_string) - position - 1
                if remaining > 7 or '1' in bit_string[position + 1:]:
                    raise ValueError("Extra Huffman payload or nonzero padding")
                break

    if len(decoded_bytes) != original_length:
        raise ValueError("Decoded length does not match original length (truncated Huffman payload)")

    return bytes(decoded_bytes)


def compress(data: bytes) -> bytes:
    """Nén HUF1 qua bản chính của partner."""
    return huffman_compress(data)


def decompress(blob: bytes) -> bytes:
    """Giải nén HUF1 qua bản chính của partner."""
    return huffman_decompress(blob)


def output_check(data: bytes) -> str:
    """Trả 16 ký tự hex đầu của SHA-256 để đối chiếu đầu ra."""
    return hashlib.sha256(data).hexdigest()[:16]
