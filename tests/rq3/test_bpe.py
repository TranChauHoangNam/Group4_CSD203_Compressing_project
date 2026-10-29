"""Segmented fixed-12-bit BPE contracts for all three variants."""
from collections import Counter
import random
import re

import pytest

from rq3 import bpe

VARIANTS = ["naive", "noheap", "inc"]


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("k", [256, 1024, 3840])
@pytest.mark.parametrize("data", [b"", b"A", b"ABABABA", b"A" * 65536, bytes(range(256))], ids=["empty", "one_byte", "ABABABA", "same_64kib", "all_256"])
def test_roundtrip(data, k, variant):
    merges = bpe.train(data, k, variant)
    tokens = bpe.encode(data, merges)
    assert bpe.decode(tokens, merges) == data
    assert bpe.decompress(bpe.compress(data, k, variant)) == data
    assert bpe.decompress(bpe.compress_with_merges(data, merges)) == data


@pytest.mark.parametrize("variant", VARIANTS)
def test_illustration_k3(variant):
    data = b"aaabdaaabac"
    merges = bpe.train(data, 3, variant)
    assert merges == [(97, 97), (97, 98), (256, 257)]
    assert bpe.encode(data, merges) == [258, 100, 258, 97, 99]
    assert bpe.decode([258, 100, 258, 97, 99], merges) == data


def test_short_file_roundtrip(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"BPE sample. ABABABA\n")
    data = path.read_bytes()
    assert bpe.decompress(bpe.compress(data, 256, "naive")) == data


@pytest.mark.parametrize("data,expected", [(b"aaa", [(97, 97), (256, 97)]), (b"aaaa", [(97, 97), (256, 256)]), (b"abababab", [(97, 98), (256, 256), (257, 257)])])
def test_overlap_counts_until_no_pairs(data, expected):
    assert bpe.train(data, 256, "naive") == expected


@pytest.mark.parametrize("variant", VARIANTS)
def test_singleton_pair_is_merged(variant):
    # The assignment chooses the largest positive count, including one.
    assert bpe.train(b"ab", 1, variant) == [(97, 98)]
    assert bpe.train(b"abc", 3, variant) == [(97, 98), (256, 99)]
    assert bpe.train(b"a b", 256, variant) == [(32, 98)]


@pytest.mark.parametrize("seed", range(100))
def test_fast_encode_matches_reference(seed):
    rng = random.Random(seed)
    alphabet = rng.randrange(2, 5)
    train_data = bytes(rng.randrange(alphabet) for _ in range(rng.randrange(301)))
    test_data = bytes(rng.randrange(alphabet) for _ in range(rng.randrange(301)))
    for k in (0, 1, 3, 16, 64):
        merges = bpe.train(train_data, k, "naive")
        for data in (train_data, test_data):
            tokens = bpe.encode(data, merges)
            assert tokens == bpe.encode_reference(data, merges)
            assert bpe.decode(tokens, merges) == data


def test_production_does_not_call_reference(monkeypatch):
    def forbidden(*args):
        raise AssertionError("Reference must only be used by tests")
    monkeypatch.setattr(bpe, "encode_reference", forbidden)
    assert bpe.decompress(bpe.compress(b"ABABABA", 256, "naive")) == b"ABABABA"


def spec_pack(values):
    # Independent oracle: textual bit concatenation, not the implementation.
    text = "".join(format(v, "012b") for v in values)
    text += "0" * (-len(text) % 8)
    return bytes(int(text[i:i + 8], 2) for i in range(0, len(text), 8))


def test_exact_wire_format_d7():
    table = bytes.fromhex("061061 061062 100101")
    payload = bytes.fromhex("102064 102061 0630")
    expected = (b"BPE1" + (11).to_bytes(8, "big") + (3).to_bytes(2, "big")
                + table + (5).to_bytes(8, "big") + payload)
    blob = bpe.compress(b"aaabdaaabac", 3, "naive")
    assert blob == expected
    assert len(blob[:14]) == 14
    assert blob[14:23] == table  # Three merges, exactly 3 bytes each.
    assert blob[23:31] == (5).to_bytes(8, "big")
    assert len(blob) == 39  # 14 + 9 + 8 + 8.
    assert bpe.decompress(expected) == b"aaabdaaabac"


def test_empty_and_no_merge_wire_format():
    assert bpe.compress(b"", 0, "naive") == b"BPE1" + bytes(18)
    data = bytes(range(256))
    expected = (b"BPE1" + (256).to_bytes(8, "big") + bytes(2)
                + (256).to_bytes(8, "big") + spec_pack(data))
    assert bpe.compress(data, 0, "naive") == expected
    assert len(expected) == 22 + 384
    assert bpe.decompress(expected) == data


@pytest.mark.parametrize("m", [0, 1, 256, 257, 768, 769, 1792, 1793, 3840])
def test_fixed_width_and_deep_dictionary(m):
    merges = ([(0, 0)] + [(255 + i, 0) for i in range(1, m)]) if m else []
    data = b"A"
    blob = bpe.compress_with_merges(data, merges)
    assert len(blob) == 22 + 3 * m + 2
    assert blob[12:14] == m.to_bytes(2, "big")
    assert blob[14:14 + 3*m] == spec_pack(x for pair in merges for x in pair)
    assert blob[14 + 3*m:22 + 3*m] == (1).to_bytes(8, "big")
    assert blob[-2:] == bytes.fromhex("0410")
    assert bpe.decompress(blob) == data
    if m:
        assert bpe.decode([255 + m], merges) == bytes(m + 1)


@pytest.mark.parametrize("kind", ["magic", "short", "truncated", "extra", "truncated_table", "token_padding", "forward_id", "token_id", "length", "too_many_merges", "uint64_count"])
def test_reject_malformed_container(kind):
    blob = bytearray(bpe.compress(b"aaabdaaabac", 3, "naive"))
    if kind == "magic": blob[:4] = b"XXXX"
    elif kind == "short": blob = blob[:21]
    elif kind == "truncated": blob = blob[:-1]
    elif kind == "extra": blob += b"\0"
    elif kind == "truncated_table": blob = blob[:25]
    elif kind == "token_padding": blob[-1] |= 1
    elif kind == "forward_id": blob[14] = 0x10
    elif kind == "token_id": blob[31:33] = b"\xff\xff"
    elif kind == "length": blob[11] = 9
    elif kind == "too_many_merges": blob[12:14] = (3841).to_bytes(2, "big")
    elif kind == "uint64_count": blob[23:31] = (2**32 + 5).to_bytes(8, "big")
    with pytest.raises(ValueError):
        bpe.decompress(bytes(blob))


@pytest.mark.parametrize("k", [-1, 3841, 1.5, True])
def test_invalid_k(k):
    with pytest.raises(ValueError):
        bpe.train(b"abc", k, "naive")


def test_invalid_variant():
    with pytest.raises(ValueError):
        bpe.train(b"abc", 3, "wrong")


def test_segment_boundary_never_merged():
    data = b"ab ab ab"
    assert bpe._segments(data) == [b"ab", b" ab", b" ab"]
    merges = bpe.train(data, 256, "naive")
    assert merges == [(97, 98), (32, 256)]
    assert bpe.encode(data, merges) == [256, 257, 257]
    # Even an externally supplied b+space merge must not cross the boundary.
    assert bpe.encode(data, [(98, 32)]) == list(data)
    assert bpe.encode_reference(data, [(98, 32)]) == list(data)
    assert bpe.decompress(bpe.compress(data, 256, "naive")) == data


def test_weighted_unique_segments(monkeypatch):
    data = b"xy xy xy xy abab"
    calls = []
    original = bpe._replace
    def record(tokens, pair, new_id):
        calls.append(tuple(tokens))
        return original(tokens, pair, new_id)
    monkeypatch.setattr(bpe, "_replace", record)
    assert bpe.train(data, 1, "naive") == [(120, 121)]
    assert len(calls) == len(set(re.findall(rb" ?[^\s]+|\s+", data))) == 3


def test_segment_cache(monkeypatch):
    data = b"ab ab ab\t ab ab\n\n"
    merges = bpe.train(data, 256, "naive")
    expected = bpe.encode_reference(data, merges)
    calls = []
    original = bpe._encode_segment
    def record(segment, pairs, ranks):
        calls.append(segment)
        return original(segment, pairs, ranks)
    monkeypatch.setattr(bpe, "_encode_segment", record)
    assert bpe.encode(data, merges) == expected
    assert Counter(calls) == Counter({s: 1 for s in re.findall(rb" ?[^\s]+|\s+", data)})
    # A second call with a different table must not reuse stale cached tokens.
    assert bpe.encode(data, []) == list(data)


def recount_occurrences(data, k):
    # Independent training oracle: keep EVERY occurrence, no aggregation/cache.
    segments = [list(s) for s in re.findall(rb" ?[^\s]+|\s+", data)]
    merges = []
    for rank in range(k):
        counts = Counter(pair for segment in segments for pair in zip(segment, segment[1:]))
        if not counts:
            break
        pair = min(counts, key=lambda p: (-counts[p], p))
        rewritten = []
        for segment in segments:
            output, i = [], 0
            while i < len(segment):
                if tuple(segment[i:i + 2]) == pair:
                    output.append(256 + rank)
                    i += 2
                else:
                    output.append(segment[i])
                    i += 1
            rewritten.append(output)
        segments = rewritten
        merges.append(pair)
    return merges


@pytest.mark.parametrize("seed", range(50))
def test_segmented_random_against_occurrence_oracle(seed):
    rng = random.Random(seed)
    alphabet = b"aabc \t\n\r\v\f"
    vocabulary = [bytes(rng.choice(alphabet) for _ in range(rng.randrange(1, 20))) for _ in range(5)]
    data = b" ".join(rng.choice(vocabulary) for _ in range(15))
    assert b"".join(re.findall(rb" ?[^\s]+|\s+", data)) == data
    for k in (0, 1, 3, 16):
        merges = bpe.train(data, k, "naive")
        assert merges == recount_occurrences(data, k)
        test_data = data + b"\t ab ab ab"
        tokens = bpe.encode(test_data, merges)
        assert tokens == bpe.encode_reference(test_data, merges)
        assert bpe.decode(tokens, merges) == test_data
        assert bpe.decompress(bpe.compress_with_merges(test_data, merges)) == test_data


@pytest.mark.parametrize("orig_len", [10, 12])
def test_reject_decoded_length_in_both_directions(orig_len):
    blob = bytearray(bpe.compress(b"aaabdaaabac", 3, "naive"))
    blob[4:12] = orig_len.to_bytes(8, "big")
    with pytest.raises(ValueError):
        bpe.decompress(bytes(blob))


@pytest.mark.parametrize("i", range(3))
@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("invalid", ["self", "future", "out_of_range"])
def test_reject_invalid_merge_reference_at_each_rank(i, side, invalid):
    pairs = [[97, 97], [97, 98], [256, 257]]
    pairs[i][side] = {"self": 256 + i, "future": 257 + i, "out_of_range": 4095}[invalid]
    blob = bytearray(bpe.compress(b"aaabdaaabac", 3, "naive"))
    blob[14:23] = spec_pack(x for pair in pairs for x in pair)
    with pytest.raises(ValueError):
        bpe.decompress(bytes(blob))


@pytest.mark.parametrize("cut", range(39))
def test_every_truncated_d7_prefix_rejected(cut):
    blob = bpe.compress(b"aaabdaaabac", 3, "naive")
    with pytest.raises(ValueError):
        bpe.decompress(blob[:cut])


@pytest.mark.parametrize("count", [0, 1, 4, 6, 2**32 + 5, 2**64 - 1])
def test_reject_payload_size_for_declared_token_count(count):
    blob = bytearray(bpe.compress(b"aaabdaaabac", 3, "naive"))
    blob[23:31] = count.to_bytes(8, "big")
    with pytest.raises(ValueError):
        bpe.decompress(bytes(blob))
