import pandas as pd


def minmax_normalize(series: pd.Series) -> pd.Series:
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)


def preprocess_department_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "drop_rate" in out.columns:
        out["drop_rate"] = out["drop_rate"].clip(lower=0.0, upper=1.0)

    if "provider_score" in out.columns:
        out["provider_score"] = minmax_normalize(out["provider_score"]).clip(0.0, 1.0)

    if "flow_efficiency" in out.columns:
        out["flow_efficiency"] = minmax_normalize(out["flow_efficiency"]).clip(0.0, 1.0)

    return out
