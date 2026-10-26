"""Các hợp đồng round-trip chờ Cặp 3 cài BPE; không ghi CSV."""
import pytest

from rq3 import bpe


@pytest.mark.xfail(reason="chưa cài BPE", raises=NotImplementedError, strict=True)
@pytest.mark.parametrize("variant", ["inc", "noheap", "naive"])
@pytest.mark.parametrize("k", [256, 1024, 3840])
@pytest.mark.parametrize("data", [b"", b"A", b"ABABABA"])
def test_roundtrip(data, k, variant):
    assert bpe.decompress(bpe.compress(data, k, variant)) == data
    merges = bpe.train(data, k, variant)
    assert bpe.decode(bpe.encode(data, merges), merges) == data


@pytest.mark.xfail(reason="chưa cài BPE", raises=NotImplementedError, strict=True)
@pytest.mark.parametrize("variant", ["inc", "noheap", "naive"])
def test_illustration_k3(variant):
    data = b"aaabdaaabac"
    merges = bpe.train(data, 3, variant)
    assert bpe.decode(bpe.encode(data, merges), merges) == data


@pytest.mark.xfail(reason="chưa cài BPE", raises=NotImplementedError, strict=True)
def test_short_file_roundtrip(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"BPE sample. ABABABA\n")
    data = path.read_bytes()
    assert bpe.decompress(bpe.compress(data, 256, "inc")) == data
