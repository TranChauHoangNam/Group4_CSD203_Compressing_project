"""Dataset trống chỉ hợp lệ với rq=edge."""
import csv

import pytest

from common.results_schema import append_row, sha16


@pytest.mark.parametrize("dataset", ["", None, "missing"])
@pytest.mark.parametrize("rq", ["edge", "1", "2", "3"])
def test_blank_dataset_only_for_edge(tmp_path, dataset, rq):
    row = {
        "rq": rq, "state": "original", "codec": "bpe",
        "orig_bytes": 0, "comp_bytes": 12,
        "output_check": sha16(b""), "roundtrip_ok": True,
    }
    if dataset != "missing":
        row["dataset"] = dataset
    path = tmp_path / "results.csv"
    if rq == "edge":
        append_row(str(path), row)
        with path.open(encoding="utf-8", newline="") as stream:
            assert next(csv.DictReader(stream))["dataset"] == ""
    else:
        with pytest.raises(ValueError, match="dataset"):
            append_row(str(path), row)
        assert not path.exists()


def test_edge_still_rejects_unknown_dataset(tmp_path):
    with pytest.raises(ValueError, match="dataset"):
        append_row(str(tmp_path / "results.csv"), {
            "rq": "edge", "dataset": "unknown", "state": "original",
            "codec": "bpe", "orig_bytes": 0, "comp_bytes": 12,
            "output_check": sha16(b""), "roundtrip_ok": True,
        })
