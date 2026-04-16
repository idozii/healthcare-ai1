from app.config import (
    WEIGHT_DISTANCE,
    WEIGHT_DROP_PENALTY,
    WEIGHT_FLOW_EFFICIENCY,
    WEIGHT_PROVIDER_QUALITY,
)


def compute_score(row: dict) -> float:
    distance_score = 1.0 / (1.0 + float(row.get("distance_km", 1e6)))
    quality_score = float(row.get("provider_score", 0.0))
    drop_penalty = 1.0 - float(row.get("drop_rate", 1.0))
    flow_score = float(row.get("flow_efficiency", 0.0))

    return (
        WEIGHT_DISTANCE * distance_score
        + WEIGHT_PROVIDER_QUALITY * quality_score
        + WEIGHT_DROP_PENALTY * drop_penalty
        + WEIGHT_FLOW_EFFICIENCY * flow_score
    )
