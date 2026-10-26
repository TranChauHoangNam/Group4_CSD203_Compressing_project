"""Kiểm tra bảo toàn histogram và tính tái lập khi đổi thứ tự."""

import random

import pytest

from rq2.h0 import entropy_h0, histogram
from rq2.reorder import counting_sort_runs, fisher_yates


@pytest.mark.parametrize("data", [b"", b"x", b"A" * 1024, bytes(range(256)) * 8, b"banana bread"])
def test_preserve_histogram_and_input(data: bytes) -> None:
    """Hai phép đổi thứ tự giữ nguyên độ dài, histogram, H0 và đầu vào."""
    original = bytes(bytearray(data))
    for result in (counting_sort_runs(data), fisher_yates(data, 203)):
        assert isinstance(result, bytes)
        assert len(result) == len(data)
        assert histogram(result) == histogram(data)
        assert entropy_h0(result) == entropy_h0(data)
        assert data == original


def test_counting_sort_order() -> None:
    """Các byte sau counting sort không giảm và có đủ các run."""
    data = bytes(range(255, -1, -1)) * 3
    result = counting_sort_runs(data)
    assert all(left <= right for left, right in zip(result, result[1:]))
    assert result == bytes(sorted(data))
    assert counting_sort_runs(b"banana") == b"aaabnn"


def test_fisher_yates_seed() -> None:
    """Seed tái lập kết quả và không làm thay đổi RNG toàn cục."""
    data = bytes(range(256)) * 8
    state = random.getstate()
    first = fisher_yates(data, 42)
    assert first == fisher_yates(data, 42)
    assert first != fisher_yates(data, 43)
    assert first != data
    assert random.getstate() == state
