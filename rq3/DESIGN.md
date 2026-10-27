# BPE implementation contract

1. Initial tokens are bytes 0..255; merge i creates token 256+i, at most 4095.
2. Split input with `re.findall(rb" ?[^\s]+|\s+", data)`. Preserve every byte;
   never merge across segment boundaries. Weight unique segments by frequency.
   Encode caches each unique segment per call.
3. Count all adjacent pairs including overlaps. Select greatest weighted count,
   breaking ties by smallest (a,b). Replace left-to-right without overlaps.
4. Continue until K merges or no adjacent pair remains. Count 1 is eligible:
   ab, K=1 yields (97,98). The former count<2 stop was removed to follow the
   assignment literally. Empty input and one-byte segments can stop before K.
5. inc maintains linked lists, pair positions and an inverted pair index;
   only affected edges are updated. The heap uses (-count,a,b) and lazy deletion.
   noheap uses the same updates but scans the count dictionary to select a pair.
   naive recounts every unique segment each round with frequency weights.
6. Format: BPE1 + original length u64 + actual merge count u16 + 3 bytes per
   merge (two 12-bit IDs) + token count u64 + fixed 12-bit token payload.
   All integers and bits are big-endian/MSB-first; final padding bits are zero.
   Invalid magic, merge DAG, token IDs, lengths, padding and extra bytes are rejected.
7. aaabdaaabac, K=3 gives (97,97), (97,98), (256,257) and tokens
   [258,100,258,97,99]. Total container size is 39 bytes, including 8 payload bytes.
8. ratio=(22+3*m+ceil(12*n_tokens/8))/orig_bytes;
   ratio_tokens_only=ceil(12*n_tokens/8)/orig_bytes;
   bytes_per_token=orig_bytes/n_tokens. Empty-input ratios are undefined.

## Measurement contract

All primary RQ3 models train on the full manifest-validated V1/E1 train inputs
(nominal 1 MiB, V1 is one byte shorter to preserve UTF-8). All tests use full
1 MiB files. K is 256/1024/3840 for all three variants. inc/noheap training is
median-of-three, naive is one measured run. Compression/decompression is
median-of-three, excluding training; peak allocation is traced separately.
Every timed and memory round-trip validates full SHA-256.

The four high-K full naive training measurements originally lived in
final_submission/naive_full_experiment.json. rq3.upgrade_full validates their
input and merge hashes against current inc training, archives the mixed-scope
records, and imports the actual measured times with provenance. The eight test
rows are measured afresh. Historical times are not relabelled as new.

Training memory remains a separate experiment: identical 128 KiB prefixes,
K=256, one traced run. This is not the full-corpus training-time matrix.
