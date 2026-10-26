"""Đo RQ2 và ghi CSV chung; chạy bằng python -m rq2.run_rq2."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Callable, Iterator, Sequence

from common.results_schema import append_row, sha16
from rq2 import huffman
from rq2.h0 import entropy_h0
from rq2.reorder import counting_sort_runs, fisher_yates

R1_FILES = ("alice29.txt", "kennedy.xls", "v1_test_1mib.txt")


@dataclass(frozen=True)
class Codec:
    """Hai hàm byte của một codec cùng tên dùng trong CSV."""

    name: str
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]


@dataclass(frozen=True)
class Measurement:
    """Trung vị thời gian, đỉnh bộ nhớ và kết quả đã kiểm tra toàn vẹn."""

    comp_bytes: int
    comp_ms: float
    decomp_ms: float
    peak_mem_kib: float
    restored: bytes


def _positive_int(value: str) -> int:
    """Đọc số lần lặp nguyên dương cho argparse."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("--repeats phải lớn hơn 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Khai báo các tham số chạy thực nghiệm từ thư mục gốc."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("results_rq2.csv"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    parser.add_argument("--repeats", type=_positive_int, default=3)
    parser.add_argument(
        "--codec", nargs="+", action="append", default=[], metavar="NAME=MODULE",
        help="Module Cặp 1, ví dụ rle=pair1.rle lzw=pair1.lzw",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser


def load_codecs(overrides: Sequence[str]) -> tuple[list[Codec], list[str]]:
    """Nạp Huffman và các codec tùy chọn; bỏ qua module không import được."""
    modules = {"rle": "rle", "lzw": "lzw"}
    assigned: set[str] = set()
    for specification in overrides:
        name, separator, module = specification.partition("=")
        if not separator or name not in modules or not module or name in assigned:
            raise ValueError("--codec cần rle=<module> hoặc lzw=<module>, mỗi tên một lần")
        modules[name] = module
        assigned.add(name)
    codecs = [Codec("huffman", huffman.compress, huffman.decompress)]
    skipped = []
    for name, module_name in modules.items():
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            print(
                f"Cảnh báo: bỏ qua codec {name}: chưa có module "
                f"({module_name}; {exc})", file=sys.stderr,
            )
            skipped.append(name)
            continue
        compress = getattr(module, "compress", None)
        decompress = getattr(module, "decompress", None)
        if not callable(compress) or not callable(decompress):
            raise ValueError(f"Codec {name} ({module_name}) phải có compress và decompress")
        codecs.append(Codec(name, compress, decompress))
    return codecs, skipped


def iter_states(data: bytes, seeds: Sequence[int]) -> Iterator[tuple[str, int | None, bytes]]:
    """Tạo mỗi trạng thái trực tiếp từ cùng dữ liệu gốc."""
    yield "original", None, data
    yield "runs", None, counting_sort_runs(data)
    for seed in seeds:
        yield "shuffled", seed, fisher_yates(data, seed)


def _check_roundtrip(restored: bytes, expected_digest: bytes) -> None:
    """Từ chối đầu ra sai kiểu hoặc SHA-256 đầy đủ không khớp."""
    if not isinstance(restored, bytes):
        raise TypeError("decompress(bytes) phải trả bytes")
    if hashlib.sha256(restored).digest() != expected_digest:
        raise ValueError("Round-trip thất bại: SHA-256 đầy đủ không khớp")


def measure(codec: Codec, data: bytes, repeats: int) -> Measurement:
    """Đo trung vị không tracing; đo đỉnh nén + giải nén trong một lượt riêng."""
    if repeats <= 0:
        raise ValueError("repeats phải lớn hơn 0")
    if tracemalloc.is_tracing():
        raise RuntimeError("Cần tắt tracemalloc trước khi đo thời gian")
    expected_digest = hashlib.sha256(data).digest()
    compress_times = []
    decompress_times = []
    comp_bytes = 0
    for _ in range(repeats):
        start = time.perf_counter()
        blob = codec.compress(data)
        compress_times.append((time.perf_counter() - start) * 1000)
        if not isinstance(blob, bytes):
            raise TypeError("compress(bytes) phải trả bytes")
        start = time.perf_counter()
        restored = codec.decompress(blob)
        decompress_times.append((time.perf_counter() - start) * 1000)
        _check_roundtrip(restored, expected_digest)
        comp_bytes = len(blob)
        del blob, restored

    tracemalloc.start()
    try:
        blob = codec.compress(data)
        restored = codec.decompress(blob)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if not isinstance(blob, bytes):
        raise TypeError("compress(bytes) phải trả bytes")
    _check_roundtrip(restored, expected_digest)
    return Measurement(
        comp_bytes, median(compress_times), median(decompress_times), peak / 1024, restored,
    )


def _print_summary(
    written: int, expected: int, ran: list[str], skipped_codecs: list[str],
    skipped_files: list[str],
) -> None:
    """In số dòng thực tế, số dòng theo đầu vào khả dụng và danh sách bỏ qua."""
    print(f"Số dòng đã ghi: {written}; số dòng kỳ vọng: {expected}")
    print("Codec đã chạy: " + (", ".join(ran) or "không có"))
    print("Codec bị bỏ qua: " + (", ".join(skipped_codecs) or "không có"))
    print("File bị bỏ qua: " + (", ".join(skipped_files) or "không có"))


def main(argv: Sequence[str] | None = None) -> int:
    """Chạy RQ2; trả mã khác 0 khi thiếu toàn bộ dữ liệu hoặc gặp lỗi."""
    args = build_parser().parse_args(argv)
    if args.out.exists() and not args.overwrite:
        print(f"Lỗi: {args.out} đã tồn tại; dùng --overwrite để ghi lại.", file=sys.stderr)
        return 2
    paths = []
    skipped_files = []
    for name in R1_FILES:
        path = args.data_dir / name
        if not path.is_file():
            print(f"Cảnh báo: thiếu file {name} trong {args.data_dir}; bỏ qua.", file=sys.stderr)
            skipped_files.append(name)
        else:
            paths.append(path)
    if not paths:
        print(
            f"Lỗi: không có file R1. Đặt {', '.join(R1_FILES)} vào "
            f"{args.data_dir}, hoặc chọn --data-dir <thư mục dữ liệu>.", file=sys.stderr,
        )
        return 2
    if args.out.resolve() in {path.resolve() for path in paths}:
        print("Lỗi: --out không được trùng file dữ liệu đầu vào.", file=sys.stderr)
        return 2
    try:
        overrides = [item for group in args.codec for item in group]
        codecs, skipped_codecs = load_codecs(overrides)
    except Exception as exc:
        print(f"Lỗi nạp codec: {exc}", file=sys.stderr)
        return 2

    expected = len(paths) * (2 + len(args.seeds)) * len(codecs)
    written = 0
    ran: list[str] = []
    context = "đọc dữ liệu"
    try:
        for path in paths:
            context = f"file={path.name}"
            data = path.read_bytes()
            for state, seed, reordered in iter_states(data, args.seeds):
                context = f"file={path.name}, trạng thái={state}, seed={seed}"
                h0_bits = entropy_h0(reordered)
                for codec in codecs:
                    context = f"codec={codec.name}, file={path.name}, trạng thái={state}, seed={seed}"
                    result = measure(codec, reordered, args.repeats)
                    notes = ""
                    if codec.name == "huffman":
                        ratio = (
                            f"{(result.comp_bytes - huffman.HEADER_SIZE) / len(reordered):.6f}"
                            if reordered else ""
                        )
                        notes = f"ratio_no_header={ratio}"
                    row = {
                        "rq": "2", "dataset": "R1", "file": path.name,
                        "state": state, "seed": seed, "codec": codec.name,
                        "orig_bytes": len(reordered), "comp_bytes": result.comp_bytes,
                        "h0_bits": h0_bits, "comp_ms": result.comp_ms,
                        "decomp_ms": result.decomp_ms, "peak_mem_kib": result.peak_mem_kib,
                        "output_check": sha16(result.restored), "roundtrip_ok": True,
                        "notes": notes,
                    }
                    if written == 0:
                        args.out.parent.mkdir(parents=True, exist_ok=True)
                        if args.out.exists():
                            if not args.overwrite:
                                raise FileExistsError(f"{args.out} đã tồn tại; cần --overwrite")
                            args.out.unlink()
                    append_row(str(args.out), row)
                    written += 1
                    if codec.name not in ran:
                        ran.append(codec.name)
    except Exception as exc:
        print(f"Lỗi tại {context}: {exc}. Dừng; không ghi dòng lỗi.", file=sys.stderr)
        _print_summary(written, expected, ran, skipped_codecs, skipped_files)
        return 1
    _print_summary(written, expected, ran, skipped_codecs, skipped_files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
