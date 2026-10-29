"""Container chung cho mọi codec: Magic (4 byte ASCII) + độ dài gốc (8 byte, big-endian).

GIẢ ĐỊNH CẦN CẢ NHÓM CHỐT: thứ tự byte của độ dài gốc là big-endian.
Mọi codec (RLE, Huffman, LZW, BPE) nên dùng lại hai hàm dưới đây để container thống nhất.
"""
import hashlib

HEADER_LEN = 12  # 4 byte Magic + 8 byte độ dài gốc


def pack_header(magic: bytes, orig_len: int) -> bytes:
    if len(magic) != 4:
        raise ValueError("Magic phải đúng 4 byte")
    return magic + orig_len.to_bytes(8, "big")


def parse_header(blob, magic: bytes) -> int:
    """Kiểm tra Magic, trả về độ dài gốc. Ném ValueError nếu file sai."""
    if len(blob) < HEADER_LEN:
        raise ValueError("File nén quá ngắn, thiếu header")
    if bytes(blob[:4]) != magic:
        raise ValueError(f"Magic sai: nhận {bytes(blob[:4])!r}, cần {magic!r}")
    return int.from_bytes(blob[4:HEADER_LEN], "big")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_16(data: bytes) -> str:
    """16 ký tự hex đầu của SHA-256 (cột output_check)."""
    return sha256_hex(data)[:16]
