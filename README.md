# Agentic ML Pipeline

A desktop app for end-to-end ML classification on any CSV dataset. Upload data, pick a target column, and step through feature selection, model training, evaluation, and probability scoring — with human-in-the-loop review at every stage.

**Stack:** Tauri v2 · Svelte 5 · Tailwind CSS 4 · FastAPI · scikit-learn

---

## Prerequisites

Install these before anything else.

| Tool | macOS | Windows |
|---|---|---|
| Python 3.10+ | `brew install python` | [python.org](https://www.python.org/downloads/) — tick "Add to PATH" |
| Node.js 18+ | `brew install node` | [nodejs.org](https://nodejs.org/) LTS |
| Rust | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` | [rustup.rs](https://rustup.rs/) |
| Xcode CLI (macOS only) | `xcode-select --install` | — |
| C++ Build Tools + WebView2 (Windows only) | — | [tauri.app/start/prerequisites](https://tauri.app/start/prerequisites/) |

---

## Setup

### 1. Python backend

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pandas numpy scikit-learn scipy joblib python-dotenv
```

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn pandas numpy scikit-learn scipy joblib python-dotenv
```

### 2. Frontend

```bash
cd ui
npm install
```

---

## Running (development)

Open two terminals from the project root.

**Terminal 1 — API server**

macOS/Linux:
```bash
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Windows:
```powershell
venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — Desktop app**

```bash
cd ui
npm run tauri dev
```

The Tauri window opens automatically. The API must be running first.

> **Browser-only** (skips Rust/Tauri): run `npm run dev` inside `ui/` and open `http://localhost:5173`. API still needs to be on port 8000.

---

## Building a distributable

```bash
cd ui
npm run tauri build
```

Output locations:
- **macOS:** `ui/src-tauri/target/release/bundle/macos/` (.app + .dmg)
- **Windows:** `ui/src-tauri/target/release/bundle/msi/` (.msi) or `nsis/` (.exe installer)

First build takes several minutes — Rust compiles from scratch.

---

## Pipeline stages

| # | Stage | What happens | Output |
|---|---|---|---|
| 1 | **ETL** | Upload CSV, pick target column, keep/drop columns | `data/cleaned_fraud.csv` |
| 2 | **Stats** | Correlation, VIF, mutual information → feature selection | `data/selected_features.json` |
| 3 | **Model** | Train RandomForest with configurable hyperparameters | `data/model.pkl`, `data/model_metrics.json` |
| 4 | **Evaluate** | Threshold tuning, precision/recall tradeoff | `data/eval_report.json` |
| 5 | **Score** | Run model on full dataset, probability + segment per row | `data/scored_output.csv` |

Scored output includes all original columns plus:
- `probability` — model's predicted probability (0–1)
- `segment_name` — Low / Medium / High / Very High
- `segment_number` — 1 / 2 / 3 / 4

---

## Project structure

```
api/
  main.py               Route handlers
  pipeline_runner.py    All ML computation
  state.py              In-memory session state
  schemas.py            Pydantic models

ui/
  src/
    App.svelte                    Root layout + sidebar stepper
    components/stages/            ETLStage, StatsStage, ModelStage, EvaluateStage
    components/shared/            Reusable UI components
    api/client.js                 All fetch calls to the API
  src-tauri/                      Rust / Tauri shell

data/                             Created at runtime (gitignored)
```

---

## Troubleshooting

**`uvicorn` not found** — activate the venv first (`source venv/bin/activate` or `venv\Scripts\activate`).

**Tauri build fails on Windows** — install Microsoft C++ Build Tools and WebView2 Runtime. Full guide: [tauri.app/start/prerequisites](https://tauri.app/start/prerequisites/).

**`npm run tauri dev` hangs or errors** — make sure port 5173 is free. Kill any stale Vite processes and retry.

**CORS errors in browser mode** — the API allows all origins in dev. Confirm `uvicorn` is running on port 8000.
