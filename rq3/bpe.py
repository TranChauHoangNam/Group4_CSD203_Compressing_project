"""Giao diện BPE; Cặp 3 quyết định cấu trúc merges và tokens khi cài đặt.

variant thuộc {"inc", "noheap", "naive"}; k thuộc {256, 1024, 3840}.
k=3 chỉ là ngoại lệ minh họa trong test gọi trực tiếp, không ghi CSV.
"""


def train(data: bytes, k: int, variant: str):
    """Trả về merges học từ data với k phép gộp và biến thể variant.

    Cấu trúc merges chưa chốt. Cho phép k=3 cho ví dụ aaabdaaabac.
    """
    raise NotImplementedError


def encode(data: bytes, merges):
    """Trả về tokens bằng bảng merges đã huấn luyện; cấu trúc tokens chưa chốt."""
    raise NotImplementedError


def decode(tokens, merges) -> bytes:
    """Khôi phục bytes từ tokens và bảng merges tương ứng."""
    raise NotImplementedError


def compress(data: bytes, k: int, variant: str) -> bytes:
    """Huấn luyện và đóng gói BPE thành bytes.

    Khi cài đặt, dùng container.pack_header(b"BPE1", len(data)).
    Cách tuần tự hóa bảng merge và tokens cần được Cặp 3 thống nhất.
    """
    raise NotImplementedError


def decompress(blob: bytes) -> bytes:
    """Đọc container magic b'BPE1', bảng merge, tokens và khôi phục bytes gốc."""
    raise NotImplementedError
