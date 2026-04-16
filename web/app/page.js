"use client";

import { useMemo, useState } from "react";

const EXAMPLES = [
  {
    label: "Chest pain + shortness of breath",
    text: "chest pain and shortness of breath",
    location: "Austin, TX",
    top_k: 5
  },
  {
    label: "Flu-like symptoms",
    text: "fever, cough, body aches, sore throat",
    location: "Chicago, IL",
    top_k: 5
  },
  {
    label: "Abdominal pain",
    text: "lower abdominal pain with nausea",
    location: "Seattle, WA",
    top_k: 5
  }
];

const INITIAL_FORM = {
  text: "",
  location: "",
  lat: "",
  lon: "",
  top_k: 5
};

function formatNumber(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number.toFixed(digits);
}

function formatDistance(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  if (number < 1) {
    return `${Math.round(number * 1000)} m`;
  }
  return `${number.toFixed(1)} km`;
}

function scoreLabel(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) {
    return "0%";
  }
  return `${Math.round(score * 100)}%`;
}

function makeRequestBody(form) {
  const payload = {
    text: form.text.trim(),
    top_k: Number(form.top_k) || 5
  };

  if (form.location.trim()) {
    payload.location = form.location.trim();
  }

  const lat = form.lat.trim();
  const lon = form.lon.trim();
  if (lat && lon) {
    payload.lat = Number(lat);
    payload.lon = Number(lon);
  }

  return payload;
}

export default function Page() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const diseases = result?.diseases || [];
  const recommendationsByDisease = result?.recommendations_by_disease || {};
  const diseaseNames = useMemo(() => Object.keys(recommendationsByDisease), [recommendationsByDisease]);

  const activeRecommendations = useMemo(() => {
    if (diseaseNames.length > 0) {
      return recommendationsByDisease[diseaseNames[0]] || [];
    }
    return result?.recommendations || [];
  }, [diseaseNames, recommendationsByDisease, result]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: {
          "content-type": "application/json"
        },
        body: JSON.stringify(makeRequestBody(form))
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Prediction request failed.");
      }

      setResult(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Prediction request failed.");
    } finally {
      setLoading(false);
    }
  }

  function applyExample(example) {
    setForm((current) => ({
      ...current,
      text: example.text,
      location: example.location,
      top_k: example.top_k
    }));
  }

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Vercel-ready frontend</p>
          <h1>Healthcare AI triage with a cleaner deployment path</h1>
          <p>
            Keep the Python diagnosis engine where it works best, and put the user-facing experience on Next.js so Vercel can handle the UI and API proxy.
          </p>
          <div className="hero-badges">
            <span>Next.js App Router</span>
            <span>Proxy API route</span>
            <span>FastAPI backend compatible</span>
          </div>
        </div>

        <div className="hero-card">
          <div className="hero-card-top">
            <span className="status-pill">Deployment model</span>
            <strong>Frontend on Vercel</strong>
          </div>
          <p>
            Set <code>HEALTHCARE_AI_API_BASE_URL</code> to the Python service URL, and the Next.js app will forward prediction requests through <code>/api/predict</code>.
          </p>
        </div>
      </section>

      <section className="content-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="panel-header">
            <div>
              <p className="section-label">Symptom intake</p>
              <h2>Ask for a diagnosis and care recommendation</h2>
            </div>
            <div className="sample-row">
              {EXAMPLES.map((example) => (
                <button key={example.label} type="button" className="ghost-button" onClick={() => applyExample(example)}>
                  {example.label}
                </button>
              ))}
            </div>
          </div>

          <label>
            Symptoms
            <textarea
              required
              value={form.text}
              onChange={(event) => setForm((current) => ({ ...current, text: event.target.value }))}
              placeholder="Describe the patient symptoms, duration, and severity"
            />
          </label>

          <div className="field-grid">
            <label>
              Location text
              <input
                value={form.location}
                onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
                placeholder="City, suburb, or address"
              />
            </label>

            <div className="coord-grid">
              <label>
                Latitude
                <input
                  value={form.lat}
                  onChange={(event) => setForm((current) => ({ ...current, lat: event.target.value }))}
                  placeholder="Optional"
                />
              </label>
              <label>
                Longitude
                <input
                  value={form.lon}
                  onChange={(event) => setForm((current) => ({ ...current, lon: event.target.value }))}
                  placeholder="Optional"
                />
              </label>
            </div>
          </div>

          <label>
            Top K
            <input
              type="number"
              min="1"
              max="20"
              value={form.top_k}
              onChange={(event) => setForm((current) => ({ ...current, top_k: event.target.value }))}
            />
          </label>

          <div className="actions">
            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? "Running model..." : "Generate recommendation"}
            </button>
          </div>

          {error ? <p className="feedback error">{error}</p> : <p className="feedback">The API accepts either a location string or coordinates.</p>}
        </form>

        <section className="panel results-panel">
          <div className="panel-header compact">
            <div>
              <p className="section-label">Results</p>
              <h2>Retrieved diseases and ranked clinics</h2>
            </div>
            {result ? <span className="status-pill muted">{result.retrieval_mode || "unknown"}</span> : null}
          </div>

          {!result ? (
            <div className="empty-state">
              <h3>Awaiting a prediction</h3>
              <p>Submit a symptom description to see the top diseases and recommended departments or hospitals.</p>
            </div>
          ) : (
            <div className="results-stack">
              <div className="summary-row">
                <div className="summary-card">
                  <span className="summary-label">Resolved location</span>
                  <strong>
                    {result.resolved_location?.source === "direct_coordinates"
                      ? `${formatNumber(result.resolved_location?.lat, 4)}, ${formatNumber(result.resolved_location?.lon, 4)}`
                      : `${result.resolved_location?.lat ?? "-"}, ${result.resolved_location?.lon ?? "-"}`}
                  </strong>
                </div>
                <div className="summary-card">
                  <span className="summary-label">Message</span>
                  <strong>{result.message || "Prediction ready"}</strong>
                </div>
              </div>

              <div className="result-block">
                <h3>Top diseases</h3>
                <div className="stack">
                  {diseases.length > 0 ? (
                    diseases.map((disease, index) => (
                      <article key={`${disease.disease_name || disease.Disease || index}`} className="result-card">
                        <div className="result-card-head">
                          <div>
                            <span className="rank-badge">#{index + 1}</span>
                            <h4>{disease.disease_name || disease.Disease || "Unknown disease"}</h4>
                          </div>
                          <span className="score-pill">{scoreLabel(disease.score ?? disease.confidence ?? disease.similarity)}</span>
                        </div>
                        <p>{disease.description || disease.summary || disease.reason || "No extra description returned."}</p>
                      </article>
                    ))
                  ) : (
                    <p>No reliable diagnosis match returned.</p>
                  )}
                </div>
              </div>

              <div className="result-block">
                <h3>Recommendations</h3>
                {diseaseNames.length > 0 ? (
                  diseaseNames.map((diseaseName) => (
                    <div key={diseaseName} className="recommendation-group">
                      <div className="group-title">
                        <h4>{diseaseName}</h4>
                        <span className="group-count">{(recommendationsByDisease[diseaseName] || []).length} options</span>
                      </div>
                      <div className="stack">
                        {(recommendationsByDisease[diseaseName] || []).map((item, index) => (
                          <article key={`${diseaseName}-${item.clinic_id || item.hospital_name || index}`} className="result-card recommendation-card">
                            <div className="result-card-head">
                              <div>
                                <span className="rank-badge">#{index + 1}</span>
                                <h4>{item.facility_name || item.hospital_name || "Unnamed facility"}</h4>
                              </div>
                              <span className="score-pill">{scoreLabel(item.score)}</span>
                            </div>
                            <p>{item.department_name || item.facility_type || "Care site"}</p>
                            <div className="metric-row">
                              <span>Distance {formatDistance(item.distance_km)}</span>
                              <span>Provider {scoreLabel(item.provider_score)}</span>
                              <span>Drop {scoreLabel(item.drop_rate ? 1 - item.drop_rate : 0)}</span>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="stack">
                    {activeRecommendations.length > 0 ? (
                      activeRecommendations.map((item, index) => (
                        <article key={`${item.clinic_id || item.hospital_name || index}`} className="result-card recommendation-card">
                          <div className="result-card-head">
                            <div>
                              <span className="rank-badge">#{index + 1}</span>
                              <h4>{item.facility_name || item.hospital_name || "Unnamed facility"}</h4>
                            </div>
                            <span className="score-pill">{scoreLabel(item.score)}</span>
                          </div>
                          <p>{item.department_name || item.facility_type || "Care site"}</p>
                          <div className="metric-row">
                            <span>Distance {formatDistance(item.distance_km)}</span>
                            <span>Provider {scoreLabel(item.provider_score)}</span>
                            <span>Drop {scoreLabel(item.drop_rate ? 1 - item.drop_rate : 0)}</span>
                          </div>
                        </article>
                      ))
                    ) : (
                      <p>No recommendation rows returned.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}