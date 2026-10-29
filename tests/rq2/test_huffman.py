"""Kiểm tra round-trip, định dạng chính tắc và các luồng bị hỏng."""

import hashlib
import os
import random
import struct

import pytest

from rq2.h0 import entropy_h0, histogram
from rq2.huffman import HEADER_SIZE, compress, decompress, output_check
from rq2.tests.reference import huffman_alt

TEXT = ("Huffman coding compresses frequent symbols with shorter codes. "
        "Nén dữ liệu và tokenizer BPE trong đồ án CSD203.\n").encode("utf-8") * 200
CASES = [b"", b"\x00", b"Z" * (64 * 1024), bytes(range(256)), TEXT, os.urandom(64 * 1024)]
CASE_IDS = ["empty", "one-byte", "single-symbol-64k", "all-bytes", "text", "random-64k"]


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_round_trip_sha256(data: bytes) -> None:
    """Giải nén phải khôi phục dữ liệu và toàn bộ SHA-256."""
    restored = decompress(compress(data))
    assert restored == data
    assert hashlib.sha256(restored).digest() == hashlib.sha256(data).digest()
    assert output_check(restored) == output_check(data)


@pytest.mark.parametrize("data, expected", [
    (b"", {}),
    (b"Z" * 9, {90: "0"}),
    (b"ABCD", {65: "00", 66: "01", 67: "10", 68: "11"}),
    (b"AAAAABBC", {65: "0", 66: "10", 67: "11"}),
    (bytes([255]) * 10 + bytes([0]) * 3 + bytes([128]),
     {255: "0", 0: "10", 128: "11"}),
])
def test_canonical_histogram_order(data, expected):
    from rq2.huffman import build_code_lengths, generate_canonical_codes

    codes = generate_canonical_codes(build_code_lengths(data))
    assert list(codes.items()) == list(expected.items())


def test_output_check() -> None:
    """Tiện ích trả đúng 16 ký tự hex đầu của SHA-256 đã biết."""
    assert output_check(b"abc") == "ba7816bf8f01cfea"
    assert output_check(b"") == "e3b0c44298fc1c14"


def test_empty_header() -> None:
    """Dữ liệu rỗng chỉ có header 268 byte và bảng mã toàn 0."""
    assert HEADER_SIZE == 268
    assert compress(b"") == b"HUF1" + b"\x00" * 264


def test_single_symbol() -> None:
    """Một loại byte có mã 0 dài 1 bit và đệm 0 ở byte cuối."""
    blob = compress(b"Z" * 9)
    lengths = blob[12:HEADER_SIZE]
    assert blob[:12] == b"HUF1" + struct.pack(">Q", 9)
    assert lengths[ord("Z")] == 1
    assert sum(lengths) == 1
    assert blob[HEADER_SIZE:] == b"\x00\x00"


def test_canonical_known_vector() -> None:
    """Vector độc lập: A=0, B=10, C=11; ABCC đóng gói thành 0x5e."""
    lengths = bytearray(256)
    lengths[65:68] = bytes([1, 2, 2])
    header = b"HUF1" + struct.pack(">Q", 4) + bytes(lengths)
    assert decompress(header + b"\x5e") == b"ABCC"
    # AAABC có mã 0001011, đệm 0 thành 00010110.
    expected = b"HUF1" + struct.pack(">Q", 5) + bytes(lengths) + b"\x16"
    assert compress(b"AAABC") == expected


def test_ties_and_determinism() -> None:
    """Kiểm tra vector phá hòa ABC và tính tái lập của bản chính partner."""
    blob = compress(b"ABC")
    assert blob[12 + 65:12 + 68] == bytes([2, 2, 1])
    assert blob[HEADER_SIZE:] == b"\xb0"  # A=10, B=11, C=0.
    assert compress(b"ABC") == blob
    assert compress(b"CBA")[12:HEADER_SIZE] == blob[12:HEADER_SIZE]
    all_bytes = compress(bytes(range(256)))
    assert all_bytes[12:HEADER_SIZE] == bytes([8]) * 256
    assert all_bytes[HEADER_SIZE:] == bytes(range(256))


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_kraft(data: bytes) -> None:
    """Bảng độ dài thỏa Kraft và đánh dấu đúng các byte xuất hiện."""
    lengths = compress(data)[12:HEADER_SIZE]
    assert sum(2.0 ** (-length) for length in lengths if length) <= 1.0
    assert [length > 0 for length in lengths] == [count > 0 for count in histogram(data)]


def test_payload_entropy_bound() -> None:
    """Độ dài mã trung bình và payload gồm đệm đều nằm trong [H0, H0+1)."""
    blob = compress(TEXT)
    lengths = blob[12:HEADER_SIZE]
    bit_count = sum(count * length for count, length in zip(histogram(TEXT), lengths))
    payload_bits = (len(blob) - HEADER_SIZE) * 8
    h0 = entropy_h0(TEXT)
    assert h0 <= bit_count / len(TEXT) < h0 + 1
    assert h0 <= payload_bits / len(TEXT) < h0 + 1
    assert 0 <= payload_bits - bit_count < 8


def test_bad_magic() -> None:
    """Magic sai phải gây ValueError."""
    with pytest.raises(ValueError, match="magic"):
        decompress(b"XXXX" + compress(TEXT)[4:])


def test_every_truncated_prefix() -> None:
    """Mọi vị trí cắt của một luồng mẫu, gồm cả header, đều bị từ chối."""
    blob = compress(bytes(range(256)) * 2)
    for end in range(len(blob)):
        with pytest.raises(ValueError):
            decompress(blob[:end])


@pytest.mark.parametrize("data", CASES[1:], ids=CASE_IDS[1:])
def test_truncated_final_byte(data: bytes) -> None:
    """Thiếu byte payload cuối luôn gây ValueError trên các ca biên."""
    with pytest.raises(ValueError):
        decompress(compress(data)[:-1])


def test_invalid_table() -> None:
    blob = bytearray(compress(b"ABC"))
    blob[12 + 65:12 + 68] = bytes([1, 1, 1])
    for decoder in (decompress, huffman_alt.decompress):
        with pytest.raises(ValueError):
            decoder(bytes(blob))
    blob[12:HEADER_SIZE] = bytes(256)
    for decoder in (decompress, huffman_alt.decompress):
        with pytest.raises(ValueError):
            decoder(bytes(blob))


def test_invalid_payload_and_padding() -> None:
    blob = compress(b"A")
    for decoder in (decompress, huffman_alt.decompress):
        for invalid in (blob[:-1] + b"\x80", blob[:-1] + b"\x01", blob + b"\x00",
                        compress(b"") + b"\x00"):
            with pytest.raises(ValueError):
                decoder(invalid)


def test_round_trip_one_mib() -> None:
    """Kiểm tra file 1 MiB với tất cả giá trị byte, không đặt ngưỡng thời gian."""
    data = random.Random(203).randbytes(1024 * 1024)
    restored = decompress(compress(data))
    assert restored == data
    assert hashlib.sha256(restored).digest() == hashlib.sha256(data).digest()
