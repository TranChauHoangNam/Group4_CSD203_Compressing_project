"""Regression checks for round-trip auditing and malformed streams."""
import tracemalloc

import pytest

import lzw
from rq2 import huffman
from tools.measure import measure, RoundTripError


def test_memory_pass_must_check_hash_and_stop_tracing():
    class Codec:
        calls = 0

        def compress(self, data):
            return data

        def decompress(self, data):
            self.calls += 1
            return data if self.calls <= 3 else b'corrupt'

    with pytest.raises(RoundTripError, match='memory pass'):
        measure(Codec(), b'correct')
    assert not tracemalloc.is_tracing()


def test_memory_pass_exception_stops_tracing():
    class Codec:
        def compress(self, data):
            if tracemalloc.is_tracing():
                raise ValueError('traced failure')
            return data

        def decompress(self, data):
            return data

    with pytest.raises(ValueError, match='traced failure'):
        measure(Codec(), b'correct')
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize('padding', range(1, 16))
def test_lzw_rejects_nonzero_padding(padding):
    blob = bytearray(lzw.compress(b'A'))
    blob[-1] |= padding
    with pytest.raises(ValueError, match='padding'):
        lzw.decompress(bytes(blob))


def test_huffman_empty_stream_rejects_nonempty_table():
    blob = bytearray(huffman.compress(b''))
    blob[12] = 1
    with pytest.raises(ValueError):
        huffman.decompress(bytes(blob))
