from pathlib import Path
import re
from difflib import SequenceMatcher
import json

import numpy as np
import pandas as pd

from app.services.scoring import compute_score
from app.utils.distance import haversine_km


class RecommendationService:
    _GENERIC_DISEASE_TOKENS = {
        "acute", "chronic", "syndrome", "disease", "disorder", "unspecified", "other", "with", "without"
    }
    _RULE_BASED_CODE_CANDIDATES = {
        "influenza": ["J10.1", "J11.1", "J10.81"],
        "flu": ["J10.1", "J11.1", "J10.81"],
        "pneumonia": ["J12.0", "J12.9", "J18.9"],
        "pericarditis": ["I30.9", "I31.1"],
        "myocarditis": ["I51.4", "B33.22"],
        "viral syndrome": ["B34.9", "J11.1", "J10.1"],
    }

    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parents[2]

        self.departments = pd.read_csv(self.base_dir / "app" / "data" / "departments.csv")
        self.providers = pd.read_csv(self.base_dir / "app" / "data" / "providers.csv")

        self.clinic_profiles = self._load_optional_csv([
            self.base_dir / "clinic_profiles.csv",
            self.base_dir / "app" / "data" / "clinic_profiles.csv",
        ])
        self.clinic_retention = self._load_optional_csv([
            self.base_dir / "clinic_retention.csv",
            self.base_dir / "app" / "data" / "clinic_retention.csv",
        ])
        self.clinic_diagnosis_volume = self._load_optional_csv([
            self.base_dir / "clinic_diagnosis_volume.csv",
            self.base_dir / "app" / "data" / "clinic_diagnosis_volume.csv",
        ])
        self.clinic_profiles_lists_json_path = self._pick_existing_path([
            self.base_dir / "clinic_profiles_lists.json",
            self.base_dir / "app" / "data" / "clinic_profiles_lists.json",
        ])
        self.clinic_facility_name_lookup = self._build_facility_name_lookup()
        self.diagnosis_dict = self._load_optional_csv([
            self.base_dir / "data" / "orig" / "diagnosis.csv",
            self.base_dir.parent / "data" / "orig" / "diagnosis.csv",
            self.base_dir / "app" / "data" / "diagnosis.csv",
        ])

        self.known_dx_codes = set()
        self.code_freq_norm: dict[str, float] = {}
        if self.clinic_diagnosis_volume is not None and not self.clinic_diagnosis_volume.empty:
            self.known_dx_codes = set(
                self.clinic_diagnosis_volume["DiagnosisValue"].astype(str).str.strip().replace("", np.nan).dropna().tolist()
            )
            freq = (
                self.clinic_diagnosis_volume.groupby("DiagnosisValue", as_index=False)["encounter_count"]
                .sum()
                .rename(columns={"DiagnosisValue": "code", "encounter_count": "count"})
            )
            if not freq.empty:
                mx = float(freq["count"].max())
                self.code_freq_norm = {
                    str(r["code"]): (float(r["count"]) / mx if mx > 0 else 0.0)
                    for _, r in freq.iterrows()
                }

        self.inferred_dx_by_name: dict[str, str] = {}
        self._prepare_diagnosis_dictionary()
        self._build_inferred_dx_mapping()

        self.has_clinic_matrix = self.clinic_profiles is not None and not self.clinic_profiles.empty
        self.clinic_matrix = self._build_clinic_matrix() if self.has_clinic_matrix else pd.DataFrame()

    @staticmethod
    def _load_optional_csv(candidates: list[Path]) -> pd.DataFrame | None:
        for path in candidates:
            if path.exists():
                return pd.read_csv(path)
        return None

    @staticmethod
    def _pick_existing_path(candidates: list[Path]) -> Path | None:
        for path in candidates:
            if path.exists():
                return path
        return None

    def _build_facility_name_lookup(self) -> dict[int, str]:
        lookup: dict[int, str] = {}
        path = self.clinic_profiles_lists_json_path
        if path is None:
            return lookup
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, list):
                return lookup
            for row in payload:
                if not isinstance(row, dict):
                    continue
                cid = row.get("ClinicID")
                name = str(row.get("facility_name", "")).strip()
                if cid is None or not name:
                    continue
                try:
                    key = int(float(cid))
                except Exception:
                    continue
                lookup[key] = name
        except Exception:
            return {}
        return lookup

    @staticmethod
    def _safe_norm(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce").fillna(0.0)
        lo = float(s.min())
        hi = float(s.max())
        if hi <= lo:
            return pd.Series([0.5] * len(s), index=s.index, dtype=float)
        return (s - lo) / (hi - lo)

    @staticmethod
    def _norm_text(value: str) -> str:
        s = str(value or "").lower()
        s = re.sub(r"\([^)]*\)", " ", s)
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _tokenize_significant(self, value: str) -> set[str]:
        tokens = set(self._norm_text(value).split())
        return {t for t in tokens if t and t not in self._GENERIC_DISEASE_TOKENS and len(t) >= 3}

    def _prepare_diagnosis_dictionary(self) -> None:
        if self.diagnosis_dict is None or self.diagnosis_dict.empty:
            self.diagnosis_dict = pd.DataFrame(columns=["DiagnosisName", "DiagnosisValue"])
            return

        required = {"DiagnosisName", "DiagnosisValue"}
        if not required.issubset(self.diagnosis_dict.columns):
            self.diagnosis_dict = pd.DataFrame(columns=["DiagnosisName", "DiagnosisValue"])
            return

        d = self.diagnosis_dict[["DiagnosisName", "DiagnosisValue"]].copy()
        d["DiagnosisName"] = d["DiagnosisName"].astype(str).str.strip()
        d["DiagnosisValue"] = d["DiagnosisValue"].astype(str).str.strip()
        d = d[(d["DiagnosisName"] != "") & (d["DiagnosisValue"] != "")]
        if self.known_dx_codes:
            d = d[d["DiagnosisValue"].isin(self.known_dx_codes)]
        d = d.drop_duplicates(subset=["DiagnosisValue"], keep="first").reset_index(drop=True)
        d["_norm_name"] = d["DiagnosisName"].map(self._norm_text)
        self.diagnosis_dict = d

    def _similarity(self, disease_name: str, diagnosis_name: str) -> float:
        a = self._norm_text(disease_name)
        b = self._norm_text(diagnosis_name)
        if not a or not b:
            return 0.0
        seq = SequenceMatcher(None, a, b).ratio()
        ta = set(a.split())
        tb = set(b.split())
        overlap = len(ta & tb) / max(1, len(ta | tb))
        contains = 0.12 if ta and (ta.issubset(tb) or tb.issubset(ta)) else 0.0
        return min(1.0, 0.62 * seq + 0.38 * overlap + contains)

    def _infer_diagnosis_value_for_name(self, disease_name: str) -> str | None:
        if self.diagnosis_dict is None or self.diagnosis_dict.empty:
            return None
        key = self._norm_text(disease_name)
        if not key:
            return None
        if key in self.inferred_dx_by_name:
            return self.inferred_dx_by_name[key]

        # Priority 1: rule-based candidates for common conditions.
        for rule, candidates in self._RULE_BASED_CODE_CANDIDATES.items():
            if rule in key:
                available = [c for c in candidates if c in self.known_dx_codes]
                if available:
                    best = max(available, key=lambda c: float(self.code_freq_norm.get(c, 0.0)))
                    self.inferred_dx_by_name[key] = best
                    return best

        query_tokens = self._tokenize_significant(disease_name)
        best_code = None
        best_score = -1.0
        for _, row in self.diagnosis_dict.iterrows():
            cand_name = str(row["DiagnosisName"])
            cand_code = str(row["DiagnosisValue"])
            cand_tokens = self._tokenize_significant(cand_name)

            seq = self._similarity(disease_name, cand_name)
            overlap = 0.0
            if query_tokens and cand_tokens:
                overlap = len(query_tokens & cand_tokens) / len(query_tokens | cand_tokens)
            token_hit = 1.0 if query_tokens and (query_tokens & cand_tokens) else 0.0
            freq_bonus = float(self.code_freq_norm.get(cand_code, 0.0))

            score = 0.50 * seq + 0.30 * overlap + 0.12 * token_hit + 0.08 * freq_bonus
            if score > best_score:
                best_score = score
                best_code = cand_code

        # Conservative floor to avoid noisy links.
        if best_code and best_score >= 0.22:
            self.inferred_dx_by_name[key] = best_code
            return best_code
        return None

    def _build_inferred_dx_mapping(self) -> None:
        diseases_path = self.base_dir / "app" / "data" / "diseases.csv"
        if not diseases_path.exists() or self.diagnosis_dict is None or self.diagnosis_dict.empty:
            return
        try:
            d = pd.read_csv(diseases_path)
            names = d.get("disease_name", pd.Series([], dtype=str)).astype(str).tolist()
            for name in names:
                key = self._norm_text(name)
                if not key or key in self.inferred_dx_by_name:
                    continue
                inferred = self._infer_diagnosis_value_for_name(name)
                if inferred:
                    self.inferred_dx_by_name[key] = inferred
        except Exception:
            return

    def _build_clinic_matrix(self) -> pd.DataFrame:
        profiles = self.clinic_profiles.copy()
        profiles = profiles.rename(columns={"ClinicID": "clinic_id", "City": "city", "Address": "address"})

        # Normalize schema variants from refreshed clinic_profiles.csv.
        if "facility_name" not in profiles.columns:
            profiles["facility_name"] = ""
        if "specialty_names" not in profiles.columns:
            profiles["specialty_names"] = ""
        if "facility_type" not in profiles.columns:
            profiles["facility_type"] = "Unknown"
        if "has_specialty" not in profiles.columns:
            if "n_specialties" in profiles.columns:
                profiles["has_specialty"] = pd.to_numeric(profiles["n_specialties"], errors="coerce").fillna(0.0) > 0
            else:
                profiles["has_specialty"] = 0
        if "has_ed" not in profiles.columns:
            if "has_ed_final" in profiles.columns:
                profiles["has_ed"] = profiles["has_ed_final"]
            elif "has_ed_curated" in profiles.columns:
                profiles["has_ed"] = profiles["has_ed_curated"]
            else:
                profiles["has_ed"] = 0

        profiles["clinic_id"] = pd.to_numeric(profiles["clinic_id"], errors="coerce")
        profiles = profiles.dropna(subset=["clinic_id", "lat", "lon"]).copy()
        profiles["clinic_id"] = profiles["clinic_id"].astype(int)

        for col in ["n_departments", "has_specialty", "has_ed", "has_or", "has_icu"]:
            if col not in profiles.columns:
                profiles[col] = 0

        for col in ["has_specialty", "has_ed", "has_or", "has_icu"]:
            profiles[col] = profiles[col].astype(str).str.lower().isin(["true", "1", "yes"]).astype(float)

        # Build baseline quality/efficiency from profile structure.
        dept_norm = self._safe_norm(profiles["n_departments"]) if "n_departments" in profiles.columns else 0.5
        specialty_flag = profiles["has_specialty"]
        ed_flag = profiles["has_ed"]
        or_flag = profiles["has_or"]
        icu_flag = profiles["has_icu"]

        profiles["provider_score"] = (0.45 * dept_norm + 0.35 * specialty_flag + 0.10 * ed_flag + 0.10 * or_flag).clip(0.0, 1.0)
        profiles["flow_efficiency"] = (0.35 * dept_norm + 0.25 * specialty_flag + 0.20 * or_flag + 0.20 * icu_flag).clip(0.0, 1.0)

        # Baseline retention proxy from structural capability (overridden by diagnosis retention when available).
        baseline_drop = 0.55 - 0.25 * profiles["provider_score"] - 0.15 * profiles["flow_efficiency"]
        profiles["drop_rate"] = baseline_drop.clip(0.15, 0.65)
        profiles["retention_source"] = "baseline_proxy"

        # Prefer facility_name from CSV; fallback to clinic_profiles_lists.json; fallback to legacy label.
        csv_names = profiles["facility_name"].astype(str).str.strip()
        json_names = profiles["clinic_id"].map(self.clinic_facility_name_lookup).fillna("").astype(str).str.strip()
        fallback_names = "Clinic " + profiles["clinic_id"].astype(str)
        display_name = csv_names.where(csv_names != "", json_names)
        display_name = display_name.where(display_name != "", fallback_names)

        city_text = profiles["city"].fillna("Unknown").astype(str).str.strip()
        city_text = city_text.where(city_text != "", "Unknown")
        profiles["hospital_name"] = display_name + " - " + city_text
        profiles["department_name"] = "General Care"

        keep_cols = [
            "clinic_id",
            "hospital_name",
            "facility_name",
            "facility_type",
            "department_name",
            "lat",
            "lon",
            "provider_score",
            "drop_rate",
            "flow_efficiency",
            "address",
            "city",
            "n_departments",
            "has_specialty",
            "has_ed",
            "has_or",
            "has_icu",
            "specialty_names",
            "retention_source",
        ]
        return profiles[keep_cols].copy()

    def _disease_fit_signal(self, disease: dict, candidates: pd.DataFrame) -> pd.Series:
        mapped = str(disease.get("mapped_departments", "")).lower()
        depts = {x.strip() for x in mapped.split("|") if x.strip()}

        fit = pd.Series([0.0] * len(candidates), index=candidates.index, dtype=float)

        if "emergency" in depts and "has_ed" in candidates.columns:
            fit += 0.30 * pd.to_numeric(candidates["has_ed"], errors="coerce").fillna(0.0)
        if "internal medicine" in depts and "n_departments" in candidates.columns:
            fit += 0.12 * self._safe_norm(candidates["n_departments"])

        specialty_depts = {"cardiology", "pulmonology", "gastroenterology", "orthopedics", "neurology", "infectious disease"}
        if depts.intersection(specialty_depts) and "has_specialty" in candidates.columns:
            fit += 0.25 * pd.to_numeric(candidates["has_specialty"], errors="coerce").fillna(0.0)

        if "cardiology" in depts and "has_icu" in candidates.columns:
            fit += 0.10 * pd.to_numeric(candidates["has_icu"], errors="coerce").fillna(0.0)

        if "orthopedics" in depts and "has_or" in candidates.columns:
            fit += 0.12 * pd.to_numeric(candidates["has_or"], errors="coerce").fillna(0.0)

        return fit.clip(0.0, 1.0)

    @staticmethod
    def _extract_department_names(diseases: list[dict]) -> list[str]:
        department_names: list[str] = []
        for item in diseases:
            mapped = str(item.get("mapped_departments", "")).strip()
            if not mapped:
                continue
            parts = [x.strip() for x in mapped.split("|") if x.strip()]
            department_names.extend(parts)
        return list(dict.fromkeys(department_names))

    def _extract_diagnosis_values(self, diseases: list[dict]) -> list[str]:
        dx_vals: list[str] = []
        candidate_keys = ["DiagnosisValue", "diagnosis_value", "icd_code", "diagnosis_code"]
        for d in diseases:
            for key in candidate_keys:
                val = d.get(key)
                if val is None:
                    continue
                s = str(val).strip()
                if s:
                    dx_vals.append(s)
            if not any(d.get(k) for k in candidate_keys):
                name = str(d.get("disease_name") or d.get("Disease") or "").strip()
                inferred = self._infer_diagnosis_value_for_name(name)
                if inferred:
                    dx_vals.append(inferred)
        return list(dict.fromkeys(dx_vals))

    @staticmethod
    def _select_diverse_top(df: pd.DataFrame, top_k: int) -> pd.DataFrame:
        if df.empty:
            return df
        if len(df) <= top_k:
            return df

        selected_idx: list[int] = []
        used_hospitals: set[str] = set()
        used_cities: set[str] = set()

        for idx, row in df.iterrows():
            if len(selected_idx) >= top_k:
                break

            hospital = str(row.get("hospital_name", ""))
            city = str(row.get("city", ""))

            if hospital in used_hospitals:
                continue

            city_penalty = 0.06 if city and city in used_cities else 0.0
            adjusted_score = float(row.get("score", 0.0)) - city_penalty

            # Only keep if it remains reasonably strong relative to top-ranked item.
            top_score = float(df.iloc[0].get("score", 0.0))
            if adjusted_score < max(0.0, top_score - 0.25):
                continue

            selected_idx.append(idx)
            used_hospitals.add(hospital)
            if city:
                used_cities.add(city)

        if len(selected_idx) < top_k:
            for idx, row in df.iterrows():
                if len(selected_idx) >= top_k:
                    break
                hospital = str(row.get("hospital_name", ""))
                if hospital in used_hospitals:
                    continue
                selected_idx.append(idx)
                used_hospitals.add(hospital)

        return df.loc[selected_idx]

    def _recommend_from_clinic_matrix(self, diseases: list[dict], user_location: tuple[float, float], top_k: int) -> list[dict]:
        if self.clinic_matrix.empty:
            return []

        effective_top_k = max(1, min(int(top_k), 3))
        candidates = self.clinic_matrix.copy()
        primary_disease = diseases[0] if diseases else {}
        dx_values = self._extract_diagnosis_values(diseases)
        candidates["disease_fit"] = self._disease_fit_signal(primary_disease, candidates)
        candidates["diagnosis_coverage"] = 0.0
        candidates["followup_rate"] = np.nan
        candidates["volume_norm"] = 0.0

        # Enrich score matrix with diagnosis-specific volume and retention when diagnosis codes are available.
        if dx_values and self.clinic_diagnosis_volume is not None and self.clinic_retention is not None:
            vol = self.clinic_diagnosis_volume.copy()
            vol = vol.rename(columns={"ClinicID": "clinic_id", "DiagnosisValue": "diagnosis_value"})
            vol = vol[vol["diagnosis_value"].astype(str).isin(dx_values)].copy()
            vol["clinic_id"] = pd.to_numeric(vol["clinic_id"], errors="coerce")
            vol["encounter_count"] = pd.to_numeric(vol.get("encounter_count", 0), errors="coerce").fillna(0.0)
            vol_agg = vol.groupby("clinic_id", as_index=False)["encounter_count"].sum()
            if not vol_agg.empty:
                vol_agg["volume_norm"] = self._safe_norm(vol_agg["encounter_count"])
                vol_agg["diagnosis_coverage"] = vol_agg["volume_norm"]

            ret = self.clinic_retention.copy()
            ret = ret.rename(columns={"ClinicID": "clinic_id", "DiagnosisValue": "diagnosis_value"})
            ret = ret[ret["diagnosis_value"].astype(str).isin(dx_values)].copy()
            ret["clinic_id"] = pd.to_numeric(ret["clinic_id"], errors="coerce")
            ret["journeys_started"] = pd.to_numeric(ret.get("journeys_started", 0), errors="coerce").fillna(0.0)
            ret["followup_rate"] = pd.to_numeric(ret.get("followup_rate", 0), errors="coerce").fillna(0.0).clip(0.0, 1.0)
            ret["weight"] = ret["journeys_started"].clip(lower=1)
            ret_agg = (
                ret.groupby("clinic_id", as_index=False)
                .apply(lambda g: pd.Series({
                    "followup_rate": float(np.average(g["followup_rate"], weights=g["weight"])),
                    "journeys_started": float(g["journeys_started"].sum()),
                }))
                .reset_index(drop=True)
            ) if not ret.empty else pd.DataFrame(columns=["clinic_id", "followup_rate", "journeys_started"])

            candidates = candidates.merge(vol_agg[["clinic_id", "volume_norm"]] if not vol_agg.empty else vol_agg, on="clinic_id", how="left")
            if not vol_agg.empty and "diagnosis_coverage" in vol_agg.columns:
                candidates = candidates.merge(vol_agg[["clinic_id", "diagnosis_coverage"]], on="clinic_id", how="left", suffixes=("", "_dx"))
            candidates = candidates.merge(ret_agg[["clinic_id", "followup_rate"]] if not ret_agg.empty else ret_agg, on="clinic_id", how="left")

            # Resolve merge suffixes when baseline columns already existed.
            vol_candidates = [c for c in ["volume_norm", "volume_norm_y", "volume_norm_x"] if c in candidates.columns]
            if vol_candidates:
                vol_series = pd.Series([np.nan] * len(candidates), index=candidates.index, dtype=float)
                for col in vol_candidates:
                    vol_series = vol_series.combine_first(pd.to_numeric(candidates[col], errors="coerce"))
                candidates["volume_norm"] = pd.to_numeric(vol_series, errors="coerce").fillna(0.0)

            dx_cov_candidates = [c for c in ["diagnosis_coverage_dx", "diagnosis_coverage"] if c in candidates.columns]
            if dx_cov_candidates:
                cov_series = pd.Series([np.nan] * len(candidates), index=candidates.index, dtype=float)
                for col in dx_cov_candidates:
                    cov_series = cov_series.combine_first(pd.to_numeric(candidates[col], errors="coerce"))
                candidates["diagnosis_coverage"] = pd.to_numeric(cov_series, errors="coerce").fillna(0.0)

            for col in ["volume_norm_x", "volume_norm_y", "diagnosis_coverage_dx"]:
                if col in candidates.columns:
                    candidates = candidates.drop(columns=[col])

            if "volume_norm" not in candidates.columns:
                candidates["volume_norm"] = 0.0
            else:
                candidates["volume_norm"] = pd.to_numeric(candidates["volume_norm"], errors="coerce").fillna(0.0)

            if "diagnosis_coverage" not in candidates.columns:
                candidates["diagnosis_coverage"] = 0.0
            else:
                candidates["diagnosis_coverage"] = pd.to_numeric(candidates["diagnosis_coverage"], errors="coerce").fillna(0.0)

            if "followup_rate" not in candidates.columns:
                candidates["followup_rate"] = np.nan
            candidates["drop_rate"] = np.where(
                candidates["followup_rate"].notna(),
                1.0 - candidates["followup_rate"].clip(0.0, 1.0),
                candidates["drop_rate"],
            )
            candidates["retention_source"] = np.where(
                candidates["followup_rate"].notna(),
                "diagnosis_retention",
                candidates.get("retention_source", "baseline_proxy"),
            )
            candidates["provider_score"] = (
                0.55 * candidates["provider_score"] + 0.25 * candidates["volume_norm"] + 0.20 * (1.0 - candidates["drop_rate"])
            ).clip(0.0, 1.0)
            candidates["flow_efficiency"] = (
                0.70 * candidates["flow_efficiency"] + 0.20 * candidates["volume_norm"] + 0.10 * candidates["disease_fit"]
            ).clip(0.0, 1.0)

        # For emergency-linked diagnoses, keep ED-capable clinics when available.
        mapped = str(primary_disease.get("mapped_departments", "")).lower()
        if "emergency" in mapped and "has_ed" in candidates.columns:
            ed_mask = pd.to_numeric(candidates["has_ed"], errors="coerce").fillna(0.0) > 0
            if bool(ed_mask.any()):
                candidates = candidates[ed_mask].copy()

        user_lat, user_lon = user_location
        candidates["distance_km"] = candidates.apply(
            lambda r: haversine_km(user_lat, user_lon, float(r["lat"]), float(r["lon"])),
            axis=1,
        )

        candidates["score"] = candidates.apply(lambda r: compute_score(r.to_dict()), axis=1)
        candidates["score"] = (
            candidates["score"]
            + 0.12 * candidates["disease_fit"]
            + 0.12 * candidates["diagnosis_coverage"]
        ).clip(0.0, 1.0)
        has_dx_coverage = float(pd.to_numeric(candidates["diagnosis_coverage"], errors="coerce").fillna(0.0).max()) > 0.0

        if has_dx_coverage:
            candidates["score"] = (
                candidates["score"]
                + 0.22 * pd.to_numeric(candidates["diagnosis_coverage"], errors="coerce").fillna(0.0)
                + 0.08 * pd.to_numeric(candidates["volume_norm"], errors="coerce").fillna(0.0)
            ).clip(0.0, 1.0)

        candidates = candidates.sort_values(["score", "provider_score"], ascending=False)
        candidates = candidates.drop_duplicates(subset=["hospital_name", "department_name"], keep="first")

        if has_dx_coverage:
            preferred = candidates[pd.to_numeric(candidates["diagnosis_coverage"], errors="coerce").fillna(0.0) > 0.0].copy()
            fallback = candidates[pd.to_numeric(candidates["diagnosis_coverage"], errors="coerce").fillna(0.0) <= 0.0].copy()

            selected = self._select_diverse_top(preferred, effective_top_k)
            if len(selected) < effective_top_k:
                need = effective_top_k - len(selected)
                extra = self._select_diverse_top(fallback, need)
                selected = pd.concat([selected, extra], axis=0)
            candidates = selected
        else:
            candidates = self._select_diverse_top(candidates, effective_top_k)

        cols = [
            "hospital_name",
            "facility_name",
            "facility_type",
            "department_name",
            "distance_km",
            "provider_score",
            "drop_rate",
            "flow_efficiency",
            "score",
            "clinic_id",
            "address",
            "city",
            "disease_fit",
            "diagnosis_coverage",
            "has_ed",
            "has_icu",
            "has_or",
            "has_specialty",
            "specialty_names",
            "retention_source",
        ]
        cols = [c for c in cols if c in candidates.columns]
        return candidates[cols].head(effective_top_k).to_dict(orient="records")

    def recommend(self, diseases: list[dict], user_location: tuple[float, float], top_k: int = 5) -> list[dict]:
        effective_top_k = max(1, min(int(top_k), 3))

        # Prefer clinic matrix when available so imported clinic_* CSV features are used.
        if self.has_clinic_matrix:
            out = self._recommend_from_clinic_matrix(diseases=diseases, user_location=user_location, top_k=effective_top_k)
            if out:
                return out

        target_departments = self._extract_department_names(diseases)

        candidates = self.departments.copy()
        if target_departments and "department_name" in candidates.columns:
            candidates = candidates[candidates["department_name"].isin(target_departments)].copy()

        if candidates.empty:
            return []

        merged = candidates.merge(self.providers, on="department_id", how="left", suffixes=("", "_provider"))
        merged = merged.fillna(0)

        user_lat, user_lon = user_location
        merged["distance_km"] = merged.apply(
            lambda r: haversine_km(user_lat, user_lon, float(r["lat"]), float(r["lon"])),
            axis=1,
        )

        merged["score"] = merged.apply(lambda r: compute_score(r.to_dict()), axis=1)
        merged = merged.sort_values(["score", "provider_score"], ascending=False)
        if "hospital_name" in merged.columns and "department_name" in merged.columns:
            merged = merged.drop_duplicates(subset=["hospital_name", "department_name"], keep="first")
        merged = self._select_diverse_top(merged, effective_top_k)

        cols = [
            "hospital_name",
            "department_name",
            "distance_km",
            "provider_score",
            "drop_rate",
            "flow_efficiency",
            "score",
        ]
        cols = [c for c in cols if c in merged.columns]
        return merged[cols].head(effective_top_k).to_dict(orient="records")
