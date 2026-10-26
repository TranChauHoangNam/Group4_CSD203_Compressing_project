"""RLE (Magic RLE1): payload là các cặp (count, byte), count từ 1 đến 255.
Run dài hơn 255 được tách thành nhiều cặp."""
from container import HEADER_LEN, pack_header, parse_header

MAGIC = b"RLE1"


def compress(data: bytes) -> bytes:
    data = bytes(data)
    n = len(data)
    out = bytearray(pack_header(MAGIC, n))
    i = 0
    while i < n:
        b = data[i]
        j = i + 1
        limit = i + 255 if i + 255 < n else n
        while j < limit and data[j] == b:
            j += 1
        out.append(j - i)
        out.append(b)
        i = j
    return bytes(out)


def decompress(blob: bytes) -> bytes:
    n = parse_header(blob, MAGIC)
    payload = memoryview(blob)[HEADER_LEN:]
    if len(payload) % 2:
        raise ValueError("Payload RLE phải gồm các cặp (count, byte)")
    out = bytearray()
    for k in range(0, len(payload), 2):
        count = payload[k]
        if count == 0:
            raise ValueError("count = 0 không hợp lệ")
        out += bytes((payload[k + 1],)) * count
    if len(out) != n:
        raise ValueError(f"Độ dài sau giải nén {len(out)} khác độ dài gốc trong header {n}")
    return bytes(out)
