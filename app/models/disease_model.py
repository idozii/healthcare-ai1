import faiss
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    DISEASES_CSV_PATH,
    DISEASE_EMBEDDINGS_PATH,
    HYBRID_DENSE_WEIGHT,
    MIN_DISEASE_CONFIDENCE,
    RETRIEVAL_CANDIDATE_POOL,
)
from app.utils.symptom_matching import (
    clinical_boost,
    confidence_threshold_for_query,
    detect_intents,
    enrich_sparse_query,
    normalize_symptom_text,
    retrieval_delta_for_intent,
)


class DiseaseRetriever:
    def __init__(self, embedding_model) -> None:
        self.embedding_model = embedding_model
        self.df = pd.read_csv(DISEASES_CSV_PATH)
        self.df = self.df.fillna("")
        self.disease_names = self.df.get("disease_name", "").astype(str).tolist()
        self.descriptions = self.df.get("description", "").astype(str).tolist()
        self.mapped_departments = self.df.get("mapped_departments", "").astype(str).tolist()

        self.corpus = (
            pd.Series(self.disease_names)
            + " "
            + pd.Series(self.descriptions)
            + " "
            + pd.Series(self.mapped_departments)
        ).tolist()

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.lexical_matrix = self.vectorizer.fit_transform(self.corpus)

        self.embeddings = self._load_or_build_embeddings()
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def _load_or_build_embeddings(self) -> np.ndarray:
        if DISEASE_EMBEDDINGS_PATH.exists():
            emb = np.load(DISEASE_EMBEDDINGS_PATH)
            if emb.shape[0] == len(self.df):
                return emb.astype(np.float32)

        if "description" not in self.df.columns:
            raise ValueError("diseases.csv must contain a 'description' column")

        texts = self.df["description"].astype(str).tolist()
        emb = self.embedding_model.encode_many(texts).astype(np.float32)
        np.save(DISEASE_EMBEDDINGS_PATH, emb)
        return emb

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        if len(self.df) == 0:
            return []

        normalized_query = enrich_sparse_query(normalize_symptom_text(text))
        intents = detect_intents(normalized_query)

        q_lex = self.vectorizer.transform([normalized_query])
        lexical_scores = cosine_similarity(q_lex, self.lexical_matrix).ravel()

        vec = self.embedding_model.encode(normalized_query)
        candidate_pool = min(max(top_k * 20, RETRIEVAL_CANDIDATE_POOL), len(self.df))
        distances, semantic_idx = self.index.search(np.array([vec], dtype=np.float32), candidate_pool)

        semantic_scores = np.zeros(len(self.df), dtype=np.float32)
        semantic_scores[semantic_idx[0]] = np.maximum(0.0, 1.0 - (distances[0] / 2.0))

        lexical_top = np.argsort(lexical_scores)[::-1][:candidate_pool]
        candidate_idx = np.unique(np.concatenate([semantic_idx[0], lexical_top]))

        rows = []
        alpha = HYBRID_DENSE_WEIGHT
        for idx in candidate_idx:
            i = int(idx)
            s_score = float(semantic_scores[i])
            l_score = float(lexical_scores[i])
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
            hybrid = max(0.0, min(1.0, alpha * s_score + (1.0 - alpha) * l_score + boost + intent_delta))
            rows.append(
                {
                    "idx": i,
                    "hybrid_score": hybrid,
                    "semantic_score": s_score,
                    "lexical_score": l_score,
                }
            )

        if not rows:
            return []

        rank_df = pd.DataFrame(rows).sort_values("hybrid_score", ascending=False)
        best_score = float(rank_df["hybrid_score"].iloc[0])
        min_conf = confidence_threshold_for_query(normalized_query, MIN_DISEASE_CONFIDENCE)
        if best_score < min_conf:
            return []

        if "headache" in intents:
            headache_mask = (
                self.df["disease_name"].str.contains(r"migraine|headache", case=False, regex=True, na=False)
                | self.df["description"].str.contains(r"migraine|headache|one-sided|unilateral|throbbing|photophobia|aura", case=False, regex=True, na=False)
            )
            rank_df = rank_df.loc[rank_df["idx"].isin(self.df.index[headache_mask])].copy()
            if rank_df.empty:
                return []

        take = rank_df.head(top_k).copy()
        matches = self.df.iloc[take["idx"].tolist()].copy().reset_index(drop=True)
        matches["confidence"] = take["hybrid_score"].values
        matches["semantic_score"] = take["semantic_score"].values
        matches["lexical_score"] = take["lexical_score"].values
        matches["distance"] = 1.0 - matches["confidence"]
        matches["retrieval_mode"] = "semantic_hybrid"
        return matches.to_dict(orient="records")
