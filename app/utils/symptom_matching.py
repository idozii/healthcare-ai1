import re


_SYMPTOM_REPLACEMENTS = [
    (r"\bbroken\s+leg(s)?\b", "leg fracture"),
    (r"\bbroken\s+arm(s)?\b", "arm fracture"),
    (r"\bbroken\s+bone(s)?\b", "bone fracture"),
    (r"\bone[-\s]?sided\s+headache\b", "migraine headache"),
    (r"\bone\s+side(?:d)?\s+headache\b", "migraine headache"),
    (r"\bone\s+side\s+of\s+my\s+head\b", "migraine headache"),
    (r"\bone\s+side\s+of\s+the\s+head\b", "migraine headache"),
    (r"\bunilateral\s+headache\b", "migraine headache"),
    (r"\bsides?\s+of\s+my\s+head\b", "headache migraine"),
    (r"\bshortness of breath\b", "dyspnea"),
    (r"\bchest pain\b", "angina chest pain"),
    (r"\bneck\s+hurts?\b", "neck pain"),
    (r"\bcan['’]?t\s+move\b", "limited mobility"),
    (r"\bcan['’]?t\s+walk\b", "gait difficulty"),
    (r"\bbody\s+aches?\b", "myalgia body ache"),
    (r"\bhigh\s+fever\b", "fever"),
    (r"\bchills?\b", "chills"),
    (r"\bbathroom\s+very\s+often\b", "urinate frequently"),
    (r"\bpass\s+small\s+amounts\b", "urinary urgency"),
    (r"\blower\s+abdomen\b", "suprapubic pain"),
    (r"\bcloudy\s+urine\b", "cloudy urine"),
    (r"\bpeeing\b", "urinate"),
    (r"\bpee\b", "urinate"),
    (r"\bvery\s+thirsty\b", "thirsty"),
    (r"\bwounds\s+heal\s+slowly\b", "slow wound healing"),
    (r"\bblur(?:r)?y\s+vision\b", "blurred vision"),
    (r"\bdiarrhoea\b", "diarrhea"),
    (r"\bcan['’]?t\s+keep\s+food\s+down\b", "vomiting"),
    (r"\brunny\s+nose\b", "nasal congestion"),
    (r"\bscratchy\s+throat\b", "sore throat"),
    (r"\bteeth\b", "tooth pain dental"),
    (r"\btoothache\b", "tooth pain"),
    (r"\bgum\s+pain\b", "gum pain dental"),
]

_NON_CLINICAL_PATTERNS = [
    r"\bi\s*am\s+gay\b",
    r"\bi['’]?m\s+gay\b",
    r"\bi\s*am\s+straight\b",
    r"\bi['’]?m\s+straight\b",
]

_SYMPTOM_SIGNAL_TERMS = {
    "pain", "hurt", "hurts", "swelling", "fever", "cough", "breath", "shortness", "fracture", "injury",
    "vomit", "nausea", "chest", "neck", "head", "leg", "arm", "walk", "move", "mobility", "dizzy",
    "fatigue", "weakness", "pressure", "tightness", "burning", "palpitation", "chills", "myalgia", "ache",
    "migraine", "photophobia", "aura", "throbbing", "unilateral", "urinate", "urination", "urinary",
    "bathroom", "cloudy", "thirsty", "diarrhea", "diarrhoea", "stomach", "cramps", "sneezing", "runny",
    "nose", "congestion", "watery", "vision", "blurred", "wound", "heal", "hunger", "hungry",
    "tooth", "teeth", "dental", "gum", "gums", "jaw",
}

_BODY_PART_HINTS = {"leg", "legs", "arm", "arms", "knee", "knees", "ankle", "ankles", "foot", "feet", "hip", "hips"}
_INJURY_CONTEXT_WORDS = {"pain", "injury", "trauma", "fracture", "swelling"}

_INTENT_KEYWORDS = {
    "injury": {
        "broken", "fracture", "injury", "sprain", "trauma", "fall", "accident", "bone", "leg", "arm"
    },
    "cardio": {
        "chest", "heart", "palpitation", "angina", "pressure", "myocard", "cardiac"
    },
    "resp": {
        "breath", "dyspnea", "wheezing", "cough", "asthma", "pulmonary", "lung"
    },
    "gastro": {
        "stomach", "abdominal", "reflux", "nausea", "vomit", "heartburn", "gastro"
    },
    "urinary": {
        "urinate", "urination", "urinary", "bladder", "bathroom", "dysuria", "urgency", "cloudy", "suprapubic"
    },
    "diabetes": {
        "thirsty", "urinate", "urination", "hungry", "weight", "wound", "healing", "blurred", "vision", "fatigue"
    },
    "hypertension": {
        "headache", "pressure", "dizzy", "dizziness", "blurred", "vision", "lightheaded", "head"
    },
    "gastroenteritis": {
        "diarrhea", "vomit", "vomiting", "nausea", "cramps", "stomach", "abdominal", "food poisoning", "stomach flu"
    },
    "cold": {
        "runny", "nose", "sneezing", "congestion", "scratchy", "throat", "watery", "mild", "cough"
    },
    "headache": {
        "headache", "migraine", "unilateral", "one-sided", "one sided", "throbbing", "photophobia", "aura", "temple"
    },
    "infection": {
        "fever", "chills", "myalgia", "ache", "aches", "flu", "influenza", "viral", "sore", "throat", "sudden"
    },
    "dental": {
        "tooth", "teeth", "toothache", "dental", "gum", "gums", "jaw", "molar", "oral"
    },
}

_INTENT_TERMS = {
    "injury": {"fracture", "injury", "sprain", "trauma", "orthopedic", "bone", "emergency"},
    "cardio": {"heart", "cardio", "angina", "myocard", "failure", "pericard"},
    "resp": {"pulmonary", "asthma", "pneumonia", "dyspnea", "respir"},
    "gastro": {"gastro", "reflux", "stomach", "abdominal"},
    "urinary": {"urinary", "urinate", "bladder", "dysuria", "urgency", "cloudy", "uti"},
    "diabetes": {"diabetes", "thirsty", "urinate", "urinary", "blurred", "vision", "wound", "healing"},
    "hypertension": {"hypertension", "pressure", "headache", "dizzy", "blurred", "vision", "lightheaded"},
    "gastroenteritis": {"gastroenteritis", "diarrhea", "vomiting", "nausea", "cramps", "food poisoning", "stomach flu"},
    "cold": {"cold", "runny", "sneezing", "congestion", "scratchy", "watery", "throat"},
    "headache": {"headache", "migraine", "photophobia", "aura", "throbbing", "unilateral", "temple"},
    "infection": {"influenza", "flu", "viral", "chills", "myalgia", "body ache", "sore throat"},
    "dental": {"tooth", "dental", "oral", "gingiva", "jaw", "odont"},
}

_CONFLICT_DEPTS = {
    "injury": {"cardiology", "psychiatry"},
}

_INTENT_DEPT_BONUS = {
    "injury": {"emergency", "orthopedic", "orthopaedic", "internal medicine"},
    "urinary": {"internal medicine", "emergency"},
    "diabetes": {"endocrinology", "internal medicine"},
    "hypertension": {"internal medicine", "cardiology"},
    "gastroenteritis": {"internal medicine", "emergency", "gastroenterology"},
    "cold": {"internal medicine", "pulmonology"},
    "headache": {"internal medicine", "emergency"},
    "infection": {"internal medicine", "pulmonology", "emergency"},
    "dental": {"dentistry", "oral", "maxillofacial", "emergency", "ent", "internal medicine"},
}

_INTENT_DEPT_PENALTY = {
    "injury": {"cardiology": 0.22, "psychiatry": 0.16, "pulmonology": 0.10},
    "urinary": {"cardiology": 0.12, "psychiatry": 0.10},
    "diabetes": {"psychiatry": 0.10},
    "hypertension": {"psychiatry": 0.10},
    "gastroenteritis": {"cardiology": 0.14},
    "cold": {"cardiology": 0.12},
    "headache": {"cardiology": 0.18, "pulmonology": 0.10},
    "infection": {"cardiology": 0.24, "psychiatry": 0.12},
    "dental": {"cardiology": 0.16, "psychiatry": 0.12},
}

_CARDIO_QUERY_HINTS = {"chest", "angina", "heart", "cardiac", "palpitation", "pressure"}
_HEADACHE_QUERY_HINTS = {"headache", "migraine", "unilateral", "one-sided", "one sided", "throbbing", "photophobia", "aura", "temple"}


def normalize_symptom_text(text: str) -> str:
    out = (text or "").lower().strip()

    for p in _NON_CLINICAL_PATTERNS:
        out = re.sub(p, " ", out)

    # For paragraph-style inputs, keep clauses that carry symptom signals.
    clauses = re.split(r"[\n\r\.!?;]+", out)
    selected: list[str] = []
    for c in clauses:
        c_norm = c.strip()
        if not c_norm:
            continue
        tokens = set(re.findall(r"[a-z]+", c_norm))
        if tokens.intersection(_SYMPTOM_SIGNAL_TERMS):
            selected.append(c_norm)
    if selected:
        out = " ".join(selected)

    for pattern, replacement in _SYMPTOM_REPLACEMENTS:
        out = re.sub(pattern, replacement, out)

    # Remove repeated emphasis words that add noise but no clinical meaning.
    out = re.sub(r"\b(so|very|really|too)\b", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def enrich_sparse_query(normalized_text: str) -> str:
    tokens = re.findall(r"[a-z]+", normalized_text)
    if not tokens:
        return normalized_text

    token_set = set(tokens)
    if len(token_set) <= 2 and token_set.intersection(_BODY_PART_HINTS) and not token_set.intersection(_INJURY_CONTEXT_WORDS):
        # Keep this lightweight so sparse inputs like "legs" still map to injury-related diagnoses.
        return f"{normalized_text} leg pain injury trauma fracture swelling unable to bear weight"

    if token_set.intersection(_HEADACHE_QUERY_HINTS):
        return (
            f"{normalized_text} migraine headache unilateral one-sided throbbing photophobia aura temple "
            f"head pain severe headache"
        )

    if token_set.intersection({"teeth", "tooth", "toothache", "dental", "gum", "gums", "jaw"}):
        return (
            f"{normalized_text} tooth pain dental pain gum swelling jaw pain oral infection "
            f"tooth abscess severe toothache"
        )

    return normalized_text


def detect_intents(normalized_text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z]+", normalized_text))
    intents: set[str] = set()
    for intent, words in _INTENT_KEYWORDS.items():
        if tokens.intersection(words):
            intents.add(intent)
    return intents


def confidence_threshold_for_query(normalized_text: str, base_threshold: float) -> float:
    tokens = re.findall(r"[a-z]+", normalized_text)
    token_count = len(set(tokens))
    intents = detect_intents(normalized_text)

    threshold = base_threshold
    if token_count == 1:
        threshold = max(0.04, base_threshold - 0.16)
    elif token_count <= 2:
        threshold = max(0.10, base_threshold - 0.10)

    if "injury" in intents and token_count <= 2:
        threshold = max(0.06, threshold - 0.04)

    if "headache" in intents:
        threshold = max(0.12, threshold - 0.06)

    if "dental" in intents and token_count <= 3:
        threshold = max(0.06, threshold - 0.05)

    return threshold


def retrieval_delta_for_intent(mapped_departments: str, intents: set[str], normalized_text: str) -> float:
    dept_blob = (mapped_departments or "").lower()
    tokens = set(re.findall(r"[a-z]+", normalized_text))
    token_count = len(tokens)
    has_cardio_query_hints = bool(tokens.intersection(_CARDIO_QUERY_HINTS))

    delta = 0.0
    for intent in intents:
        for good_dept in _INTENT_DEPT_BONUS.get(intent, set()):
            if good_dept in dept_blob:
                delta += 0.08

        for bad_dept, penalty in _INTENT_DEPT_PENALTY.get(intent, {}).items():
            if bad_dept in dept_blob:
                # Avoid over-penalizing cardio when query explicitly has chest/cardiac hints.
                if intent == "infection" and bad_dept == "cardiology" and has_cardio_query_hints:
                    penalty *= 0.35
                delta -= penalty

    # Stronger down-ranking for sparse body-part queries like "legs".
    if "injury" in intents and token_count <= 2:
        delta *= 1.35

    if "headache" in intents and token_count <= 4:
        delta *= 1.10

    return delta


def clinical_boost(disease_name: str, description: str, mapped_departments: str, intents: set[str]) -> float:
    text_blob = f"{disease_name} {description}".lower()
    dept_blob = (mapped_departments or "").lower()

    boost = 0.0

    for intent in intents:
        intent_terms = _INTENT_TERMS.get(intent, set())
        if any(t in text_blob for t in intent_terms):
            boost += 0.12
        if any(t in dept_blob for t in intent_terms):
            boost += 0.08

        for bad_dept in _CONFLICT_DEPTS.get(intent, set()):
            if bad_dept in dept_blob and not any(t in text_blob for t in intent_terms):
                boost -= 0.10

    if "headache" in intents and any(term in text_blob for term in {"migraine", "headache", "throbbing", "photophobia", "aura", "unilateral"}):
        boost += 0.10

    return boost
