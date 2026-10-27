"""Analyze feasibility measurements; all extrapolations are ESTIMATES."""
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rq3/out"


def fit(rows, predictor):
    # Least squares log(time_ms) = a + b*log(bytes) + c*log(actual merges).
    features = [[1.0, math.log(r[predictor]), math.log(r["m"])] for r in rows]
    targets = [math.log(r["train_ms"]) for r in rows]
    matrix = [[sum(x[i] * x[j] for x in features) for j in range(3)]
              + [sum(x[i] * y for x, y in zip(features, targets))] for i in range(3)]
    for pivot in range(3):
        best = max(range(pivot, 3), key=lambda j: abs(matrix[j][pivot]))
        matrix[pivot], matrix[best] = matrix[best], matrix[pivot]
        divisor = matrix[pivot][pivot]
        if abs(divisor) < 1e-12:
            raise ValueError("Singular fit")
        matrix[pivot] = [v / divisor for v in matrix[pivot]]
        for j in range(3):
            if j != pivot:
                scale = matrix[j][pivot]
                matrix[j] = [v - scale * w for v, w in zip(matrix[j], matrix[pivot])]
    return [matrix[i][3] for i in range(3)]


def predict(coefficients, size, merges):
    a, b, c = coefficients
    return math.exp(a + b * math.log(size) + c * math.log(merges)) / 1000


def analyze(report):
    results = {"label": "ESTIMATE", "method": "log(T_ms)=a+b*log(X)+c*log(m)",
               "cv": "leave-one-prefix-size-out (both K rows held out together)",
               "range": "min/max of both predictor models and their four CV refits; sensitivity envelope, NOT confidence interval",
               "assumption": "extrapolation assumes m=K; possible early stopping and shrinking pair dictionaries are not modeled",
               "models": {}, "extrapolations": []}
    for variant in ("naive", "noheap"):
        rows = [c for c in report["cells"] if c["scope"] == "prefix" and c["variant"] == variant]
        models = {}
        for predictor in ("raw_bytes", "unique_bytes"):
            coefficients = fit(rows, predictor)
            errors, folds = [], []
            for size in sorted({r["raw_bytes"] for r in rows}):
                train = [r for r in rows if r["raw_bytes"] != size]
                test = [r for r in rows if r["raw_bytes"] == size]
                fold = fit(train, predictor)
                folds.append(fold)
                for r in test:
                    predicted = predict(fold, r[predictor], r["m"]) * 1000
                    errors.append(abs(predicted - r["train_ms"]) / r["train_ms"] * 100)
            models[predictor] = {"coefficients": coefficients, "cv_mape_percent": mean(errors), "fold_coefficients": folds}
        results["models"][variant] = models
        print(variant, 'CV MAPE:', {p: round(m['cv_mape_percent'], 3) for p, m in models.items()},
              'better:', min(models, key=lambda p: models[p]['cv_mape_percent']))
        for corpus in ("V1", "E1"):
            stat = next(s for s in report["segments"] if s["corpus"] == corpus and s["size_kib_label"] == 1024)
            for k in (256, 1024, 3840):
                values, central = [], {}
                for predictor, model in models.items():
                    central[predictor] = predict(model["coefficients"], stat[predictor], k)
                    values += [central[predictor]] + [predict(c, stat[predictor], k) for c in model["fold_coefficients"]]
                row = {"label": "ESTIMATE", "corpus": corpus, "variant": variant, "k": k,
                       "assumed_m": k, "central_seconds": central,
                       "range_seconds": [min(values), max(values)],
                       "cross_corpus_transfer": corpus != "V1"}
                results["extrapolations"].append(row)
                print(row)
    return results


def main():
    report = json.loads((OUT / "phase3_measurements.json").read_text(encoding="utf-8"))
    results = analyze(report)
    (OUT / "phase3_estimates.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
