from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.symptom_matching import enrich_sparse_query, normalize_symptom_text


DEFAULT_DATASET = PROJECT_ROOT / "diagnosis_dataset.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "app" / "data" / "diagnosis_classifier.joblib"
DEFAULT_REPORT = PROJECT_ROOT / "app" / "data" / "diagnosis_classifier_report.json"


def _prepare_text(text: str) -> str:
    return enrich_sparse_query(normalize_symptom_text(text))


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).fillna("")
    required = {"text", "disease"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")
    df = df[["text", "disease"]].copy()
    df["text"] = df["text"].astype(str).map(_prepare_text)
    df["disease"] = df["disease"].astype(str).str.strip()
    df = df[(df["text"].str.len() > 0) & (df["disease"].str.len() > 0)]
    return df


def train_classifier(df: pd.DataFrame) -> tuple[Pipeline, dict[str, object]]:
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"].tolist(),
        df["disease"].tolist(),
        test_size=0.2,
        random_state=42,
        stratify=df["disease"],
    )

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    lowercase=True,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    report = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_test, y_pred, average="weighted")),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }
    return pipeline, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a symptom-to-disease classifier from diagnosis_dataset.csv")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="Path to diagnosis_dataset.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to write the trained model artifact")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Path to write the training metrics report")
    args = parser.parse_args()

    df = load_dataset(args.data)
    pipeline, report = train_classifier(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "pipeline": pipeline,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": str(args.data),
        "rows": int(len(df)),
        "classes": sorted(df["disease"].unique().tolist()),
        "metrics": report,
    }
    joblib.dump(bundle, args.output)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved classifier to {args.output}")
    print(f"Saved metrics report to {args.report}")
    print(f"Rows: {len(df)} | Classes: {len(bundle['classes'])} | Accuracy: {report['accuracy']:.3f} | Macro F1: {report['macro_f1']:.3f}")


if __name__ == "__main__":
    main()
