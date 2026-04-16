# Vercel Deployment Guide for Healthcare AI

## Overview
This project now supports a clean **frontend + backend** separation:
- **Frontend**: Next.js app on Vercel (in `web/`)
- **Backend**: Python FastAPI service (can run on Render, Railway, Fly.io, or any server that supports Python)

## Quick Start for Vercel

### 1. Deploy the Python Backend
Choose one of these platforms:

**Option A: Render (easiest)**
- Push the repo to GitHub
- Go to [render.com](https://render.com)
- Create a new "Blueprint" deployment
- Select this repo and apply `render.yaml`
- Once deployed, note the public URL (e.g., `https://healthcare-ai.onrender.com`)

**Option B: Railway or Fly.io**
- Follow their respective docs for Python/FastAPI deployment
- Ensure the service is publicly accessible

**Option C: Self-hosted**
- Run `uvicorn app.main:app --host 0.0.0.0 --port 8000` on your server
- Ensure it's accessible from the internet

### 2. Deploy the Frontend to Vercel

**From GitHub:**
1. Push this repo to GitHub (if not already there)
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project" → Select this repo
4. Set **Root Directory** to `healthcare-ai/web`
5. Add Environment Variable:
   - Name: `HEALTHCARE_AI_API_BASE_URL`
   - Value: `https://your-backend-url.onrender.com` (or wherever your Python API is hosted)
6. Click "Deploy"

**From CLI:**
```bash
cd healthcare-ai/web
npm install
vercel
```

When prompted:
- Link to Vercel account (or create one)
- Accept project defaults
- Add the `HEALTHCARE_AI_API_BASE_URL` environment variable via the CLI or dashboard

### 3. Verify It Works
1. Open your Vercel deployment URL in a browser
2. Enter a symptom description (or use one of the examples)
3. Verify the response comes from your backend

## Environment Variables

### On Vercel Dashboard
- `HEALTHCARE_AI_API_BASE_URL`: Public URL of your Python backend (e.g., `https://healthcare-ai.onrender.com`)

### Local Development
Create a `.env.local` file in `healthcare-ai/web/`:
```
HEALTHCARE_AI_API_BASE_URL=http://localhost:8000
```

Then run:
```bash
cd healthcare-ai/web
npm install
npm run dev
```

And in another terminal:
```bash
cd healthcare-ai
uvicorn app.main:app --reload
```

Then visit `http://localhost:3000`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Vercel (Next.js Frontend)                 │
│  ┌─────────────────────────────────────────────────┐│
│  │ /                        (React UI)              ││
│  │ /api/predict             (API Proxy Route)       ││
│  └─────────────────────────────────────────────────┘│
└────────────────┬────────────────────────────────────┘
                 │ (forwards POST /predict)
                 ↓
        ┌────────────────────────────┐
        │  Python Backend            │
        │  (Render / Railway / etc)  │
        │  ┌────────────────────────┐│
        │  │ POST /predict          ││
        │  │ (FastAPI + ML models)  ││
        │  └────────────────────────┘│
        └────────────────────────────┘
```

## Troubleshooting

**"502 Could not reach the backend"**
- Check that `HEALTHCARE_AI_API_BASE_URL` is set correctly on Vercel
- Ensure the Python backend is running and publicly accessible
- Test the backend URL in your browser: `https://your-backend.com/docs`

**"API returns 422"**
- Make sure you provide either `location` text or both `lat` and `lon` coordinates
- Check the error message for details

**Build fails on Vercel**
- Ensure `Root Directory` is set to `healthcare-ai/web`
- Check that `package.json` exists in that directory
- Verify no conflicting Next.js config

## Rollback or Update

To change the backend URL:
1. Go to Vercel Project Settings → Environment Variables
2. Update `HEALTHCARE_AI_API_BASE_URL`
3. Redeploy (or changes auto-apply on next deployment)

To update the frontend code:
1. Push changes to GitHub
2. Vercel auto-redeploys on push to main branch

## Cost Notes
- **Vercel**: Free tier covers this use case (up to 100GB bandwidth/month)
- **Render**: Free tier may sleep after 15 min of inactivity; use paid tier for always-on
- **Railway**: Generous free tier with always-on
- **Fly.io**: Similar to Railway, good for always-on services

---

**Need help?** Check:
- [Next.js docs](https://nextjs.org/docs)
- [FastAPI docs](https://fastapi.tiangolo.com)
- [Vercel docs](https://vercel.com/docs)
