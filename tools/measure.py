"""Đo một lượt: thời gian nén/giải nén (trung vị của N lần), bộ nhớ đỉnh (tracemalloc), SHA-256."""
import statistics
import time
import tracemalloc

from container import sha256_16, sha256_hex


class RoundTripError(Exception):
    pass


def measure(codec, data: bytes, repeats: int = 3, with_mem: bool = True) -> dict:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    if tracemalloc.is_tracing():
        raise RuntimeError("Tracing must be off before measuring")
    ref = sha256_hex(data)
    comp_t, dec_t = [], []
    blob = back = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        blob = codec.compress(data)
        t1 = time.perf_counter()
        back = codec.decompress(blob)
        t2 = time.perf_counter()
        if sha256_hex(back) != ref:
            raise RoundTripError("SHA-256 sau giải nén không khớp bản gốc")
        comp_t.append((t1 - t0) * 1000)
        dec_t.append((t2 - t1) * 1000)

    peak_kib = None
    if with_mem:  # đo riêng, vì tracemalloc làm chậm chương trình
        tracemalloc.start()
        try:
            b2 = codec.compress(data)
            d2 = codec.decompress(b2)
            peak_kib = tracemalloc.get_traced_memory()[1] / 1024
        finally:
            tracemalloc.stop()
        if sha256_hex(d2) != ref:
            raise RoundTripError("SHA-256 mismatch in memory pass")
        if b2 != blob:
            raise RoundTripError("Compressed output differs in memory pass")
        del b2, d2

    return {
        "orig_bytes": len(data),
        "comp_bytes": len(blob),
        "comp_ms": statistics.median(comp_t),
        "decomp_ms": statistics.median(dec_t),
        "peak_mem_kib": peak_kib,
        "output_check": sha256_16(back),
        "roundtrip_ok": True,
    }
