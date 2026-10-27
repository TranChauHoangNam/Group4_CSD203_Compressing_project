"""Phase 2 equivalence: weighted segments, overlap, and real corpus prefixes."""
import hashlib
import json
from pathlib import Path
import random

import pytest

from rq3 import bpe


VARIANTS = ("naive", "noheap", "inc")
EDGE_CASES = [b"", b"A", b"A" * 65536, bytes(range(256)), b"ABABABA",
              b"aaabdaaabac", b"aaaa", b"abababab", b" aaa", b"ab ab ab",
              b"aaa aaa aaa\n aaa\n", b" \t\n\r\v\f", b"xy xy xy xy abab", b"aaa", b"BPE sample. ABABABA\n"]


def assert_equivalent(data, k):
    expected = bpe.train(data, k, "naive")
    tokens = bpe.encode(data, expected)
    assert tokens == bpe.encode_reference(data, expected)
    for variant in ("noheap", "inc"):
        merges = bpe.train(data, k, variant)
        assert merges == expected, (variant, k, data, expected, merges)
        encoded = bpe.encode(data, merges)
        assert encoded == tokens, (variant, k, data, tokens, encoded)
        assert bpe.decode(encoded, merges) == data
    return len(expected), len(tokens)


@pytest.mark.parametrize("data", EDGE_CASES, ids=["empty", "one", "64k_same", "all_bytes", "ABABABA", "D7", "aaaa", "abababab", "leading_space", "boundary", "repeated_segments", "whitespace", "weighted", "aaa", "short_file_content"])
@pytest.mark.parametrize("k", [3, 256, 3840])
def test_edge_variants(data, k):
    assert_equivalent(data, k)


@pytest.mark.parametrize("seed", range(200))
def test_random_segmented_variants(seed):
    rng = random.Random(seed)
    alphabet = bytes(range(97, 97 + 2 + seed % 3)) + b" \n"
    length = seed if seed < 2 else rng.randrange(2, 301)
    data = bytes(rng.choice(alphabet) for _ in range(length))
    if length >= 2:
        # Force both boundary types, while preserving length <= 300.
        data = b" " + data[1:-1] + b"\n"
    for k in (0, 1, 3, 16, 64, 256):
        assert_equivalent(data, k)


@pytest.mark.parametrize("name", ["v1_train_1mib.txt", "e1_train_1mib.txt"])
def test_corpus_prefix_variants(name):
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "wiki" / name
    if not path.is_file():
        pytest.skip(f"{name} missing; see README 'Data' section")
    whole = path.read_bytes()
    expected = json.loads((root / "docs/manifest.json").read_text(encoding="utf-8"))["files"][name]
    assert len(whole) == expected["bytes"]
    assert hashlib.sha256(whole).hexdigest() == expected["sha256"]
    data = whole[:65536]
    assert len(data) == 65536
    m, n = assert_equivalent(data, 256)
    print(f"{name}: prefix_bytes={len(data)}, K=256, merges={m}, tokens={n}, all_variants=MATCH")


@pytest.mark.parametrize("variant", ["noheap", "inc"])
def test_incremental_does_not_use_full_replacement_scan(monkeypatch, variant):
    data = b"aaaa abab abab\n aaa aaa ab ab ab"
    expected = bpe.train(data, 64, "naive")
    def forbidden(*args):
        raise AssertionError("Incremental trainers must update local edges, not rescan via _replace")
    monkeypatch.setattr(bpe, "_replace", forbidden)
    assert bpe.train(data, 64, variant) == expected
