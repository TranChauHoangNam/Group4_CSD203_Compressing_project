"""Tổng hợp CSV RQ2 bằng csv/statistics và vẽ bằng matplotlib đã cài sẵn."""
from __future__ import annotations

import argparse
import csv
from io import BytesIO, StringIO
import math
from pathlib import Path
from statistics import mean

STATES = ("original", "runs", "shuffled")
CODECS = ("huffman", "rle", "lzw")
GAP_COLUMNS = ("ratio_minus_h0", "tốt hơn mốc H0/8?")
RATIO_COLUMNS = ("file", "codec", "state", "ratio", "ratio_min", "ratio_max", "h0_ratio", "ratio_no_header") + GAP_COLUMNS
SPEED_METRICS = ("comp_kibs", "decomp_kibs", "peak_mem_kib")
SPEED_COLUMNS = ("file", "codec", "state") + SPEED_METRICS + GAP_COLUMNS
COMPARISON_COLUMNS = ("file", "state", "huffman", "rle", "lzw", "codec thắng (ratio nhỏ nhất)", "chênh lệch với hạng nhì")


def fmt(value):
    """Một quy tắc trình bày dùng chung cho bảng, hình và văn bản."""
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def summarize(rows):
    """Một dòng mỗi (file, codec, state); mỗi seed shuffled có trọng số bằng nhau.

    comp/decomp_kibs là trung bình các throughput đã có trong CSV, không phải
    throughput tính lại từ thời gian trung bình. Repeats đã được runner tổng hợp.
    """
    groups = {}
    for row in rows:
        key = (row["file"], row["codec"], row["state"])
        if key[1] not in CODECS or key[2] not in STATES:
            raise ValueError(f"Codec/state không hợp lệ: {key}")
        if row.get("roundtrip_ok") != "true":
            raise ValueError(f"Round-trip không đạt: {key}")
        groups.setdefault(key, []).append(row)
    ratio_rows, speed_rows = [], []

    def numbers(group, column):
        values = [float(row[column]) for row in group]
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError(f"{column} phải hữu hạn và không âm")
        return values

    order = lambda key: (key[0], CODECS.index(key[1]), STATES.index(key[2]))
    for key in sorted(groups, key=order):
        group = groups[key]
        if key[2] == "shuffled":
            seeds = [row.get("seed", "") for row in group]
            if "" in seeds or len(set(seeds)) != len(seeds):
                raise ValueError(f"Thiếu/trùng seed: {key}")
        elif len(group) != 1 or group[0].get("seed", "") != "":
            raise ValueError(f"original/runs phải đúng một dòng và seed rỗng: {key}")
        base = dict(zip(("file", "codec", "state"), key))
        ratios = numbers(group, "ratio")
        h0_values = numbers(group, "h0_ratio")
        if max(h0_values) - min(h0_values) >= 1e-9:
            raise ValueError(f"Mốc H0/8 không đồng nhất: {key}")
        payload = ""
        if key[1] == "huffman":
            values = []
            for row in group:
                prefix, separator, value = row.get("notes", "").partition("=")
                if prefix != "ratio_no_header" or not separator:
                    raise ValueError(f"Thiếu notes ratio_no_header: {key}")
                values.append(float(value))
            if any(not math.isfinite(value) or value < 0 for value in values):
                raise ValueError(f"Payload ratio không hợp lệ: {key}")
            payload = mean(values)
        gap = mean(ratios) - mean(h0_values)
        extra = {"ratio_minus_h0": gap, "tốt hơn mốc H0/8?": "có" if gap < 0 else "không"}
        ratio_rows.append({**base, **extra, "ratio": mean(ratios), "ratio_min": min(ratios),
                           "ratio_max": max(ratios), "h0_ratio": mean(h0_values),
                           "ratio_no_header": payload})
        speed_rows.append({**base, **extra, **{column: mean(numbers(group, column))
                                     for column in SPEED_METRICS}})
    return ratio_rows, speed_rows


def write_unchanged_or_new(path: Path, content: bytes, overwrite=False):
    """Mặc định giữ bảo vệ cũ; --overwrite cho phép tái sinh đầu ra đã được yêu cầu."""
    if path.exists():
        if path.read_bytes() != content:
            if not overwrite:
                raise FileExistsError(f"File đích khác nội dung: {path}; dùng --overwrite để tái sinh")
            path.write_bytes(content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def table_markdown(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines += ["| " + " | ".join(fmt(row[column]) for column in columns) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def compare_codecs(ratio_rows):
    result = []
    for file in sorted({r["file"] for r in ratio_rows}):
        for state in STATES:
            values = {r["codec"]: r["ratio"] for r in ratio_rows if r["file"] == file and r["state"] == state}
            ordered = sorted(values.values())
            result.append({"file": file, "state": state, **values,
                           "codec thắng (ratio nhỏ nhất)": ", ".join(c for c in CODECS if values[c] == ordered[0]),
                           "chênh lệch với hạng nhì": ordered[1] - ordered[0]})
    return result


def write_tables(out_dir: Path, ratio_rows, speed_rows, overwrite=False):
    for name, rows, columns in [("rq2_table_ratio", ratio_rows, RATIO_COLUMNS),
                                ("rq2_table_speed", speed_rows, SPEED_COLUMNS),
                                ("rq2_table_comparison", compare_codecs(ratio_rows), COMPARISON_COLUMNS)]:
        stream = StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        write_unchanged_or_new(out_dir / (name + ".csv"), stream.getvalue().encode("utf-8"), overwrite)
        write_unchanged_or_new(out_dir / (name + ".md"), table_markdown(rows, columns).encode("utf-8"), overwrite)


def plot_results(out_dir: Path, ratio_rows, speed_rows, overwrite=False):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Cần matplotlib đã cài. Hỏi người dùng trước khi cài; không tự pip install.") from exc
    all_files = sorted({row["file"] for row in ratio_rows})
    colors = ("white", "#c0c0c0", "#eeeeee")
    hatches = ("//", "..", "xx")
    for rows, metric, filename, title, ylabel in [
        (ratio_rows, "ratio", "rq2_ratio.png", "RQ2 — Tỷ lệ nén theo thứ tự byte", "Tỷ lệ nén (byte/byte)"),
        (speed_rows, "comp_kibs", "rq2_speed.png", "RQ2 — Thông lượng nén theo thứ tự byte", "Thông lượng nén (KiB/s)"),
    ]:
        files = all_files if metric == "ratio" else [f for f in all_files if f in ("kennedy.xls", "v1_test_1mib.txt")]
        if not files:
            continue
        fig, axes = plt.subplots(len(files), 1, figsize=(12, 4.5 * len(files)), squeeze=False)
        lookup = {(r["file"], r["codec"], r["state"]): r for r in rows}
        for ax, file in zip(axes[:, 0], files):
            maxima = []
            for index, codec in enumerate(CODECS):
                values = [lookup[(file, codec, state)][metric] for state in STATES]
                positions = [i + (index - 1) * .25 for i in range(len(STATES))]
                bars = ax.bar(positions, values, width=.24, label=codec, color=colors[index],
                              hatch=hatches[index], edgecolor="black", linewidth=.5)
                ax.bar_label(bars, labels=[fmt(v) for v in values], padding=4, fontsize=9,
                             bbox=dict(facecolor="white", edgecolor="none", pad=.6))
                maxima.extend(values)
            if metric == "ratio":
                h0 = next(r["h0_ratio"] for r in ratio_rows if r["file"] == file)
                ax.axhline(h0, color="black", linestyle="--", linewidth=1.3, label="H0/8")
                ax.text(.99, .96, f"H0/8 = {fmt(h0)}", transform=ax.transAxes, ha="right", va="top", fontsize=9)
                maxima.append(h0)
                ax.set_yscale("log")
                ax.set_ylim(min(maxima) / 2, max(maxima) * 2.2)
            else:
                ax.set_ylim(0, max(maxima) * 1.25 if max(maxima) else 1)
            ax.set_title(file, fontsize=11)
            ax.set_xticks(range(len(STATES)), STATES)
            ax.set_xlabel("Trạng thái byte")
            ax.set_ylabel(ylabel)
            ax.grid(axis="y", alpha=.25)
            ax.set_axisbelow(True)
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .96), ncol=4)
        fig.suptitle(title, fontsize=15, y=.99)
        fig.text(.5, .01, "shuffled: trung bình các seed; nhãn dùng cùng định dạng số với bảng" +
                 ("; trục tỷ lệ log" if metric == "ratio" else "; chỉ so sánh hai file lớn"), ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .035, 1, .93))
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=160)
        plt.close(fig)
        write_unchanged_or_new(out_dir / filename, buffer.getvalue(), overwrite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("results_rq2_all.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("rq2/out"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--report", type=Path, help="Tái sinh báo cáo và bảng truy vết")
    parser.add_argument("--mechanism-output", type=Path, default=Path("rq2/out/mechanism_output.txt"))
    args = parser.parse_args(argv)
    ratio_rows, speed_rows = summarize(read_rows(args.csv))
    write_tables(args.out_dir, ratio_rows, speed_rows, args.overwrite)
    plot_results(args.out_dir, ratio_rows, speed_rows, args.overwrite)
    if args.report:
        from rq2.build_report import build_report
        build_report(args.csv, args.out_dir, args.report, args.mechanism_output, args.overwrite)
    print(f"Đã tạo {len(ratio_rows)} dòng bảng tỷ lệ, {len(speed_rows)} dòng bảng tốc độ, "
          f"{len(compare_codecs(ratio_rows))} dòng so sánh và 2 hình tại {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
