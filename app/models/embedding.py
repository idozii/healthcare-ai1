from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import ALLOW_MODEL_DOWNLOAD, EMBEDDING_MODEL_NAME


class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self.model = SentenceTransformer(
            model_name,
            local_files_only=not ALLOW_MODEL_DOWNLOAD,
        )

    def encode(self, text: str) -> np.ndarray:
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        return np.asarray(embedding, dtype=np.float32)

    def encode_many(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings, dtype=np.float32)
