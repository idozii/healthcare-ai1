from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="Healthcare Diagnosis + Recommendation System",
    docs_url="/docs",
    openapi_url="/openapi.json",
)
app.include_router(router)

# Mount static files only if directory exists
static_dir = Path(__file__).resolve().parents[1]
if static_dir.exists():
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    except Exception as e:
        print(f"Warning: Could not mount static files: {e}")

@app.on_event("startup")
async def startup_event():
    print("✓ Healthcare API starting up...")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
		return """
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
		<title>MediPower</title>
	<style>
		:root {
			--bg: #f4f7f3;
			--bg-alt: #eaf2ed;
			--panel: #ffffff;
			--panel-alt: #fbfdfb;
			--ink: #1f2a24;
			--muted: #5f6f65;
			--brand: #0e7a64;
			--brand-deep: #0a5e4d;
			--accent: #d9f3e7;
			--danger: #b3261e;
			--border: #dfe8e2;
			--border-strong: #cfdad3;
			--surface: #ffffff;
			--surface-soft: #f7faf8;
			--surface-alt: #f4faf7;
			--shadow: 0 10px 28px rgba(24, 50, 41, 0.06);
			--hero-start: #0b6f5b;
			--hero-end: #1ca889;
			--hero-shadow: 0 14px 36px rgba(14, 122, 100, 0.22);
			--input-bg: #ffffff;
			--button-secondary-bg: #ebf3ef;
			--button-secondary-ink: #2c4638;
			--item-bg: #ffffff;
			--item-border: #e9efea;
			--radius: 16px;
			--space-1: clamp(10px, 1.4vw, 14px);
			--space-2: clamp(12px, 1.7vw, 18px);
			--ease-smooth: cubic-bezier(0.2, 0.7, 0.2, 1);
		}
		body[data-theme="dark"] {
			--bg: #0b1110;
			--bg-alt: #101918;
			--panel: #101916;
			--panel-alt: #111c19;
			--ink: #edf4ef;
			--muted: #9ab0a6;
			--brand: #42c5a0;
			--brand-deep: #2ab084;
			--accent: #153a31;
			--danger: #ff8e84;
			--border: #22342f;
			--border-strong: #30453f;
			--surface: #111916;
			--surface-soft: #0f1715;
			--surface-alt: #13201d;
			--shadow: 0 14px 32px rgba(0, 0, 0, 0.28);
			--hero-start: #123f34;
			--hero-end: #1c6a56;
			--hero-shadow: 0 16px 38px rgba(0, 0, 0, 0.28);
			--input-bg: #0f1715;
			--button-secondary-bg: #182521;
			--button-secondary-ink: #dfece6;
			--item-bg: #101916;
			--item-border: #22332d;
		}
		* { box-sizing: border-box; }
		body {
			margin: 0;
			min-height: 100vh;
			font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
			color: var(--ink);
			background:
				radial-gradient(1200px 500px at 100% -10%, color-mix(in srgb, var(--brand) 18%, transparent) 0%, transparent 55%),
				radial-gradient(900px 400px at -20% 0%, color-mix(in srgb, var(--accent) 70%, transparent) 0%, transparent 55%),
				var(--bg);
			padding:
				max(14px, env(safe-area-inset-top))
				max(14px, env(safe-area-inset-right))
				max(14px, env(safe-area-inset-bottom))
				max(14px, env(safe-area-inset-left));
			font-size: clamp(14px, 0.9vw, 16px);
		}
		.wrap {
			max-width: 1160px;
			margin: 0 auto;
			display: grid;
			gap: var(--space-2);
		}
		.hero {
			background: linear-gradient(145deg, var(--hero-start), var(--hero-end));
			color: #fff;
			border-radius: var(--radius);
			padding: clamp(16px, 2.2vw, 24px);
			box-shadow: var(--hero-shadow);
			display: grid;
			gap: 8px;
			justify-items: center;
			text-align: center;
			position: relative;
		}
		.hero-actions {
			position: absolute;
			top: 12px;
			right: 12px;
			display: flex;
			gap: 8px;
		}
		.theme-toggle {
			width: auto;
			min-width: 112px;
			padding: 8px 12px;
			border: 1px solid rgba(255, 255, 255, 0.28);
			background: rgba(255, 255, 255, 0.14);
			color: #fff;
			backdrop-filter: blur(10px);
			box-shadow: none;
		}
		.theme-toggle:hover {
			transform: translateY(-1px);
			background: rgba(255, 255, 255, 0.22);
			box-shadow: none;
		}
		.hero .kicker {
			font-size: 0.78rem;
			letter-spacing: 0.14em;
			text-transform: uppercase;
			opacity: 0.88;
			margin-bottom: 8px;
		}
		.hero h1 {
			margin: 0;
			font-size: clamp(1.45rem, 2.3vw, 2.05rem);
			letter-spacing: 0.2px;
		}
		.hero p {
			margin: 0 auto;
			opacity: 0.92;
			max-width: 760px;
			font-size: clamp(0.94rem, 1.05vw, 1rem);
			line-height: 1.45;
		}
		.brand-mark {
			display: grid;
			place-items: center;
			width: 138px;
			height: 138px;
			margin-bottom: 2px;
		}
		.brand-mark img {
			display: block;
			width: 100%;
			height: 100%;
			object-fit: contain;
			filter: drop-shadow(0 14px 26px rgba(0, 0, 0, 0.26));
		}
		.helper-note {
			margin-top: 6px;
			font-size: 0.82rem;
			color: var(--muted);
		}
		.alert-banner {
			border-color: #ffd4d1;
			background: #fff1ef;
			color: #8a1c14;
		}
		.panel {
			background: var(--panel);
			border-radius: var(--radius);
			padding: clamp(14px, 1.8vw, 20px);
			border: 1px solid var(--border);
			box-shadow: var(--shadow);
		}
		.grid {
			display: grid;
			gap: var(--space-1);
			grid-template-columns: minmax(0, 1.55fr) minmax(260px, 1fr);
		}
		label {
			font-size: clamp(0.84rem, 1vw, 0.9rem);
			color: var(--muted);
			display: block;
			margin-bottom: 6px;
		}
		input, textarea, button {
			width: 100%;
			border-radius: 12px;
			border: 1px solid var(--border-strong);
			font: inherit;
			font-size: 16px;
		}
		textarea {
			resize: vertical;
			min-height: clamp(96px, 15vh, 150px);
			padding: 10px 12px;
			line-height: 1.45;
			background: var(--input-bg);
			color: var(--ink);
		}
		input {
			padding: 10px 12px;
			min-height: 44px;
			background: var(--input-bg);
			color: var(--ink);
		}
		.actions {
			display: flex;
			gap: var(--space-1);
			margin-top: 12px;
			flex-wrap: wrap;
		}
		button {
			width: auto;
			border: 0;
			background: var(--brand);
			color: #fff;
			padding: 10px 16px;
			min-height: 44px;
			font-weight: 600;
			cursor: pointer;
			transition: transform 0.14s var(--ease-smooth), box-shadow 0.18s var(--ease-smooth), background 0.18s var(--ease-smooth);
		}
		.actions button {
			width: auto;
			flex: 0 0 auto;
		}
		button:hover {
			transform: translateY(-1px);
			background: var(--brand-deep);
			box-shadow: 0 8px 18px rgba(10, 94, 77, 0.25);
		}
		button.secondary {
			background: var(--button-secondary-bg);
			color: var(--button-secondary-ink);
			box-shadow: none;
		}
		button.secondary:hover {
			background: color-mix(in srgb, var(--button-secondary-bg) 84%, var(--brand) 16%);
		}
		body[data-theme="dark"] .hero {
			background: linear-gradient(145deg, #102c26, #163d35 54%, #1f5a4c);
			border: 1px solid rgba(255, 255, 255, 0.08);
			box-shadow: 0 20px 48px rgba(0, 0, 0, 0.34);
		}
		body[data-theme="dark"] .panel,
		body[data-theme="dark"] .card,
		body[data-theme="dark"] .choice,
		body[data-theme="dark"] .item {
			backdrop-filter: blur(16px);
		}
		body[data-theme="dark"] .panel,
		body[data-theme="dark"] .card,
		body[data-theme="dark"] .item {
			background: rgba(16, 25, 22, 0.78);
			border-color: rgba(255, 255, 255, 0.08);
		}
		body[data-theme="dark"] .choice {
			background: rgba(16, 25, 22, 0.92);
			border-color: rgba(255, 255, 255, 0.08);
			box-shadow: 0 12px 24px rgba(0, 0, 0, 0.22);
		}
		body[data-theme="dark"] .choice-sub {
			background: rgba(21, 35, 31, 0.95);
			border-color: rgba(255, 255, 255, 0.08);
			color: #d4e4dc;
		}
		body[data-theme="dark"] .meta-chip,
		body[data-theme="dark"] .recommend-badge,
		body[data-theme="dark"] .chip,
		body[data-theme="dark"] .disease-action {
			border-color: rgba(255, 255, 255, 0.10);
		}
		body[data-theme="dark"] .meta-chip {
			background: rgba(24, 41, 36, 0.95);
			color: #d9ebe3;
		}
		body[data-theme="dark"] .recommend-badge {
			background: rgba(117, 93, 28, 0.22);
			color: #ffe39c;
		}
		body[data-theme="dark"] .chip {
			background: rgba(66, 197, 160, 0.18);
			color: #d5f5ea;
		}
		body[data-theme="dark"] .disease-action {
			background: rgba(28, 55, 46, 0.95);
			color: #d9f6eb;
		}
		body[data-theme="dark"] .travel-pill {
			background: rgba(16, 25, 22, 0.9);
			border-color: rgba(255, 255, 255, 0.08);
		}
		body[data-theme="dark"] .travel-label,
		body[data-theme="dark"] .travel-note,
		body[data-theme="dark"] .detail-label,
		body[data-theme="dark"] .metric-head,
		body[data-theme="dark"] .capability-group-title,
		body[data-theme="dark"] .status,
		body[data-theme="dark"] .hero .kicker {
			color: #a7bbb2;
		}
		body[data-theme="dark"] .travel-value {
			color: #f3fbf7;
		}
		body[data-theme="dark"] .capability-chip {
			background: rgba(22, 34, 30, 0.95);
			border-color: rgba(255, 255, 255, 0.09);
			color: #e8f4ef;
		}
		body[data-theme="dark"] .capability-chip.ed {
			background: rgba(14, 122, 100, 0.16);
			border-color: rgba(14, 122, 100, 0.35);
		}
		body[data-theme="dark"] .capability-chip.icu {
			background: rgba(75, 123, 236, 0.14);
			border-color: rgba(75, 123, 236, 0.30);
			color: #dfe7ff;
		}
		body[data-theme="dark"] .capability-chip.or {
			background: rgba(244, 162, 97, 0.14);
			border-color: rgba(244, 162, 97, 0.30);
			color: #ffe6cf;
		}
		body[data-theme="dark"] .capability-chip.specialty {
			background: rgba(157, 124, 245, 0.14);
			border-color: rgba(157, 124, 245, 0.30);
			color: #ece4ff;
		}
		body[data-theme="dark"] .hero-actions .theme-toggle {
			background: rgba(255, 255, 255, 0.10);
			border-color: rgba(255, 255, 255, 0.16);
			color: #fff;
		}
		body[data-theme="dark"] .brand-mark {
			background: transparent;
			border: 0;
		}
		body[data-theme="dark"] .alert-banner {
			background: rgba(74, 27, 24, 0.95);
			border-color: rgba(255, 142, 132, 0.24);
			color: #ffd6d1;
		}
		.status {
			font-size: 0.92rem;
			color: var(--muted);
			margin-top: 8px;
			min-height: 20px;
		}
		.status.error {
			color: var(--danger);
		}
		.cols {
			display: grid;
			gap: 14px;
			grid-template-columns: minmax(280px, 1fr) minmax(0, 1.25fr);
			align-items: start;
		}
		.card {
			background: var(--panel-alt);
			border: 1px solid var(--border);
			border-radius: 14px;
			padding: var(--space-1);
		}
		.card h3 {
			margin: 0 0 10px;
			font-size: 1rem;
		}
		.item {
			background: var(--item-bg);
			border: 1px solid var(--item-border);
			border-radius: 10px;
			padding: 10px;
			margin-bottom: 8px;
		}
		.chip {
			display: inline-block;
			background: var(--accent);
			color: #205a4a;
			padding: 2px 8px;
			border-radius: 999px;
			font-size: 0.78rem;
			margin-right: 6px;
		}
		.disease-title {
			display: flex;
			justify-content: space-between;
			align-items: center;
			gap: 8px;
			margin-bottom: 4px;
		}
		.disease-action {
			border: 1px solid #c5ddd1;
			background: #f3fbf7;
			color: #1f5b47;
			border-radius: 8px;
			padding: 4px 8px;
			width: auto;
			font-size: 0.8rem;
			font-weight: 600;
		}
		.choice {
			border: 1px solid #d8e9df;
			border-radius: 12px;
			background: #fff;
			padding: clamp(12px, 1.2vw, 14px);
			margin-bottom: 10px;
			box-shadow: 0 8px 18px rgba(16, 60, 48, 0.05);
		}
		.choice h4 {
			margin: 0;
			font-size: 1rem;
		}
		.choice-head {
			display: flex;
			justify-content: space-between;
			align-items: flex-start;
			gap: 8px;
			margin-bottom: 10px;
		}
		.choice-sub {
			font-size: 0.86rem;
			color: #4d6359;
			margin-top: 6px;
			background: #f4faf7;
			border: 1px solid #ddece3;
			border-radius: 10px;
			padding: 8px 9px;
		}
		.choice-meta {
			display: flex;
			flex-wrap: wrap;
			gap: 6px;
			margin-bottom: 10px;
		}
		.meta-chip {
			font-size: 0.78rem;
			background: #eef7f2;
			color: #285645;
			border: 1px solid #d6e9df;
			padding: 4px 8px;
			border-radius: 999px;
		}
		.recommend-badge {
			color: #886100;
			background: #fff6d8;
			padding: 3px 8px;
			border-radius: 999px;
			font-size: 0.8rem;
			margin-left: 8px;
		}
		.travel-grid {
			display: grid;
			grid-template-columns: repeat(3, minmax(120px, 1fr));
			gap: 8px;
		}
		.travel-pill {
			background: #f4faf7;
			border: 1px solid #dbebe2;
			border-radius: 10px;
			padding: 7px 9px;
			line-height: 1.2;
		}
		.travel-pill.level-fast {
			background: #ecfaf2;
			border-color: #cbead8;
		}
		.travel-pill.level-medium {
			background: #f4f9ef;
			border-color: #dce8cf;
		}
		.travel-pill.level-slow {
			background: #fff8eb;
			border-color: #f0dfbd;
		}
		.travel-pill.level-extreme {
			background: #fff2f0;
			border-color: #f1d2cc;
		}
		.travel-label {
			display: block;
			font-size: 0.74rem;
			color: #5a6f64;
			text-transform: uppercase;
			letter-spacing: 0.06em;
			margin-bottom: 4px;
		}
		.travel-value {
			font-size: 0.9rem;
			color: #1f2a24;
			font-weight: 600;
		}
		.travel-note {
			display: block;
			margin-top: 3px;
			font-size: 0.74rem;
			color: #6a7f74;
		}
		.detail-row {
			display: grid;
			grid-template-columns: 130px 1fr;
			gap: 8px;
			padding: 7px 0;
			border-bottom: 1px dashed #e3ece7;
			align-items: start;
		}
		.detail-row:last-child {
			border-bottom: 0;
		}
		.detail-label {
			color: var(--muted);
			font-size: 0.86rem;
		}
		.detail-value {
			font-size: 0.93rem;
		}
		.capability-list {
			display: flex;
			flex-wrap: wrap;
			gap: 6px;
		}
		.capability-groups {
			display: grid;
			gap: 8px;
		}
		.capability-group {
			display: grid;
			gap: 5px;
		}
		.capability-group-title {
			font-size: 0.72rem;
			font-weight: 700;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: #5f7569;
		}
		.capability-chip {
			display: inline-flex;
			align-items: center;
			gap: 5px;
			padding: 4px 9px;
			border-radius: 999px;
			font-size: 0.8rem;
			font-weight: 600;
			line-height: 1.2;
			border: 1px solid var(--border);
			background: var(--surface-soft);
			color: var(--ink);
			transition: transform 160ms var(--ease-smooth), box-shadow 200ms var(--ease-smooth), border-color 200ms var(--ease-smooth);
		}
		.capability-chip:hover {
			transform: translateY(-1px);
			box-shadow: 0 6px 12px rgba(18, 62, 50, 0.12);
			border-color: #bdd8ca;
		}
		.capability-chip .cap-icon {
			font-size: 0.85rem;
		}
		.capability-chip.ed {
			background: color-mix(in srgb, var(--brand) 12%, var(--surface-soft));
			border-color: color-mix(in srgb, var(--brand) 20%, var(--border));
		}
		.capability-chip.icu {
			background: color-mix(in srgb, #4b7bec 12%, var(--surface-soft));
			border-color: color-mix(in srgb, #4b7bec 22%, var(--border));
			color: color-mix(in srgb, #4b7bec 55%, var(--ink));
		}
		.capability-chip.or {
			background: color-mix(in srgb, #f4a261 12%, var(--surface-soft));
			border-color: color-mix(in srgb, #f4a261 22%, var(--border));
			color: color-mix(in srgb, #f4a261 55%, var(--ink));
		}
		.capability-chip.specialty {
			background: color-mix(in srgb, #9d7cf5 12%, var(--surface-soft));
			border-color: color-mix(in srgb, #9d7cf5 22%, var(--border));
			color: color-mix(in srgb, #9d7cf5 55%, var(--ink));
		}
		.metric {
			display: grid;
			gap: 4px;
		}
		.metric-head {
			display: flex;
			justify-content: space-between;
			align-items: center;
			font-size: 0.86rem;
			color: #42584e;
		}
		.metric-track {
			height: 8px;
			border-radius: 999px;
			background: #e8efeb;
			overflow: hidden;
		}
		.metric-fill {
			height: 100%;
			border-radius: 999px;
			background: linear-gradient(90deg, #61b98d, #0f7f67);
		}
		.metric-fill.warn {
			background: linear-gradient(90deg, #f2cf73, #d89722);
		}
		.metric-fill.accent {
			background: linear-gradient(90deg, #78cfd5, #2b8e95);
		}
		@media (max-width: 1024px) {
			.grid, .cols { grid-template-columns: 1fr; }
			.hero h1 { font-size: clamp(1.35rem, 3.5vw, 1.8rem); }
		}
		@media (max-width: 860px) {
			.grid, .cols { grid-template-columns: 1fr; }
			body { font-size: 15px; }
			.travel-grid { grid-template-columns: 1fr; }
			.detail-row { grid-template-columns: 1fr; gap: 4px; }
		}
		@media (max-width: 640px) {
			.hero-actions {
				position: static;
				justify-content: center;
				margin-bottom: 4px;
			}
			.hero, .panel, .card, .choice {
				border-radius: 12px;
				padding: 12px;
			}
			.hero .kicker { letter-spacing: 0.1em; }
			.hero p { line-height: 1.5; }
			.card h3 { font-size: 0.95rem; }
			.choice-head {
				flex-direction: column;
				align-items: flex-start;
			}
			.actions {
				display: grid;
				grid-template-columns: 1fr;
			}
			.actions button {
				width: 100%;
			}
		}
		@media (max-width: 900px) and (orientation: landscape) {
			.wrap {
				gap: 10px;
			}
			.hero {
				padding: 14px 16px;
			}
			.hero h1 {
				margin-bottom: 4px;
				font-size: 1.35rem;
			}
			.panel {
				padding: 12px;
			}
			textarea {
				min-height: 74px;
			}
		}
		@media (min-width: 1400px) {
			.wrap {
				max-width: 1280px;
			}
			.cols {
				grid-template-columns: 1fr 1.35fr;
			}
		}
		@media (prefers-reduced-motion: reduce) {
			*, *::before, *::after {
				animation: none !important;
				transition: none !important;
				scroll-behavior: auto !important;
			}
		}
	</style>
</head>
<body>
	<div class="wrap">
		<section class="hero">
			<div class="hero-actions">
				<button id="themeToggle" class="secondary theme-toggle" type="button">Dark mode</button>
			</div>
			<div class="brand-mark">
				<img src="/static/logo.png" alt="MediPower logo" />
			</div>
			<div class="kicker">Clinical Decision Support</div>
			<h1>MediPower</h1>
			<p>Start with the most likely conditions first, then compare hospital options with clearer travel times, capability fit, and care continuity signals.</p>
		</section>

		<section class="panel">
			<div id="emergencyBanner" class="item alert-banner" style="display:none;"></div>
			<div class="grid">
				<div>
					<label for="symptoms">Symptoms</label>
					<textarea id="symptoms" placeholder="Example: chest pain that gets worse when breathing, with fever and fatigue"></textarea>
				</div>
				<div>
					<label for="location">Your Location</label>
					<input id="location" list="cityHints" type="text" value="Topeka" placeholder="Enter city or ZIP (e.g., Topeka, 66604, Kansas City)" />
					<datalist id="cityHints">
						<option value="Topeka"></option>
						<option value="Junction City"></option>
						<option value="Emporia"></option>
						<option value="Kansas City"></option>
					</datalist>
					<div class="helper-note">Use city or ZIP for better distance accuracy. State-level input is approximate.</div>
				</div>
			</div>
			<div class="actions">
				<button id="runBtn" type="button">Analyze Symptoms</button>
				<button id="sampleBtn" class="secondary" type="button">Try Example</button>
			</div>
			<div id="status" class="status"></div>
		</section>

		<section class="cols">
			<div class="card">
				<h3>Likely Conditions</h3>
				<div id="diseaseList"></div>
			</div>
			<div class="card">
				<h3 id="recHeader">Recommended Hospitals for:</h3>
				<div id="tradeoffBox" class="item" style="display:none;font-size:0.9rem;"></div>
				<div id="recList">
					<div class="item">Select a condition to view detailed hospital comparisons.</div>
				</div>
			</div>
		</section>
	</div>

	<script>
		const statusEl = document.getElementById("status");
		const diseaseListEl = document.getElementById("diseaseList");
		const recListEl = document.getElementById("recList");
		const recHeaderEl = document.getElementById("recHeader");
		const emergencyBannerEl = document.getElementById("emergencyBanner");
		const tradeoffBoxEl = document.getElementById("tradeoffBox");
		const themeToggleEl = document.getElementById("themeToggle");
		let cachedRecommendations = [];
		let cachedRecommendationsByDisease = {};
		const MAX_LIKELY_CONDITIONS = 3;

		function getPreferredTheme() {
			const saved = localStorage.getItem("medipower-theme");
			if (saved === "light" || saved === "dark") return saved;
			return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
		}

		function applyTheme(theme) {
			document.body.dataset.theme = theme;
			if (themeToggleEl) {
				themeToggleEl.textContent = theme === "dark" ? "Light mode" : "Dark mode";
			}
			localStorage.setItem("medipower-theme", theme);
		}

		applyTheme(getPreferredTheme());
		if (themeToggleEl) {
			themeToggleEl.addEventListener("click", () => {
				applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
			});
		}

		function setStatus(message, isError=false) {
			statusEl.textContent = message;
			statusEl.className = isError ? "status error" : "status";
		}

		function score100(value) {
			const n = Number(value);
			if (!Number.isFinite(n)) return 0;
			return Math.max(0, Math.min(100, Math.round(n * 100)));
		}

		function kmToDriveMinutes(km) {
			if (!Number.isFinite(km)) return null;
			const avgSpeedKmh = 70;
			return Math.max(1, Math.round((km / avgSpeedKmh) * 60));
		}

		function kmToTransitMinutes(km) {
			if (!Number.isFinite(km)) return null;
			const avgSpeedKmh = 28;
			return Math.max(5, Math.round((km / avgSpeedKmh) * 60));
		}

		function kmToWalkMinutes(km) {
			if (!Number.isFinite(km)) return null;
			const avgSpeedKmh = 4.8;
			return Math.max(10, Math.round((km / avgSpeedKmh) * 60));
		}

		function waitFromFlow(flowEfficiency) {
			const flow = Number(flowEfficiency);
			if (!Number.isFinite(flow)) return "approximate 2 weeks";
			const weeks = Math.max(1, Math.round((1.2 - Math.min(flow, 1)) * 4));
			return `approximate ${weeks} week${weeks > 1 ? "s" : ""}`;
		}

		function formatDuration(minutes) {
			const total = Math.round(Number(minutes));
			if (!Number.isFinite(total) || total <= 0) return "N/A";

			const days = Math.floor(total / 1440);
			const hours = Math.floor((total % 1440) / 60);
			const mins = total % 60;
			const parts = [];
			if (days > 0) parts.push(`${days}d`);
			if (hours > 0) parts.push(`${hours}h`);
			if (mins > 0 && days === 0) parts.push(`${mins}m`);
			if (!parts.length) parts.push("<1h");

			return parts.join(" ");
		}

		function travelTimeBlock(distanceKm) {
			const driveMins = kmToDriveMinutes(distanceKm);
			const transitMins = kmToTransitMinutes(distanceKm);
			const walkMins = kmToWalkMinutes(distanceKm);

			function travelLevel(mins) {
				if (!Number.isFinite(mins)) return { cls: "level-medium", note: "estimate unavailable" };
				if (mins <= 90) return { cls: "level-fast", note: "quick access" };
				if (mins <= 360) return { cls: "level-medium", note: "moderate trip" };
				if (mins <= 1440) return { cls: "level-slow", note: "long trip" };
				return { cls: "level-extreme", note: "very far" };
			}

			const drive = formatDuration(driveMins);
			const transit = formatDuration(transitMins);
			const walk = formatDuration(walkMins);
			const driveLevel = travelLevel(driveMins);
			const transitLevel = travelLevel(transitMins);
			const walkLevel = travelLevel(walkMins);

			return `
				<div class="travel-grid">
					<div class="travel-pill ${driveLevel.cls}"><span class="travel-label">Drive</span><span class="travel-value">${drive}</span><span class="travel-note">${driveLevel.note}</span></div>
					<div class="travel-pill ${transitLevel.cls}"><span class="travel-label">Transit (est.)</span><span class="travel-value">${transit}</span><span class="travel-note">${transitLevel.note}</span></div>
					<div class="travel-pill ${walkLevel.cls}"><span class="travel-label">Walk (est.)</span><span class="travel-value">${walk}</span><span class="travel-note">${walkLevel.note}</span></div>
				</div>
			`;
		}

		function scoreMetric(label, value, styleClass="") {
			const safe = Math.max(0, Math.min(100, Number(value) || 0));
			return `
				<div class="metric">
					<div class="metric-head"><span>${label}</span><strong>${Math.round(safe)}/100</strong></div>
					<div class="metric-track"><div class="metric-fill ${styleClass}" style="width:${safe}%;"></div></div>
				</div>
			`;
		}

		function capabilityBadges(row) {
			const core = [];
			const advanced = [];
			if (Number(row.has_ed || 0) > 0) core.push({ cls: "ed", icon: "🏥", label: "Emergency Department" });
			if (Number(row.has_icu || 0) > 0) core.push({ cls: "icu", icon: "🫀", label: "ICU" });
			if (Number(row.has_or || 0) > 0) advanced.push({ cls: "or", icon: "🛠", label: "Operating Room" });
			if (Number(row.has_specialty || 0) > 0) advanced.push({ cls: "specialty", icon: "🧬", label: "Specialty Services" });

			if (!core.length && !advanced.length) {
				return `<div class="capability-list"><span class="capability-chip"><span class="cap-icon">🏨</span><span>General Outpatient</span></span></div>`;
			}

			const renderGroup = (title, items) => {
				if (!items.length) return "";
				const chips = items
					.map(({ cls, icon, label }) => `<span class="capability-chip ${cls}"><span class="cap-icon">${icon}</span><span>${label}</span></span>`)
					.join("");
				return `<div class="capability-group"><div class="capability-group-title">${title}</div><div class="capability-list">${chips}</div></div>`;
			};

			return `<div class="capability-groups">${renderGroup("Core", core)}${renderGroup("Advanced", advanced)}</div>`;
		}

		function specialtyContext(score, requiredDepartments, row) {
			const s = score100(score);
			let label = "moderate match";
			if (s >= 80) label = "strong match";
			else if (s >= 60) label = "good match";
			else if (s < 40) label = "limited match";

			const req = (requiredDepartments || "").split("|").map(x => x.trim()).filter(Boolean).join(", ");
			const facilityType = row.facility_type ? String(row.facility_type) : "Unknown facility type";
			return `${s}/100 (${label}${req ? ` • needs: ${req}` : ""} • ${facilityType})`;
		}

		function milesFromKm(km) {
			if (!Number.isFinite(km)) return null;
			return km * 0.621371;
		}

		function diseaseRelevanceScore(disease) {
			const candidates = [
				disease?.confidence,
				disease?.probability,
				disease?.prob,
				disease?.score,
				disease?.relevance,
				disease?.Similarity,
			];
			for (const raw of candidates) {
				const n = Number(raw);
				if (Number.isFinite(n)) {
					if (n > 1) return Math.max(0, Math.min(1, n / 100));
					return Math.max(0, Math.min(1, n));
				}
			}
			return null;
		}

		function selectRelevantDiseases(diseases) {
			const enriched = (diseases || []).map((d, index) => ({
				d,
				index,
				score: diseaseRelevanceScore(d),
			}));

			const hasScore = enriched.some(x => x.score !== null);
			if (!hasScore) {
				return enriched.slice(0, MAX_LIKELY_CONDITIONS).map(x => x.d);
			}

			const ranked = enriched
				.slice()
				.sort((a, b) => {
					const as = a.score ?? -1;
					const bs = b.score ?? -1;
					if (bs !== as) return bs - as;
					return a.index - b.index;
				});
			return ranked.slice(0, MAX_LIKELY_CONDITIONS).map(x => x.d);
		}

		function showEmergencyBanner(diseaseNames, symptomText) {
			const text = (symptomText || "").toLowerCase();
			const names = (diseaseNames || []).map(x => String(x || "").toLowerCase());
			const emergencyHit = text.includes("chest pain") || names.some(n => ["acute coronary", "pericarditis", "myocarditis", "pulmonary embolism"].some(k => n.includes(k)));
			if (emergencyHit) {
				emergencyBannerEl.style.display = "block";
				emergencyBannerEl.textContent = "⚠ Chest pain can be serious. If symptoms are severe, worsening, or associated with shortness of breath/fainting, call 911 or go to the nearest ED immediately.";
			} else {
				emergencyBannerEl.style.display = "none";
				emergencyBannerEl.textContent = "";
			}
		}

		function buildOptionBlock(title, badge, row, specialtyMatch) {
			const retention = (1 - Number(row.drop_rate || 0)) * 100;
			const quality = Number(row.provider_score || 0);
			const totalScore = Math.round(Number(row.score || 0) * 100);
			const specialtyCases = Math.max(10, Math.round((specialtyMatch * 120) + 20));
			const specialtyScore = score100(specialtyMatch);
			const qualityScore = score100(quality);
			const clinicId = row.clinic_id !== undefined && row.clinic_id !== null ? String(row.clinic_id) : null;
			const city = row.city ? String(row.city) : "";
			const address = row.address ? String(row.address) : "";
			const retentionSource = String(row.retention_source || "baseline_proxy");
			const locationBits = [address, city].filter(Boolean).join(", ");
			const capability = capabilityBadges(row);
			const requiredDepartments = row.required_departments || "";
			const altReason = row.option_reason || "";
			const hospitalName = String(row.hospital_name || "Hospital");
			const hospitalLabel = city && !hospitalName.toLowerCase().includes(city.toLowerCase())
				? `${hospitalName} - ${city}`
				: hospitalName;

			return `
				<div class="choice">
					<div class="choice-head">
						<h4>${title}: [${hospitalLabel}]</h4>
						<span class="recommend-badge">${badge}</span>
					</div>
					${altReason ? `<div class="choice-sub">${altReason}</div>` : ""}
					<div class="choice-meta">
						${clinicId ? `<span class="meta-chip">Clinic ID: ${clinicId}</span>` : ""}
						${locationBits ? `<span class="meta-chip">${locationBits}</span>` : ""}
					</div>
					<div class="detail-row"><div class="detail-label">Travel Time</div><div class="detail-value">${travelTimeBlock(Number(row.distance_km))}</div></div>
					<div class="detail-row"><div class="detail-label">Wait Time</div><div class="detail-value">${waitFromFlow(row.flow_efficiency)}</div></div>
					<div class="detail-row"><div class="detail-label">Capabilities</div><div class="detail-value">${capability}</div></div>
					<div class="detail-row"><div class="detail-label">Specialty Fit</div><div class="detail-value">${specialtyContext(specialtyScore / 100, requiredDepartments, row)} (${specialtyCases} similar cases/year)</div></div>
					<div class="detail-row"><div class="detail-label">Performance</div><div class="detail-value">${scoreMetric("Total score", totalScore, "")}${scoreMetric("Quality", qualityScore, "accent")}${scoreMetric("Specialty match", specialtyScore, "warn")}<div style="margin-top:6px;font-size:0.8rem;color:#60746a;">Follow-up retention: ${retention.toFixed(0)}%${retentionSource === "baseline_proxy" ? " (estimated)" : ""}</div></div></div>
				</div>
			`;
		}

		function renderRecommendationChoices(diseaseName, mappedDepartments) {
			recHeaderEl.textContent = `Recommended Hospitals for: ${diseaseName}`;
			const diseaseSpecific = cachedRecommendationsByDisease[diseaseName] || [];

			if (diseaseSpecific.length) {
				cachedRecommendations = diseaseSpecific;
			}

			const deptSet = new Set((mappedDepartments || "").split("|").map(x => x.trim()).filter(Boolean));
			let pool = cachedRecommendations.filter(r => deptSet.has(String(r.department_name || "").trim()));
			if (!pool.length) {
				pool = diseaseSpecific.length ? diseaseSpecific.slice() : cachedRecommendations.slice();
			}

			const optionKey = row => [row.clinic_id, row.hospital_name, row.address, row.city].map(v => String(v || "").trim().toLowerCase()).join("|");
			const uniquePool = [];
			const seen = new Set();
			for (const row of pool) {
				const key = optionKey(row);
				if (seen.has(key)) continue;
				seen.add(key);
				uniquePool.push(row);
			}

			if (uniquePool.length < 3) {
				const broaderPool = diseaseSpecific.length ? diseaseSpecific : cachedRecommendations;
				for (const row of broaderPool) {
					const key = optionKey(row);
					if (seen.has(key)) continue;
					seen.add(key);
					uniquePool.push(row);
					if (uniquePool.length >= 3) break;
				}
			}
			pool = uniquePool;

			if (!pool.length) {
				recListEl.innerHTML = "<div class='item'>No recommendation found for this condition.</div>";
				return;
			}

			const byScore = [...pool].sort((a, b) => Number(b.score || 0) - Number(a.score || 0));
			const byDistance = [...pool].sort((a, b) => Number(a.distance_km || 1e9) - Number(b.distance_km || 1e9));

			const best = byScore[0];
			const usedKeys = new Set([optionKey(best)]);
			const nearest = byDistance.find(x => !usedKeys.has(optionKey(x)));
			if (nearest) usedKeys.add(optionKey(nearest));
			const alternative = byScore.find(x => !usedKeys.has(optionKey(x)));

			const optionRows = [
				{ title: "Option 1", badge: "RECOMMENDED", row: best, reason: "Best overall balance of quality, retention, and capability.", specialty: deptSet.has(String(best.department_name || "").trim()) ? 1 : 0.65 },
			];

			if (nearest) {
				optionRows.push({
					title: "Option 2",
					badge: "NEAREST",
					row: nearest,
					reason: "Closest option by distance/travel time.",
					specialty: deptSet.has(String(nearest.department_name || "").trim()) ? 0.8 : 0.55,
				});
			}

			if (alternative) {
				optionRows.push({
					title: "Option 3",
					badge: "ALTERNATIVE",
					row: alternative,
					reason: "Alternative with different capability/experience tradeoff.",
					specialty: deptSet.has(String(alternative.department_name || "").trim()) ? 0.75 : 0.5,
				});
			}

			optionRows.forEach(o => {
				o.row.required_departments = mappedDepartments || "";
				o.row.option_reason = o.reason;
			});

			if (nearest) {
				const bestMiles = milesFromKm(Number(best.distance_km));
				const nearestMiles = milesFromKm(Number(nearest.distance_km));
				const specialtyBest = optionRows[0].specialty;
				const specialtyNearest = optionRows[1].specialty;
				if (Number.isFinite(bestMiles) && Number.isFinite(nearestMiles)) {
					const diff = Math.abs(bestMiles - nearestMiles);
					const caseGap = Math.max(0, Math.round((specialtyBest - specialtyNearest) * 120));
					tradeoffBoxEl.style.display = "block";
					tradeoffBoxEl.textContent = `Distance tradeoff: nearest option is about ${diff.toFixed(1)} miles ${nearestMiles < bestMiles ? "closer" : "farther"} than the top-ranked option, while the top-ranked option shows about ${caseGap} more similar cases/year.`;
				} else {
					tradeoffBoxEl.style.display = "none";
					tradeoffBoxEl.textContent = "";
				}
			} else {
				tradeoffBoxEl.style.display = "none";
				tradeoffBoxEl.textContent = "";
			}

			const rendered = optionRows.map(o => buildOptionBlock(o.title, o.badge, o.row, o.specialty));
			if (optionRows.length < 3) {
				rendered.push("<div class='item'>Only distinct clinics are shown. Fewer than 3 unique clinic-city options were available for this condition.</div>");
			}
			recListEl.innerHTML = rendered.join("");
		}

		function renderDiseases(diseases) {
			const relevantDiseases = selectRelevantDiseases(diseases);
			if (!relevantDiseases.length) {
				diseaseListEl.innerHTML = "<div class='item'>No disease candidates found.</div>";
				return;
			}

			diseaseListEl.innerHTML = relevantDiseases.map((d, idx) => {
				const name = d.disease_name || d.Disease || "Unknown";
				const desc = d.description || "";
				const mapped = d.mapped_departments || "";
				const deptBadges = mapped
					? mapped.split("|").map(dept => {
						const trimmed = dept.trim();
						if (!trimmed) return "";
						const deptColor = {
							"Cardiology": "#ff6b6b",
							"Emergency": "#ff9100",
							"Pulmonology": "#4dabf7",
							"Internal Medicine": "#69db7c",
							"Dentistry": "#ffd43b",
							"Oral Surgery": "#ffa94d",
							"Psychiatry": "#da77f2",
							"Gastroenterology": "#74c0fc",
							"Neurology": "#b197fc",
							"Orthopedics": "#a8e6cf"
						};
						const bgColor = deptColor[trimmed] || "#a0aec0";
						return `<span style="display:inline-block;background:${bgColor};color:#fff;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;margin-right:6px;margin-top:4px;">${trimmed}</span>`;
					}).join("")
					: "";
				return `
					<div class="item">
						<div class="disease-title">
							<div><span class="chip">#${idx + 1}</span><strong>${name}</strong></div>
							<button class="disease-action" data-name="${name}" data-mapped="${mapped}">Hospital suggestions</button>
						</div>
						<div style="margin-top:4px;font-size:0.9rem;color:#5f6f65;">${desc}</div>
						${deptBadges ? `<div style="margin-top:10px;"><div style="font-size:0.75rem;font-weight:700;color:#5f6f65;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Departments</div><div style="display:flex;flex-wrap:wrap;gap:6px;">${deptBadges}</div></div>` : ""}
					</div>
				`;
			}).join("");

			const actionButtons = diseaseListEl.querySelectorAll(".disease-action");
			actionButtons.forEach(btn => {
				btn.addEventListener("click", () => {
					renderRecommendationChoices(btn.dataset.name || "Diagnosis", btn.dataset.mapped || "");
				});
			});
		}

		async function runPrediction() {
			const text = document.getElementById("symptoms").value.trim();
			const location = document.getElementById("location").value.trim();

			if (!text) {
				setStatus("Please enter symptom text.", true);
				return;
			}
			if (!location) {
				setStatus("Please enter your location (city/address).", true);
				return;
			}

			setStatus("Finding top diagnoses...");
			diseaseListEl.innerHTML = "";
			recHeaderEl.textContent = "Recommended Hospitals for:";
			tradeoffBoxEl.style.display = "none";
			tradeoffBoxEl.textContent = "";
			recListEl.innerHTML = "<div class='item'>Please choose the condition above</div>";
			cachedRecommendations = [];
			cachedRecommendationsByDisease = {};

			try {
				const response = await fetch("/predict", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ text, location, top_k: MAX_LIKELY_CONDITIONS }),
				});

				if (!response.ok) {
					const t = await response.text();
					throw new Error(`API ${response.status}: ${t}`);
				}

				const data = await response.json();
				cachedRecommendations = data.recommendations || [];
				cachedRecommendationsByDisease = data.recommendations_by_disease || {};
				renderDiseases(data.diseases || []);
				showEmergencyBanner((data.diseases || []).map(d => d.disease_name || d.Disease), text);
				if (data.message) {
					setStatus(data.message, true);
				} else if (data.resolved_location && data.resolved_location.note) {
					setStatus(data.resolved_location.note, true);
				} else {
					setStatus("Diagnosis list ready. Click a diagnosis to view recommendations.");
				}
			} catch (err) {
				setStatus(err.message || "Prediction failed.", true);
			}
		}

		document.getElementById("runBtn").addEventListener("click", runPrediction);
		document.getElementById("sampleBtn").addEventListener("click", () => {
			document.getElementById("symptoms").value = "chest pain and shortness of breath";
			document.getElementById("location").value = "Sydney CBD";
			setStatus("Sample input loaded.");
		});
	</script>
</body>
</html>
"""


@app.get("/status")
def status() -> dict:
	return {
		"service": "Healthcare Diagnosis + Recommendation System",
		"status": "ok",
		"docs": "/docs",
	}


@app.get("/health")
def health() -> dict:
	return {"status": "healthy"}
