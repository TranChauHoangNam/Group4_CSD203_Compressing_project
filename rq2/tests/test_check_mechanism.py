"""Dữ liệu tổng hợp có seed cố định; không thay thế số liệu thực nghiệm."""
import random

import pytest

rle = pytest.importorskip("rle")
from rq2.check_mechanism import inspect_data, lzw_full_position


def test_uniform_shuffled_rle_prediction(tmp_path):
    rng = random.Random(203)
    path = tmp_path / "uniform.bin"
    path.write_bytes(bytes(rng.randrange(256) for _ in range(20000)))
    data = path.read_bytes()
    shuffled = list(data)
    rng.shuffle(shuffled)
    actual = len(rle.compress(bytes(shuffled))) / len(data)
    assert abs(inspect_data(data)['shuffled_prediction'] - actual) < .05


def test_few_values_dictionary_not_full(tmp_path):
    path = tmp_path / "few.bin"
    path.write_bytes(b"A" * 1000 + b"B" * 1000 + b"C" * 1000)
    assert lzw_full_position(path.read_bytes()) is None


def test_sorted_all_values_dictionary_full(tmp_path):
    rng = random.Random(203)
    values = list(range(256)) * 256
    rng.shuffle(values)
    path = tmp_path / "all.bin"
    path.write_bytes(bytes(sorted(values)))
    pos = lzw_full_position(path.read_bytes())
    assert isinstance(pos, int)
    assert 0 < pos < path.stat().st_size
