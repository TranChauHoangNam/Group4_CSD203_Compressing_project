"""Đối chiếu các bản sở hữu độc lập trên cùng dữ liệu tái lập được."""

import random
from typing import Callable

import pytest

from rq2.h0 import entropy_h0, histogram
from rq2.huffman import (
    HEADER_SIZE,
    MAGIC,
    compress,
    decompress,
    histogram as huffman_histogram,
    huffman_compress,
    huffman_decompress,
)
from rq2.reorder import counting_sort_runs, fisher_yates
from rq2.tests.reference import huffman_alt, partner_original

CASES = [
    b"",
    b"\x00",
    b"Z" * (64 * 1024),
    bytes(range(256)),
    b"ABABABA",
    "Canonical Huffman; kiểm tra dữ liệu lặp.\n".encode("utf-8") * 200,
    random.Random(203).randbytes(64 * 1024),
]
CASE_IDS = [
    "empty", "one-byte", "single-symbol-64k", "all-bytes",
    "abababa", "repeated-text", "random-64k-seed-203",
]


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_huffman_cross_decode_and_size(data: bytes) -> None:
    """Giải nén chéo và so kích thước; không đòi hai blob giống từng byte."""
    main_blob = compress(data)
    alt_blob = huffman_alt.compress(data)
    assert huffman_alt.decompress(main_blob) == data
    assert decompress(alt_blob) == data
    assert len(main_blob) == len(alt_blob)


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_entropy_cross_check(data: bytes) -> None:
    """Hai cách tính H0 sai khác tuyệt đối dưới 1e-12."""
    assert abs(entropy_h0(data) - partner_original.calculate_h0(data)) < 1e-12


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_counting_sort_cross_check(data: bytes) -> None:
    """Counting sort bằng histogram cho cùng kết quả với bản đối chứng."""
    assert counting_sort_runs(data) == partner_original.counting_sort_bytes(data)


@pytest.mark.parametrize("data", CASES, ids=CASE_IDS)
def test_fisher_yates_histograms(data: bytes) -> None:
    """Cả hai Fisher–Yates bảo toàn histogram, không so thứ tự đầu ra."""
    expected = histogram(data)
    assert histogram(fisher_yates(data, seed=203)) == expected
    state = random.getstate()
    try:
        random.seed(203)
        assert histogram(partner_original.fisher_yates_shuffle(data)) == expected
    finally:
        random.setstate(state)


@pytest.mark.parametrize("decoder", [decompress, huffman_decompress])
def test_short_header_raises_value_error(decoder: Callable[[bytes], bytes]) -> None:
    """Cả hai API từ chối mọi header thiếu, kể cả độ dài gốc bằng 0."""
    blob = huffman_compress(b"")
    assert MAGIC == b"HUF1"
    assert HEADER_SIZE == 268
    assert huffman_histogram is histogram
    for size in range(HEADER_SIZE):
        with pytest.raises(ValueError):
            decoder(blob[:size])


@pytest.mark.parametrize("decoder", [decompress, huffman_decompress])
def test_truncated_thirty_bytes_raises_value_error(decoder: Callable[[bytes], bytes]) -> None:
    """Cắt 30 byte payload phải báo lỗi thay vì trả dữ liệu ngắn."""
    blob = huffman_compress(bytes(range(256)) * 4)
    with pytest.raises(ValueError, match="Decoded length"):
        decoder(blob[:-30])
