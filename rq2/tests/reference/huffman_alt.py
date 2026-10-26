"""Cài đặt Huffman độc lập, chỉ dùng để đối chứng với bản chính của partner"""

import hashlib
import heapq
import struct

from rq2.h0 import histogram

MAGIC = b"HUF1"
HEADER_SIZE = 4 + 8 + 256


def output_check(data: bytes) -> str:
    """Trả 16 ký tự hex đầu của SHA-256 để đối chiếu đầu ra."""
    return hashlib.sha256(data).hexdigest()[:16]


def _code_lengths(counts: list[int]) -> list[int]:
    """Dựng cây bằng heap (tần suất, byte nhỏ nhất, chỉ số nút)."""
    lengths = [0] * 256
    heap = [(count, symbol, symbol) for symbol, count in enumerate(counts) if count]
    if not heap:
        return lengths
    if len(heap) == 1:
        lengths[heap[0][1]] = 1
        return lengths

    heapq.heapify(heap)
    children: list[tuple[int, int]] = []
    while len(heap) > 1:
        left_count, left_min, left = heapq.heappop(heap)
        right_count, right_min, right = heapq.heappop(heap)
        node = 256 + len(children)
        children.append((left, right))
        heapq.heappush(heap, (left_count + right_count, min(left_min, right_min), node))

    stack = [(heap[0][2], 0)]
    while stack:
        node, depth = stack.pop()
        if node < 256:
            lengths[node] = depth
        else:
            left, right = children[node - 256]
            stack.append((left, depth + 1))
            stack.append((right, depth + 1))
    return lengths


def _canonical_codes(lengths: list[int]) -> list[tuple[int, int]]:
    """Trả (mã nguyên, độ dài) theo byte, từ chối bảng vượt Kraft."""
    codes = [(0, 0)] * 256
    ordered = sorted((length, symbol) for symbol, length in enumerate(lengths) if length)
    code = 0
    previous_length = 0
    for length, symbol in ordered:
        code <<= length - previous_length
        if code >= (1 << length):
            raise ValueError("Invalid Huffman code lengths")
        codes[symbol] = (code, length)
        code += 1
        previous_length = length
    return codes


def compress(data: bytes) -> bytes:
    """Nén hai lượt thành header HUF1 và payload MSB first, đệm 0."""
    lengths = _code_lengths(histogram(data))
    codes = _canonical_codes(lengths)
    payload = bytearray()
    buffer = 0
    bit_count = 0
    for symbol in data:
        code, length = codes[symbol]
        buffer = (buffer << length) | code
        bit_count += length
        while bit_count >= 8:
            bit_count -= 8
            payload.append((buffer >> bit_count) & 0xFF)
        buffer &= (1 << bit_count) - 1
    if bit_count:
        payload.append(buffer << (8 - bit_count))
    return MAGIC + struct.pack(">Q", len(data)) + bytes(lengths) + bytes(payload)


def decompress(blob: bytes) -> bytes:
    """Giải nén HUF1; báo ValueError khi header/payload sai hoặc thiếu."""
    if blob[:4] != MAGIC:
        raise ValueError("Invalid Huffman magic")
    if len(blob) < HEADER_SIZE:
        raise ValueError("Truncated Huffman header")
    original_size = struct.unpack_from(">Q", blob, 4)[0]
    lengths = list(blob[12:HEADER_SIZE])
    codes = _canonical_codes(lengths)
    if original_size == 0:
        if any(lengths) or len(blob) != HEADER_SIZE:
            raise ValueError("Invalid empty Huffman stream")
        return b""

    used_lengths = [length for length in lengths if length]
    if not used_lengths:
        raise ValueError("Missing Huffman code table")
    if (len(blob) - HEADER_SIZE) * 8 < original_size * min(used_lengths):
        raise ValueError("Truncated Huffman payload")
    decode = {
        (length, code): symbol
        for symbol, (code, length) in enumerate(codes)
        if length
    }
    max_length = max(used_lengths)
    output = bytearray()
    code = 0
    length = 0
    for offset in range(HEADER_SIZE, len(blob)):
        value = blob[offset]
        for shift in range(7, -1, -1):
            code = (code << 1) | ((value >> shift) & 1)
            length += 1
            symbol = decode.get((length, code))
            if symbol is not None:
                output.append(symbol)
                code = 0
                length = 0
                if len(output) == original_size:
                    if offset != len(blob) - 1 or value & ((1 << shift) - 1):
                        raise ValueError("Invalid trailing payload or nonzero padding")
                    return bytes(output)
            elif length >= max_length:
                raise ValueError("Invalid Huffman payload code")
    raise ValueError("Truncated Huffman payload")
