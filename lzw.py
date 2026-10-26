"""LZW 12-bit (Magic LZW1).

- Mã 12-bit, từ điển 4.096 mục (0-255 là byte đơn). Khi đầy thì đóng băng (không reset).
- Khóa dict của bộ nén: prefix_code * 256 + byte.
- Bit đóng gói MSB first, byte cuối đệm bit 0. Hai mã liền nhau = 3 byte; mã lẻ cuối = 2 byte (4 bit đệm).
- Không có mã kết thúc: bộ giải nén dừng khi đủ độ dài gốc ghi trong header.
"""
from itertools import islice

from container import HEADER_LEN, pack_header, parse_header

MAGIC = b"LZW1"
MAX_CODES = 4096


def compress(data: bytes) -> bytes:
    data = bytes(data)
    n = len(data)
    out = bytearray(pack_header(MAGIC, n))
    if n == 0:
        return bytes(out)

    table = {}
    next_code = 256
    pending = -1  # mã 12-bit chờ ghép cặp
    w = data[0]
    for b in islice(data, 1, None):
        key = (w << 8) | b
        c = table.get(key)
        if c is not None:
            w = c
            continue
        # phát mã w
        if pending < 0:
            pending = w
        else:
            out += ((pending << 12) | w).to_bytes(3, "big")
            pending = -1
        if next_code < MAX_CODES:
            table[key] = next_code
            next_code += 1
        w = b
    # phát mã cuối
    if pending < 0:
        out += (w << 4).to_bytes(2, "big")
    else:
        out += ((pending << 12) | w).to_bytes(3, "big")
    return bytes(out)


def _iter_codes(body):
    m = len(body)
    i = 0
    while i + 3 <= m:
        v = (body[i] << 16) | (body[i + 1] << 8) | body[i + 2]
        yield v >> 12
        yield v & 0xFFF
        i += 3
    rem = m - i
    if rem == 2:
        yield ((body[i] << 8) | body[i + 1]) >> 4
    elif rem == 1:
        raise ValueError("Payload LZW bị cắt cụt")


def decompress(blob: bytes) -> bytes:
    n = parse_header(blob, MAGIC)
    if n == 0:
        if len(blob) != HEADER_LEN:
            raise ValueError("File rỗng nhưng còn payload")
        return b""

    table = [bytes((i,)) for i in range(256)]
    out = bytearray()
    prev = None
    for code in _iter_codes(memoryview(blob)[HEADER_LEN:]):
        if prev is None:
            if code >= 256:
                raise ValueError("Mã đầu tiên phải là byte đơn")
            entry = table[code]
        else:
            size = len(table)
            if code < size:
                entry = table[code]
            elif code == size:  # trường hợp đặc biệt KwKwK (vd. ABABABA)
                entry = prev + prev[:1]
            else:
                raise ValueError(f"Mã {code} chưa có trong từ điển")
            if size < MAX_CODES:
                table.append(prev + entry[:1])
        out += entry
        if len(out) > n:
            raise ValueError("Payload LZW giải nén vượt quá độ dài gốc trong header")
        prev = entry
    if len(out) != n:
        raise ValueError(f"Độ dài sau giải nén {len(out)} khác độ dài gốc trong header {n}")
    return bytes(out)
