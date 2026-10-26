"""Byte-level BPE, mandatory segmented fixed-12-bit format."""
from collections import Counter
import heapq
import re
import struct

from container import pack_header, parse_header

MAX_MERGES = 3840


def _merges(merges):
    """Validate the merge DAG and unique pairs."""
    pairs = list(merges)
    if len(pairs) > MAX_MERGES:
        raise ValueError('Too many merges')
    seen = set()
    result = []
    for i, pair in enumerate(pairs):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError('A merge must contain two ids')
        a, b = pair
        if any(type(x) is not int or not 0 <= x < 256 + i for x in (a, b)):
            raise ValueError('Merge references a future or invalid id')
        if (a, b) in seen:
            raise ValueError('Duplicate merge pair')
        seen.add((a, b))
        result.append((a, b))
    return result


def _replace(tokens, pair, new_id):
    result = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens) and (tokens[i], tokens[i + 1]) == pair:
            result.append(new_id)
            i += 2
        else:
            result.append(tokens[i])
            i += 1
    return result


def train(data: bytes, k: int, variant: str):
    """Train weighted unique segments with naive/noheap/inc. API K: 0..3840."""
    if not isinstance(data, bytes):
        raise TypeError('data must be bytes')
    if type(k) is not int or not 0 <= k <= MAX_MERGES:
        raise ValueError('k must be an integer from 0 to 3840')
    if variant not in {"naive", "noheap", "inc"}:
        raise ValueError('Invalid variant')
    if variant != "naive":
        return _train_incremental(data, k, use_heap=(variant == "inc"))
    # One mutable token list per UNIQUE raw segment, weighted by frequency.
    segments = [(list(segment), frequency)
                for segment, frequency in Counter(_segments(data)).items()]
    merges = []
    for _ in range(k):
        counts = Counter()
        for tokens, frequency in segments:
            for pair in zip(tokens, tokens[1:]):
                counts[pair] += frequency
        if not counts:
            break
        pair = min(counts, key=lambda p: (-counts[p], p))
        if counts[pair] < 2:
            break
        new_id = 256 + len(merges)
        segments = [(_replace(tokens, pair, new_id), frequency)
                    for tokens, frequency in segments]
        merges.append(pair)
    return merges


def _train_incremental(data, k, use_heap):
    """Linked lists per UNIQUE segment, weighted global counts and indexes.

    positions[sid][pair] holds every adjacent occurrence's left node, including
    overlaps. inverted[pair] contains exactly the segment ids holding that pair.
    Each edge update changes its global count by the segment's frequency.
    noheap scans counts; inc uses lazy heap entries (-count, a, b).
    """
    states = []
    positions = []
    counts = {}
    inverted = {}
    for sid, (segment, weight) in enumerate(Counter(_segments(data)).items()):
        values = list(segment)
        n = len(values)
        states.append((values, list(range(-1, n - 1)),
                       list(range(1, n)) + [-1], [True] * n, weight))
        local = {}
        positions.append(local)
        for left in range(n - 1):
            pair = (values[left], values[left + 1])
            local.setdefault(pair, set()).add(left)
            counts[pair] = counts.get(pair, 0) + weight
        for pair in local:
            inverted.setdefault(pair, set()).add(sid)

    heap = [(-count, a, b) for (a, b), count in counts.items()] if use_heap else []
    if use_heap:
        heapq.heapify(heap)
    merges = []
    for _ in range(k):
        if use_heap:
            while heap:
                neg_count, a, b = heapq.heappop(heap)
                pair = (a, b)
                if counts.get(pair, 0) == -neg_count:
                    break
            else:
                break
        else:
            if not counts:
                break
            pair = min(counts, key=lambda p: (-counts[p], p))
        if counts[pair] < 2:
            break
        new_id = 256 + len(merges)
        dirty = set()
        # Snapshot affected segments; indexes are updated during replacement.
        for sid in sorted(inverted[pair]):
            values, prev, nxt, alive, weight = states[sid]
            local = positions[sid]

            def remove_edge(left):
                if left == -1 or nxt[left] == -1:
                    return
                old = (values[left], values[nxt[left]])
                occurrences = local[old]
                occurrences.remove(left)
                counts[old] -= weight
                if not counts[old]:
                    del counts[old]
                if not occurrences:
                    del local[old]
                    inverted[old].remove(sid)
                    if not inverted[old]:
                        del inverted[old]
                dirty.add(old)

            def add_edge(left):
                if left == -1 or nxt[left] == -1:
                    return
                new = (values[left], values[nxt[left]])
                local.setdefault(new, set()).add(left)
                inverted.setdefault(new, set()).add(sid)
                counts[new] = counts.get(new, 0) + weight
                dirty.add(new)

            # Increasing original positions implement D2 left-to-right order.
            # Overlapping entries removed by an earlier replacement are skipped.
            for left in sorted(local[pair]):
                if not alive[left]:
                    continue
                right = nxt[left]
                if right == -1 or (values[left], values[right]) != pair:
                    continue
                before, after = prev[left], nxt[right]
                # Remove all three old edges BEFORE changing links or values.
                # Even for aaaa, each edge has its own distinct left position.
                remove_edge(before)
                remove_edge(left)
                remove_edge(right)
                values[left] = new_id
                alive[right] = False
                nxt[left] = after
                if after != -1:
                    prev[after] = left
                add_edge(before)
                add_edge(left)
        merges.append(pair)
        if use_heap:
            # Publish only final counts, not intermediate +/- updates.
            for a, b in dirty:
                count = counts.get((a, b), 0)
                if count:
                    heapq.heappush(heap, (-count, a, b))
    return merges


def _segments(data):
    """Mandatory spec pre-tokenization; byte whitespace semantics."""
    return re.findall(rb" ?[^\s]+|\s+", data)


def encode_reference(data: bytes, merges):
    """Test oracle: sequential merge scans per segment, without caching."""
    pairs = _merges(merges)
    result = []
    for segment in _segments(data):
        tokens = list(segment)
        for rank, pair in enumerate(pairs):
            tokens = _replace(tokens, pair, 256 + rank)
        result.extend(tokens)
    return result


def encode(data: bytes, merges):
    """Encode unique segments once using a call-local segment -> tokens cache.

    The cache is never shared across merge tables. Output concatenation cannot
    create a new merge across segment boundaries.
    """
    pairs = _merges(merges)
    ranks = {pair: i for i, pair in enumerate(pairs)}
    cache = {}
    result = []
    for segment in _segments(data):
        if segment not in cache:
            cache[segment] = _encode_segment(segment, pairs, ranks)
        result.extend(cache[segment])
    return result


def _encode_segment(data, pairs, ranks):
    """Linked list + heap (rank, original position) inside one segment."""
    values = list(data)
    n = len(values)
    if not n:
        return []
    prev = list(range(-1, n - 1))
    nxt = list(range(1, n)) + [-1]
    alive = [True] * n
    heap = []

    def candidate(left):
        if left < 0 or not alive[left]:
            return None
        right = nxt[left]
        if right == -1:
            return None
        rank = ranks.get((values[left], values[right]))
        return None if rank is None else (rank, left, right)

    for left in range(n - 1):
        item = candidate(left)
        if item is not None:
            heap.append(item)
    heapq.heapify(heap)
    while heap:
        rank, left, right = heapq.heappop(heap)
        if not alive[left] or not alive[right] or nxt[left] != right:
            continue
        if (values[left], values[right]) != pairs[rank]:
            continue
        values[left] = 256 + rank
        alive[right] = False
        after = nxt[right]
        nxt[left] = after
        if after != -1:
            prev[after] = left
        for position in (prev[left], left):
            item = candidate(position)
            if item is not None:
                heapq.heappush(heap, item)
    result = []
    position = 0
    while position != -1:
        result.append(values[position])
        position = nxt[position]
    return result


def _decode(tokens, pairs, limit=None):
    out = bytearray()
    for token in tokens:
        if type(token) is not int or not 0 <= token < 256 + len(pairs):
            raise ValueError('Invalid token id')
        stack = [token]
        while stack:
            value = stack.pop()
            if value < 256:
                if limit is not None and len(out) >= limit:
                    raise ValueError('Decoded data exceeds orig_len')
                out.append(value)
            else:
                a, b = pairs[value - 256]
                stack.extend((b, a))
    return bytes(out)


def decode(tokens, merges) -> bytes:
    """Expand tokens with an iterative stack, not recursive calls."""
    return _decode(tokens, _merges(merges))


def _pack(values, width):
    out = bytearray()
    accumulator = bits = 0
    for value in values:
        accumulator = (accumulator << width) | value
        bits += width
        while bits >= 8:
            bits -= 8
            out.append((accumulator >> bits) & 255)
        accumulator &= (1 << bits) - 1
    if bits:
        out.append(accumulator << (8 - bits))
    return bytes(out)


def _unpack(blob, count, width):
    if len(blob) != (count * width + 7) // 8:
        raise ValueError('Invalid bit-region size')
    padding = (-count * width) % 8
    if padding and blob[-1] & ((1 << padding) - 1):
        raise ValueError('Padding must be zero')
    values = []
    accumulator = bits = 0
    for byte in blob:
        accumulator = (accumulator << 8) | byte
        bits += 8
        while bits >= width and len(values) < count:
            bits -= width
            values.append((accumulator >> bits) & ((1 << width) - 1))
        accumulator &= (1 << bits) - 1
    return values


def compress_with_merges(data: bytes, merges) -> bytes:
    """Spec layout: BPE1/u64 length/u16 m/3m table/u64 count/12-bit payload."""
    pairs = _merges(merges)
    tokens = encode(data, pairs)
    if len(tokens) > 0xffffffffffffffff:
        raise ValueError("n_tokens exceeds uint64")
    return (pack_header(b"BPE1", len(data)) + struct.pack(">H", len(pairs))
            + _pack((x for pair in pairs for x in pair), 12)
            + struct.pack(">Q", len(tokens)) + _pack(tokens, 12))


def compress(data: bytes, k: int, variant: str) -> bytes:
    """Train then package using the mandatory fixed 12-bit spec format."""
    return compress_with_merges(data, train(data, k, variant))


def decompress(blob: bytes) -> bytes:
    """Reject invalid magic, lengths, ids, nonzero payload padding."""
    orig_len = parse_header(blob, b"BPE1")
    if len(blob) < 22:
        raise ValueError("Missing merge count or token count")
    m = struct.unpack(">H", blob[12:14])[0]
    if m > MAX_MERGES:
        raise ValueError("More than 3840 merges")
    table_end = 14 + 3 * m
    payload_start = table_end + 8
    if len(blob) < payload_start:
        raise ValueError("Truncated merge table or token count")
    n_tokens = struct.unpack(">Q", blob[table_end:payload_start])[0]
    payload_bytes = (12 * n_tokens + 7) // 8
    if len(blob) != payload_start + payload_bytes:
        raise ValueError("Invalid container size")
    flat = _unpack(blob[14:table_end], 2 * m, 12)
    pairs = _merges(list(zip(flat[::2], flat[1::2])))
    tokens = _unpack(blob[payload_start:], n_tokens, 12)
    result = _decode(tokens, pairs, orig_len)
    if len(result) != orig_len:
        raise ValueError("Decoded length does not match orig_len")
    return result
