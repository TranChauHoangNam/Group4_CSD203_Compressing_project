"""Pipeline nạp V1 (Wikipedia tiếng Việt) và E1 (tiếng Anh).

Chuẩn hóa NFC, UTF-8. Mọi lần cắt đều rơi vào ranh giới ký tự UTF-8 (nên file có thể
nhỏ hơn danh nghĩa vài byte; cột orig_bytes trong CSV ghi kích thước thật).

Đầu ra trong --data-dir:
  v1_train_1mib.txt, v1_test_1mib.txt   (1 MiB đầu / 1 MiB kế tiếp)
  e1_train_1mib.txt, e1_test_1mib.txt
  v1_256kib.txt ... v1_4096kib.txt      (tiền tố của V1, dùng cho RQ1)
  manifest.json                         (phiên bản dữ liệu, kích thước, SHA-256)

Chạy:  python prepare_wiki.py --data-dir data/wiki
Cần:   pip install datasets   (đọc streaming, chỉ tải vài MiB đầu)

Cặp 2, Cặp 3 dùng:  from prepare_wiki import load_corpus;  load_corpus("V1", "test")
"""
import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

MIB = 1024 * 1024
RQ1_SIZES_KIB = (256, 512, 1024, 2048, 4096)
HF_DATASET = "wikimedia/wikipedia"
HF_VERSION = "20231101"


def cut(b: bytes, start: int, n: int):
    """Cắt tối đa n byte từ start, lùi về ranh giới ký tự UTF-8. Trả về (start, end)."""
    end = min(start + n, len(b))
    if end < len(b):
        while end > start and (b[end] & 0xC0) == 0x80:
            end -= 1
    return start, end


def normalize(text: str) -> bytes:
    return (unicodedata.normalize("NFC", text).strip() + "\n\n").encode("utf-8")


def stream_from_hf(lang: str, target_bytes: int) -> bytes:
    try:
        from datasets import load_dataset  # import muộn để phần còn lại chạy được khi chưa cài
    except ModuleNotFoundError as exc:
        if exc.name != "datasets":
            raise
        raise SystemExit(
            "Missing optional package 'datasets' for Wikipedia download. For Python 3.14 on Windows, run: "
            "python -m pip install --upgrade pip setuptools wheel; "
            "python -m pip install --only-binary=:all: PyYAML==6.0.3; "
            "python -m pip install datasets. Or pass both --vi-file and --en-file "
            "with local UTF-8 text files to avoid installing datasets."
        ) from None

    ds = load_dataset(HF_DATASET, f"{HF_VERSION}.{lang}", split="train", streaming=True)
    chunks, total = [], 0
    for row in ds:
        if not row["text"].strip():
            continue
        c = normalize(row["text"])
        chunks.append(c)
        total += len(c)
        if total >= target_bytes:
            break
    return b"".join(chunks)


def stream_from_file(path: str) -> bytes:
    return normalize(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, data: bytes, manifest: dict):
    path.write_bytes(data)
    manifest["files"][path.name] = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def build(prefix: str, stream: bytes, out_dir: Path, manifest: dict, rq1_sizes_kib=()):
    """prefix = 'v1' hoặc 'e1'. Tạo train/test 1 MiB và các tiền tố RQ1."""
    need = (2 * MIB if not rq1_sizes_kib else max(2 * MIB, max(rq1_sizes_kib) * 1024))
    if len(stream) < need:
        raise SystemExit(f"{prefix}: luồng văn bản chỉ có {len(stream)} byte, cần ít nhất {need}")
    s0, e1 = cut(stream, 0, MIB)
    s1, e2 = cut(stream, e1, MIB)
    _write(out_dir / f"{prefix}_train_1mib.txt", stream[s0:e1], manifest)
    _write(out_dir / f"{prefix}_test_1mib.txt", stream[s1:e2], manifest)
    for kib in rq1_sizes_kib:
        a, b = cut(stream, 0, kib * 1024)
        _write(out_dir / f"{prefix}_{kib}kib.txt", stream[a:b], manifest)


def load_corpus(name: str, part: str, data_dir="data/wiki") -> bytes:
    """name: 'V1' | 'E1'; part: 'train' | 'test'. Trả về bytes UTF-8 (NFC)."""
    return (Path(data_dir) / f"{name.lower()}_{part}_1mib.txt").read_bytes()


def load_v1_prefix(size_kib: int, data_dir="data/wiki") -> bytes:
    return (Path(data_dir) / f"v1_{size_kib}kib.txt").read_bytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/wiki")
    ap.add_argument("--vi-file", help="(tùy chọn) dùng file văn bản tiếng Việt thay vì tải Hugging Face")
    ap.add_argument("--en-file", help="(tùy chọn) dùng file văn bản tiếng Anh thay vì tải Hugging Face")
    a = ap.parse_args()

    out = Path(a.data_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "local files" if (a.vi_file or a.en_file) else f"{HF_DATASET} {HF_VERSION}",
        "normalization": "NFC, UTF-8, bài viết nối bằng dòng trống",
        "cut_rule": "cắt tại ranh giới ký tự UTF-8, kích thước <= danh nghĩa",
        "files": {},
    }
    max_kib = max(RQ1_SIZES_KIB)
    vi = stream_from_file(a.vi_file) if a.vi_file else stream_from_hf("vi", max_kib * 1024 + 64 * 1024)
    build("v1", vi, out, manifest, RQ1_SIZES_KIB)
    en = stream_from_file(a.en_file) if a.en_file else stream_from_hf("en", 2 * MIB + 64 * 1024)
    build("e1", en, out, manifest)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    for name, info in manifest["files"].items():
        print(f"{name:24s} {info['bytes']:>9d} byte  sha256={info['sha256'][:16]}")


if __name__ == "__main__":
    main()
