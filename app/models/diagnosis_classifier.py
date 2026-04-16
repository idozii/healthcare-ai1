from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import DIAGNOSIS_CLASSIFIER_PATH, PROJECT_DATA_PATH
from app.utils.symptom_matching import enrich_sparse_query, normalize_symptom_text


class DiagnosisClassifier:
    def __init__(self, model_path: Path = DIAGNOSIS_CLASSIFIER_PATH) -> None:
        self.model_path = model_path
        self.bundle = self._load_bundle()
        self.pipeline = self.bundle["pipeline"]
        self.label_aliases: dict[str, list[str]] = self.bundle.get("label_aliases", {})

    def _load_bundle(self) -> dict[str, Any]:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Trained diagnosis classifier not found at {self.model_path}")
        bundle = joblib.load(self.model_path)
        if "pipeline" not in bundle:
            raise ValueError("Diagnosis classifier artifact is missing the 'pipeline' entry")
        return bundle

    def is_ready(self) -> bool:
        return self.model_path.exists()

    def predict(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        normalized_query = enrich_sparse_query(normalize_symptom_text(text))
        proba = self.pipeline.predict_proba([normalized_query])[0]
        classes = list(self.pipeline.classes_)
        order = np.argsort(proba)[::-1][:top_k]
        return [
            {
                "predicted_label": str(classes[idx]),
                "confidence": float(proba[idx]),
                "retrieval_mode": "diagnosis_classifier",
            }
            for idx in order
        ]

    @staticmethod
    def load_training_data(path: Path = PROJECT_DATA_PATH) -> pd.DataFrame:
        df = pd.read_csv(path)
        required = {"text", "disease"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"diagnosis dataset is missing required columns: {sorted(missing)}")
        return df.fillna("")
