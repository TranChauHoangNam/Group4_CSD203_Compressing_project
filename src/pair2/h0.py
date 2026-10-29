"""Histogram và entropy bậc 0 của dữ liệu byte."""

import math


def histogram(data: bytes) -> list[int]:
    """Trả số lần xuất hiện của từng giá trị byte từ 0 đến 255."""
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    return counts


def entropy_h0(data: bytes) -> float:
    """Tính H0 theo bit/byte; dữ liệu rỗng có entropy 0.0."""
    if not data:
        return 0.0
    size = len(data)
    return -sum(
        (count / size) * math.log2(count / size)
        for count in histogram(data)
        if count
    )


def h0_ratio(data: bytes) -> float:
    """Trả mốc tỷ lệ nén lý thuyết bậc 0, H0/8."""
    return entropy_h0(data) / 8.0
