from __future__ import annotations

import argparse
from difflib import SequenceMatcher
from pathlib import Path
import re

import pandas as pd


NOISE_TOKENS = {
    "icd",
    "cm",
    "hcc",
    "hhs",
    "multi",
    "unspecified",
    "spec",
    "specified",
    "other",
}


def _pick_existing_path(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


def _normalize_name(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    return "" if s.lower() == "nan" else s


def _tokenize(s: str) -> set[str]:
    text = _normalize_for_match(s)
    parts = re.findall(r"[a-z0-9]+", text)
    return {p for p in parts if len(p) >= 2}


def _normalize_for_match(s: str) -> str:
    text = _clean_text(s).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = text.replace("-", " ").replace("/", " ")
    parts = re.findall(r"[a-z0-9]+", text)
    parts = [p for p in parts if p not in NOISE_TOKENS]
    return " ".join(parts)


def _string_similarity(a: str, b: str) -> float:
    return float(SequenceMatcher(None, _normalize_for_match(a), _normalize_for_match(b)).ratio())


def _hybrid_similarity(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    overlap = 0.0 if not ta or not tb else len(ta & tb) / len(ta | tb)
    seq = _string_similarity(a, b)
    contains_boost = 0.0
    if ta and tb and (ta.issubset(tb) or tb.issubset(ta)):
        contains_boost = 0.15
    return min(1.0, 0.60 * seq + 0.40 * overlap + contains_boost)


def load_manual_mapping(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "disease_name" not in df.columns or "DiagnosisValue" not in df.columns:
        raise ValueError("manual mapping file must contain disease_name and DiagnosisValue columns")

    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        name = _normalize_name(_clean_text(row.get("disease_name", "")))
        value = _clean_text(row.get("DiagnosisValue", ""))
        if name and value:
            mapping[name] = value
    return mapping


def build_known_codes(path: Path) -> set[str]:
    df = pd.read_csv(path)
    if "DiagnosisValue" not in df.columns:
        return set()
    vals = df["DiagnosisValue"].astype(str).str.strip()
    vals = vals[(vals != "") & (vals.str.lower() != "nan")]
    return set(vals.tolist())


def load_diagnosis_dictionary(path: Path, known_codes: set[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"DiagnosisName", "DiagnosisValue"}
    if not required.issubset(df.columns):
        raise ValueError("diagnosis dictionary must contain DiagnosisName and DiagnosisValue columns")

    df = df[["DiagnosisName", "DiagnosisValue"]].copy()
    df["DiagnosisName"] = df["DiagnosisName"].map(_clean_text)
    df["DiagnosisValue"] = df["DiagnosisValue"].map(_clean_text)
    df = df[(df["DiagnosisName"] != "") & (df["DiagnosisValue"] != "")]

    if known_codes:
        df = df[df["DiagnosisValue"].isin(known_codes)]

    # Keep a single representative name per code to reduce duplicate scoring noise.
    return df.drop_duplicates(subset=["DiagnosisValue"], keep="first").reset_index(drop=True)


def suggest_codes(
    disease_name: str,
    diagnosis_dict: pd.DataFrame,
    top_n: int = 3,
) -> list[dict[str, object]]:
    if diagnosis_dict.empty:
        return []

    rows: list[dict[str, object]] = []
    for _, row in diagnosis_dict.iterrows():
        candidate_name = _clean_text(row["DiagnosisName"])
        candidate_code = _clean_text(row["DiagnosisValue"])
        if not candidate_name or not candidate_code:
            continue
        score = _hybrid_similarity(disease_name, candidate_name)
        rows.append(
            {
                "DiagnosisValue": candidate_code,
                "DiagnosisName": candidate_name,
                "score": round(score, 4),
            }
        )

    rows.sort(key=lambda x: float(x["score"]), reverse=True)
    return rows[:top_n]


def ensure_template(path: Path, diseases: pd.DataFrame) -> None:
    if path.exists():
        return
    out = diseases[["disease_name"]].copy()
    out["DiagnosisValue"] = ""
    out.to_csv(path, index=False)


def run(
    project_root: Path,
    manual_file: str,
    write: bool,
    auto_suggest: bool,
    min_score: float,
    top_suggestions: int,
    suggestions_out: str,
) -> None:
    disease_path = project_root / "app" / "data" / "diseases.csv"
    clinic_volume_path = _pick_existing_path(
        [
            project_root / "clinic_diagnosis_volume.csv",
            project_root / "app" / "data" / "clinic_diagnosis_volume.csv",
        ]
    )
    diagnosis_dict_path = _pick_existing_path(
        [
            project_root / "data" / "orig" / "diagnosis.csv",
            project_root.parent / "data" / "orig" / "diagnosis.csv",
            project_root / "app" / "data" / "diagnosis.csv",
        ]
    )

    if not disease_path.exists():
        raise FileNotFoundError(f"missing diseases.csv: {disease_path}")
    if clinic_volume_path is None:
        raise FileNotFoundError("missing clinic_diagnosis_volume.csv (root or app/data)")

    diseases = pd.read_csv(disease_path)
    if "disease_name" not in diseases.columns:
        raise ValueError("diseases.csv must contain disease_name column")

    if "DiagnosisValue" not in diseases.columns:
        diseases["DiagnosisValue"] = ""

    known_codes = build_known_codes(clinic_volume_path)
    diagnosis_dict = pd.DataFrame(columns=["DiagnosisName", "DiagnosisValue"])
    if auto_suggest:
        if diagnosis_dict_path is None:
            raise FileNotFoundError("auto-suggest enabled but diagnosis.csv was not found")
        diagnosis_dict = load_diagnosis_dictionary(diagnosis_dict_path, known_codes)

    manual_path = project_root / manual_file
    ensure_template(manual_path, diseases)
    manual_map = load_manual_mapping(manual_path)

    before_filled = diseases["DiagnosisValue"].astype(str).str.strip().ne("").sum()

    unresolved_rows: list[dict[str, str]] = []
    suggestion_rows: list[dict[str, object]] = []
    updates = 0
    auto_updates = 0
    manual_updates = 0

    for idx, row in diseases.iterrows():
        name_raw = _clean_text(row.get("disease_name", ""))
        name_key = _normalize_name(name_raw)
        current_value = _clean_text(row.get("DiagnosisValue", ""))

        if current_value:
            continue

        manual_value = manual_map.get(name_key, "")
        if manual_value and manual_value in known_codes:
            diseases.at[idx, "DiagnosisValue"] = manual_value
            updates += 1
            manual_updates += 1
        else:
            top = suggest_codes(name_raw, diagnosis_dict, top_n=max(1, top_suggestions)) if auto_suggest else []
            best = top[0] if top else None
            if best is not None and float(best["score"]) >= min_score:
                diseases.at[idx, "DiagnosisValue"] = str(best["DiagnosisValue"])
                updates += 1
                auto_updates += 1

            for rank, cand in enumerate(top, start=1):
                suggestion_rows.append(
                    {
                        "disease_name": name_raw,
                        "rank": rank,
                        "DiagnosisValue": cand["DiagnosisValue"],
                        "DiagnosisName": cand["DiagnosisName"],
                        "score": cand["score"],
                        "auto_selected": bool(rank == 1 and best is not None and float(best["score"]) >= min_score),
                    }
                )

            if best is not None and float(best["score"]) >= min_score:
                continue

            unresolved_rows.append(
                {
                    "disease_name": name_raw,
                    "DiagnosisValue": manual_value,
                    "reason": "manual code missing/invalid and no confident auto-suggestion",
                }
            )

    after_filled = diseases["DiagnosisValue"].astype(str).str.strip().ne("").sum()

    unresolved_path = project_root / "disease_mapping_unresolved.csv"
    pd.DataFrame(unresolved_rows).to_csv(unresolved_path, index=False)
    suggestions_path = project_root / suggestions_out
    pd.DataFrame(suggestion_rows).to_csv(suggestions_path, index=False)

    if write:
        diseases.to_csv(disease_path, index=False)

    print("Mapping summary")
    print(f"- diseases.csv: {disease_path}")
    print(f"- clinic_diagnosis_volume.csv: {clinic_volume_path}")
    print(f"- manual mapping file: {manual_path}")
    print(f"- auto suggest: {auto_suggest}")
    print(f"- suggestions output: {suggestions_path}")
    print(f"- unresolved output: {unresolved_path}")
    print(f"- filled before: {before_filled}")
    print(f"- filled after: {after_filled}")
    print(f"- updates applied this run: {updates}")
    print(f"  - manual updates: {manual_updates}")
    print(f"  - auto updates: {auto_updates}")
    if not write:
        print("- dry run mode: diseases.csv unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map disease_name to DiagnosisValue for clinic-aware recommendations")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to healthcare-ai project root",
    )
    parser.add_argument(
        "--manual-file",
        default="disease_to_code_manual.csv",
        help="CSV file with disease_name,DiagnosisValue",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write updates into app/data/diseases.csv",
    )
    parser.add_argument(
        "--auto-suggest",
        action="store_true",
        help="Use diagnosis dictionary to suggest DiagnosisValue for unmapped diseases",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.72,
        help="Minimum similarity score to auto-apply suggested DiagnosisValue",
    )
    parser.add_argument(
        "--top-suggestions",
        type=int,
        default=3,
        help="Number of candidate suggestions to emit per disease",
    )
    parser.add_argument(
        "--suggestions-out",
        default="disease_code_suggestions.csv",
        help="Output CSV path for suggestion candidates (relative to project root)",
    )

    args = parser.parse_args()
    run(
        project_root=Path(args.project_root).resolve(),
        manual_file=args.manual_file,
        write=args.write,
        auto_suggest=args.auto_suggest,
        min_score=args.min_score,
        top_suggestions=args.top_suggestions,
        suggestions_out=args.suggestions_out,
    )
