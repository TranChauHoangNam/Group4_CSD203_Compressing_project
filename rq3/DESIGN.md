# BPE/RQ3 design - Phase 1 amendment

D1-D4, D6-D7 retain proposal labels. D5 and D8 are mandatory assignment requirements, not proposals.

[ĐX] D1. Byte-level BPE. Token ban đầu 0..255. Merge thứ i (i từ 0) tạo token 256+i từ cặp (a,b).

[ĐX] D2. Đếm cặp: đếm MỌI vị trí kề nhau (kể cả chồng lấn, ví dụ "aaa" có 2 cặp (a,a)). Thay thế: quét trái sang phải, không chồng lấn ("aaa" -> [aa, a]).

[ĐX] D3. Chọn cặp: số đếm lớn nhất; hòa thì chọn cặp (a,b) nhỏ nhất theo thứ tự từ điển trên (a,b). Mọi biến thể phải dùng ĐÚNG luật này.

[ĐX] D4. Dừng sớm: nếu cặp tốt nhất có số đếm < 2 thì dừng; số merge thực m ≤ K.

D5. Mandatory spec format: BPE1 + orig_len (8 bytes) + K field (2 bytes; store the actual number of merges m<=K) + merge table m x 3 bytes (two 12-bit ids per merge, MSB first) + token count (8 bytes) + payload of 12-bit codes, MSB first, zero-padded. Fixed 12-bit width regardless of K. All integer fields are big-endian. The 12-byte BPE1/orig_len prefix is produced by container.pack_header(b"BPE1", orig_len).

[ĐX] D6. ratio = total compressed bytes / orig_bytes, including every field and the merge table. ratio_tokens_only = payload bytes / orig_bytes. bytes_per_token = orig_bytes / n_tokens. Invalid magic raises ValueError. Fixed overhead is 22 bytes; table bytes = 3*m; payload bytes = ceil(12*n_tokens/8). Ratios with zero denominators are undefined and left blank in CSV.

[ĐX] D7. Ví dụ kiểm chứng tay (phải đúng): dữ liệu b"aaabdaaabac", K=3. Đếm cặp lần 1: aa=4, ab=2 -> merge1 = (97,97)->256, chuỗi [256,97,98,100,256,97,98,97,99]. Lần 2: (256,97)=2 và (97,98)=2 hòa -> chọn (97,98) -> 257, chuỗi [256,257,100,256,257,97,99]. Lần 3: (256,257)=2 -> 258, chuỗi [258,100,258,97,99]. Merges = [(97,97),(97,98),(256,257)], tokens = [258,100,258,97,99]. Nếu code của bạn ra khác thì DỪNG và hỏi, đừng chỉnh test cho khớp.

D7 byte accounting under mandatory D5: orig_len=11, m=3, n_tokens=5. Prefix including K field=14 bytes; merge table=9 bytes; token count=8 bytes; payload=8 bytes; total=39 bytes. ratio=39/11, ratio_tokens_only=8/11, bytes_per_token=11/5. The merge/token example itself is unchanged.

D8. Mandatory spec requirement (no proposal label): pre-tokenize with re.findall(rb" ?[^\s]+|\s+", data). Training counts pairs per UNIQUE segment weighted by segment frequency; merges never cross segment boundaries; D2 (overlapping count, left-to-right non-overlapping replace), D3, D4 apply inside each segment. encode uses a per-segment cache (dict segment -> token list). tokens = concatenation of per-segment tokens.

## Implementation and scope

Naive recounts all pairs in the current unique segment token lists every step,
weighted by their original occurrence frequencies. The fastest encoder here is
still linked-list/heap based within each segment. Its cache is local to one encode
call, so tables cannot contaminate each other's cached tokens.
encode_reference scans each merge per segment without caching, only for tests.
A test-only full-occurrence recount provides an independent training oracle;
there is no public raw-text mode that could silently ignore D8.

API K is an integer in 0..3840. CSV constraints remain separate: K=3 only for
rq=edge, normal experiment values 256/1024/3840. All three variants are now implemented in Phase 2.
Empty input with no merges produces 22 bytes. The merge table has no padding:
each pair occupies exactly 24 bits. Only an odd token count needs four trailing
zero bits in the payload. Malformed length, id, padding and magic are rejected.

This mandatory layout replaces the earlier variable-width Phase 1 layout;
old experimental blobs are not supported. No old BPE result CSV was generated.


## Phase 2: incremental weighted training

Both noheap and inc build one linked list per UNIQUE raw segment and retain
its occurrence frequency. A segment-local pair -> set of left-node positions
index includes overlapping occurrences. The global pair -> segments inverted
index restricts each merge to affected segments. Global counts are the sum of
local occurrence counts multiplied by their segment frequencies.

Replacing a left/right node pair removes the old before-left, left-right and
right-after edges before changing the links, then adds the two new adjacent
edges. Every removed/added edge changes the count by that segment's frequency.
Zero-count pairs and empty indexes are removed. Positions are processed in
ascending original order, skipping nodes consumed by earlier replacements;
this enforces D2 for aaa, aaaa and abab overlaps without crossing segments.

noheap selects the maximum by scanning the global count dictionary, using
(-count, a, b) ordering. inc maintains a heap with exactly that ordering;
stale entries are ignored unless their stored count equals the current count.
After each complete merge, only changed pairs' final nonzero counts are pushed.
Both variants use local edge updates; neither calls the naive replacement scan.

Invariant tests compare merges and encoded tokens for 15 edge cases, 200 seeded
strings (2-4 letters plus spaces/newlines, length 0..300) at K=0,1,3,16,64,256,
and the first 64 KiB of V1/E1 train at K=256. Corpus tests validate the original
file against docs/manifest.json and fail clearly if required data are missing.
No performance conclusions or Phase 3 benchmarks are part of these tests.
