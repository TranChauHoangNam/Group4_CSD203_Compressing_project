"""Đổi thứ tự byte, bảo toàn histogram và dữ liệu đầu vào."""

import random

from .h0 import histogram


def counting_sort_runs(data: bytes) -> bytes:
    """Gom các byte bằng nhau thành run theo giá trị tăng dần."""
    result = bytearray()
    for value, count in enumerate(histogram(data)):
        result.extend(bytes([value]) * count)
    return bytes(result)


def fisher_yates(data: bytes, seed: int) -> bytes:
    """Xáo trộn Fisher–Yates với bộ sinh ngẫu nhiên riêng theo seed."""
    rng = random.Random(seed)
    result = bytearray(data)
    for index in range(len(result) - 1, 0, -1):
        other = rng.randrange(index + 1)
        result[index], result[other] = result[other], result[index]
    return bytes(result)
