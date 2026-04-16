import logging
from collections import OrderedDict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    DISEASES_CSV_PATH,
    FORCE_OFFLINE_RETRIEVER,
    MIN_DISEASE_CONFIDENCE,
    RETRIEVAL_QUERY_CACHE_SIZE,
)
from app.models.disease_model import DiseaseRetriever
from app.models.embedding import EmbeddingModel
from app.utils.symptom_matching import (
    clinical_boost,
    confidence_threshold_for_query,
    detect_intents,
    enrich_sparse_query,
    normalize_symptom_text,
    retrieval_delta_for_intent,
)


logger = logging.getLogger(__name__)


class OfflineDiseaseRetriever:
    """Fallback retriever that does not require external model downloads."""

    def __init__(self) -> None:
        self.df = pd.read_csv(DISEASES_CSV_PATH).fillna("")
        self.disease_names = self.df.get("disease_name", "").astype(str).tolist()
        self.descriptions = self.df.get("description", "").astype(str).tolist()
        self.mapped_departments = self.df.get("mapped_departments", "").astype(str).tolist()
        text_parts = []
        for i in range(len(self.df)):
            text = " ".join(
                [
                    self.disease_names[i],
                    self.descriptions[i],
                    self.mapped_departments[i],
                ]
            ).strip()
            text_parts.append(text)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(text_parts)

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        normalized_query = enrich_sparse_query(normalize_symptom_text(text))
        intents = detect_intents(normalized_query)

        q = self.vectorizer.transform([normalized_query])
        sim = cosine_similarity(q, self.matrix).ravel()

        adjusted = np.zeros_like(sim, dtype=float)
        for i in range(len(self.df)):
            boost = clinical_boost(
                disease_name=self.disease_names[i],
                description=self.descriptions[i],
                mapped_departments=self.mapped_departments[i],
                intents=intents,
            )
            intent_delta = retrieval_delta_for_intent(
                mapped_departments=self.mapped_departments[i],
                intents=intents,
                normalized_text=normalized_query,
            )
            adjusted[i] = max(0.0, min(1.0, float(sim[i]) + boost + intent_delta))

        min_conf = confidence_threshold_for_query(normalized_query, MIN_DISEASE_CONFIDENCE)
        if float(adjusted.max()) < min_conf:
            return []

        top_idx = adjusted.argsort()[::-1][:top_k]

        if "headache" in intents:
            headache_mask = (
                self.df["disease_name"].str.contains(r"migraine|headache", case=False, regex=True, na=False)
                | self.df["description"].str.contains(r"migraine|headache|one-sided|unilateral|throbbing|photophobia|aura", case=False, regex=True, na=False)
            )
            allowed_idx = np.flatnonzero(headache_mask.to_numpy())
            top_idx = np.array([idx for idx in top_idx if idx in set(allowed_idx)], dtype=int)
            if top_idx.size == 0:
                return []

        matches = self.df.iloc[top_idx].copy()
        matches["confidence"] = adjusted[top_idx]
        matches["lexical_score"] = sim[top_idx]
        matches["distance"] = 1.0 - adjusted[top_idx]
        matches["retrieval_mode"] = "offline_tfidf"
        return matches.to_dict(orient="records")


class DiseaseService:
    def __init__(self) -> None:
        self.mode = "unknown"
        self.init_error = ""
        self._query_cache: OrderedDict[tuple[str, int], list[dict]] = OrderedDict()
        self._cache_size = max(16, int(RETRIEVAL_QUERY_CACHE_SIZE))

        if FORCE_OFFLINE_RETRIEVER:
            self.retriever = OfflineDiseaseRetriever()
            self.mode = "offline_tfidf_forced"
            logger.info("DiseaseService initialized in offline_tfidf_forced mode")
            return

        try:
            self.embedding_model = EmbeddingModel()
            self.retriever = DiseaseRetriever(self.embedding_model)
            self.mode = "semantic_faiss"
            logger.info("DiseaseService initialized in semantic_faiss mode")
        except Exception as exc:
            self.init_error = str(exc)
            logger.warning("Falling back to offline TF-IDF retriever: %s", exc)
            self.retriever = OfflineDiseaseRetriever()
            self.mode = "offline_tfidf"

    def get_diseases(self, text: str, top_k: int = 5) -> list[dict]:
        cache_key = (enrich_sparse_query(normalize_symptom_text(text)), int(top_k))
        cached = self._query_cache.get(cache_key)
        if cached is not None:
            self._query_cache.move_to_end(cache_key)
            return [dict(item) for item in cached]

        out = self.retriever.query(text=text, top_k=top_k)

        self._query_cache[cache_key] = [dict(item) for item in out]
        if len(self._query_cache) > self._cache_size:
            self._query_cache.popitem(last=False)
        return out

    def get_mode(self) -> str:
        return self.mode
