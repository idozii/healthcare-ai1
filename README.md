# Healthcare Diagnosis + Recommendation System

## Goal
Build a web service that:
1. Takes user symptom text
2. Returns top-5 likely diseases
3. Recommends best departments or hospitals based on:
   - distance
   - provider performance
   - drop-off rate
   - patient flow efficiency

## Architecture
User Input -> Disease Retrieval (Embedding + FAISS)
           -> Top-K Diseases
           -> Department Mapping
           -> Scoring Engine
           -> Ranked Hospitals

## Stack
- FastAPI for the diagnosis and recommendation backend
- Next.js for the deployable frontend
- SentenceTransformers
- FAISS
- PostgreSQL (optional)
- Pandas / NumPy
- NetworkX (optional)

## Project Structure
healthcare-ai/
|- app/
|  |- main.py
|  |- api/
|  |  |- routes.py
|  |- models/
|  |- services/
|  |- data/
|  |- utils/
|  |- config.py
|- web/
|  |- app/
|  |  |- api/predict/route.js
|  |  |- globals.css
|  |  |- layout.js
|  |  |- page.js
|  |- package.json
|  |- next.config.mjs
|- notebooks/
|- requirements.txt
|- README.md

## Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   pip install -r requirements.txt

## Run Server
uvicorn app.main:app --reload

## Deploy on Vercel
The easiest Vercel path is to deploy the Next.js frontend in `web/` and keep the Python backend running separately.

1. Deploy the Python API anywhere that can run FastAPI, such as Render, Railway, Fly.io, or a VM.
2. Set `HEALTHCARE_AI_API_BASE_URL` in the Vercel project to the public URL of that backend.
3. In Vercel, set the project root directory to `healthcare-ai/web`.
4. Deploy the Next.js app.

The frontend will call `/api/predict`, and that route proxies requests to the Python backend.

### Frontend setup
From `healthcare-ai/web`:

1. Install dependencies: `npm install`
2. Start local dev server: `npm run dev`
3. Build for production: `npm run build`

### Environment variables for Vercel
- `HEALTHCARE_AI_API_BASE_URL=https://your-backend.example.com`

### Local development
- Run the Python backend: `uvicorn app.main:app --reload`
- Run the Next.js frontend in another terminal: `cd web && npm run dev`

## Deploy on Render
This project still includes the Python deployment path with `render.yaml`.

Quick steps:
1. Push code to GitHub.
2. In Render dashboard, click New + -> Blueprint.
3. Select your repository and apply the Blueprint.

Render will auto-configure:
- Build command: use `healthcare-ai/` as the working directory if the repo is deployed from the root
- Start command: use `healthcare-ai/` as the working directory if the repo is deployed from the root
- Environment variables from render.yaml.

Optional (recommended) in Render dashboard Environment Variables:
- MIN_DISEASE_CONFIDENCE=0.20
- HYBRID_DENSE_WEIGHT=0.65
- RETRIEVAL_CANDIDATE_POOL=120
- RETRIEVAL_QUERY_CACHE_SIZE=256

Local override for full semantic mode:
- FORCE_OFFLINE_RETRIEVER=0 uvicorn app.main:app --reload

## Test API
POST /predict
{
  "text": "chest pain and shortness of breath",
  "lat": -33.86,
  "lon": 151.20,
  "top_k": 5
}

## Clinic Matrix + Diagnosis Mapping
To enable diagnosis-specific clinic scoring with these files:
- clinic_profiles.csv
- clinic_retention.csv
- clinic_diagnosis_volume.csv

Add a manual mapping table:
- disease_to_code_manual.csv with columns: disease_name,DiagnosisValue

Then run:
- Dry run (no write):
   python scripts/map_disease_to_diagnosis_value.py --project-root .
- Apply updates into app/data/diseases.csv:
   python scripts/map_disease_to_diagnosis_value.py --project-root . --write

Auto-suggest DiagnosisValue from diagnosis dictionary:
- Dry run with suggestions:
   python scripts/map_disease_to_diagnosis_value.py --project-root . --auto-suggest
- Auto-apply confident suggestions and write:
   python scripts/map_disease_to_diagnosis_value.py --project-root . --auto-suggest --min-score 0.72 --write

The script also writes:
- disease_mapping_unresolved.csv
so you can quickly review diseases that still need a valid DiagnosisValue.
- disease_code_suggestions.csv
  includes top candidate codes and similarity scores per disease.

## Next Upgrade Ideas
- FAISS IVF index for faster search
- Caching embeddings with Redis
- Graph-based ranking using NetworkX
- Explanation layer for recommendation transparency
