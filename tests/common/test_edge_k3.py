"""K=3 chỉ được ghi CSV cho edge; không nới tập K còn lại."""
import csv

import pytest

from common.results_schema import append_row, sha16


@pytest.mark.parametrize("rq", ["edge", "1", "2", "3"])
@pytest.mark.parametrize("k", [3, "3", 64, 256, 1024, 3840])
def test_k_scope(tmp_path, rq, k):
    row = {"rq": rq, "dataset": "" if rq == "edge" else "V1",
           "state": "original", "codec": "bpe", "train_variant": "naive",
           "k_merges": k, "orig_bytes": 11, "comp_bytes": 31,
           "roundtrip_ok": True, "status": "ok", "comp_ms": 1, "decomp_ms": 1, "output_check": sha16(b"aaabdaaabac")}
    path = tmp_path / "result.csv"
    if int(k) in {256, 1024, 3840} or (rq == "edge" and int(k) == 3):
        append_row(str(path), row)
        with path.open(encoding="utf-8", newline="") as stream:
            assert next(csv.DictReader(stream))["k_merges"] == str(k)
    else:
        with pytest.raises(ValueError, match="k_merges"):
            append_row(str(path), row)
        assert not path.exists()
