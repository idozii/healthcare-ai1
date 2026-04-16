from pathlib import Path
import os


def _env_bool(name: str, default: bool = False) -> bool:
	raw = os.getenv(name)
	if raw is None:
		return default
	return raw.strip().lower() in {"1", "true", "yes", "on"}

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
PROJECT_DATA_PATH = PROJECT_ROOT / "diagnosis_dataset.csv"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DISEASES_CSV_PATH = DATA_DIR / "diseases.csv"
DISEASE_EMBEDDINGS_PATH = DATA_DIR / "disease_embeddings.npy"
DIAGNOSIS_CLASSIFIER_PATH = DATA_DIR / "diagnosis_classifier.joblib"

# Default OFF to keep startup stable in offline or unstable-network environments.
ALLOW_MODEL_DOWNLOAD = _env_bool("ALLOW_MODEL_DOWNLOAD", default=False)

# On serverless (e.g. Vercel), use lightweight retriever by default to reduce cold-start latency.
IS_SERVERLESS = _env_bool("VERCEL", default=False) or _env_bool("SERVERLESS", default=False)
FORCE_OFFLINE_RETRIEVER = _env_bool("FORCE_OFFLINE_RETRIEVER", default=IS_SERVERLESS)

TOP_K_DISEASES_DEFAULT = 4

# Disease retrieval tuning
MIN_DISEASE_CONFIDENCE = float(os.getenv("MIN_DISEASE_CONFIDENCE", "0.20"))
HYBRID_DENSE_WEIGHT = float(os.getenv("HYBRID_DENSE_WEIGHT", "0.65"))
RETRIEVAL_CANDIDATE_POOL = int(os.getenv("RETRIEVAL_CANDIDATE_POOL", "120"))
RETRIEVAL_QUERY_CACHE_SIZE = int(os.getenv("RETRIEVAL_QUERY_CACHE_SIZE", "256"))

# Scoring weights for recommendation ranking
WEIGHT_DISTANCE = 0.15
WEIGHT_PROVIDER_QUALITY = 0.45
WEIGHT_DROP_PENALTY = 0.25
WEIGHT_FLOW_EFFICIENCY = 0.15
