"""Kiểm tra histogram, entropy và tỷ lệ bậc 0."""

import pytest

from rq2.h0 import entropy_h0, h0_ratio, histogram


def test_histogram() -> None:
    """Histogram luôn có 256 ô và đếm đúng cả hai đầu miền byte."""
    counts = histogram(b"\x00\x00\x01\xff")
    assert len(counts) == 256
    assert counts[0] == 2
    assert counts[1] == counts[255] == 1
    assert sum(counts) == 4
    assert histogram(b"") == [0] * 256
    assert histogram(bytes(range(256))) == [1] * 256


@pytest.mark.parametrize(
    ("data", "expected"),
    [(b"", 0.0), (b"A" * 100, 0.0), (b"AB" * 100, 1.0),
     (bytes(range(256)), 8.0), (b"AAAB", 0.8112781244591328)],
)
def test_entropy_and_ratio(data: bytes, expected: float) -> None:
    """Đối chiếu với các phân phối có entropy biết trước."""
    assert entropy_h0(data) == pytest.approx(expected)
    assert h0_ratio(data) == pytest.approx(expected / 8.0)
