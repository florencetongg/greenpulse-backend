# Presentation Guide — Influencer Clout Detective

**WIF3009 · Group 11 · 10 min + demo · 11 June 2026**

> **[SHOW]** = open file / slide · **[DEMO]** = live dashboard · Times are approximate — demo is the priority.

---

## Quick reference

### Time budget


| #   | Section                       | Time |
| --- | ----------------------------- | ---- |
| 1   | Opening & problem             | 1:00 |
| 2   | Solution overview             | 1:00 |
| 3   | Dataset & labels              | 1:00 |
| 4   | Agent logic + data flow       | 2:00 |
| 5   | Special component (audit log) | 1:00 |
| 6   | **Live demo**                 | 3:30 |
| 7   | Results + future + duration   | 0:30 |


### Key numbers (memorize)


| Item                       | Value                                   |
| -------------------------- | --------------------------------------- |
| Dataset rows               | 3,000                                   |
| Label `is_fake`            | 0 = authentic (1,941), 1 = fake (1,059) |
| Train / test               | 80% / 20% (2,400 / 600)                 |
| Features after engineering | 40 columns                              |
| Final score                | ML × 0.85 + NLP × 0.15                  |
| Held-out F1                | 0.44 (precision 0.36, recall 0.56)      |
| Project duration           | ~7 weeks (22 Apr – 8 Jun 2026)          |


### Two-presenter split


| Presenter A                            | Presenter B                                       |
| -------------------------------------- | ------------------------------------------------- |
| Problem, dataset, agent logic, results | Architecture, data flow, audit log, **live demo** |


### File map (section → show this)


| Section              | Primary file                         | Lines            |
| -------------------- | ------------------------------------ | ---------------- |
| Problem              | `PROJECT_REPORT.md`                  | §2 (25–33)       |
| Architecture         | `PROJECT_REPORT.md`                  | §6 (144–162)     |
| Dataset / `is_fake`  | `data/processed/data_summary.json`   | 7–18             |
| Stratified split     | `src/feature_engineer.py`            | 262–269          |
| Agent graph          | `supervisor/langgraph_supervisor.py` | 202–217          |
| ML score             | `src/unsupervised_modeling.py`       | 105–113          |
| NLP blend 85/15      | `src/nlp_analyzer.py`                | 30–32, 314–323   |
| Data → API → agent   | `api/main.py`                        | 199–218          |
| Dashboard → API      | `src/dashboard.py`                   | 185–199, 265–268 |
| **Audit log (hero)** | `src/dashboard.py`                   | 534–538          |
| Audit log (code)     | `supervisor/langgraph_supervisor.py` | 79–83            |
| Honest metrics       | `src/holdout_evaluation.py`          | 75–90            |
| Results table        | `PROJECT_REPORT.md`                  | §7 (191–208)     |
| Future work          | `PROJECT_REPORT.md`                  | §12 (346–360)    |
| Phase timeline       | `PROJECT_REPORT.md`                  | §8.1 (227–238)   |


---

## Pre-demo setup

```powershell
cd influencer_clout_detective
# Terminal 1
python scripts/run_api.py
# Terminal 2
python scripts/run_phase5_dashboard.py
```

Open: **[http://localhost:8501](http://localhost:8501)**

**IDE tabs to pre-open:**

1. `supervisor/langgraph_supervisor.py` → lines 202–217
2. `src/dashboard.py` → lines 319–327, 534–538
3. `api/main.py` → lines 199–218
4. `data/processed/data_summary.json`

**Backup if demo is slow:** enable **Skip PDF report generation** in sidebar; show a pre-generated PDF from `reports/agent_runs/`.

### Presenter checklist

- API running (`python scripts/run_api.py`)
- Dashboard running (`python scripts/run_phase5_dashboard.py`)
- Browser on [http://localhost:8501](http://localhost:8501)
- IDE tabs pre-opened (see above)
- Optional: pre-run investigation so PDF exists as backup
- `Skip PDF` toggle tested if time is tight
- Slide deck: problem, architecture, dataset, results, future work

---

## SECTION 1 — Opening & problem (1:00)


| Cue           | File                                |
| ------------- | ----------------------------------- |
| Problem slide | `PROJECT_REPORT.md` §2, lines 25–33 |


**[Slide: Title]**

> "Good morning/afternoon. We are **Group 11**, and our project is **Influencer Clout Detective** — a B2B forensic analytics platform for vetting Instagram influencer portfolios."

**[Slide: Problem]**

> "Brands and agencies spend heavily on influencer marketing. But fake or inauthentic accounts inflate follower counts and waste campaign budget. Manual vetting does not scale when you have hundreds of profiles to review. And most fraud scores are black boxes — compliance teams cannot audit how a decision was made."

> "Our solution combines **unsupervised machine learning**, **behavioral and NLP signals**, and a **multi-agent pipeline** orchestrated by LangGraph. Every run produces evidence an analyst can review — not just a number."

---

## SECTION 2 — Solution overview (1:00)


| Cue                  | File                                             |
| -------------------- | ------------------------------------------------ |
| Architecture slide   | `PROJECT_REPORT.md` §6, lines 144–162            |
| Code peek (optional) | `supervisor/langgraph_supervisor.py` lines 60–71 |
| Phase map slide      | `PROJECT_REPORT.md` §8.1, lines 227–238          |


**[Slide: Architecture]**

> "Here is the high-level flow. A marketing analyst uploads a CSV through our **Streamlit dashboard**. The dashboard calls our **FastAPI** endpoint, which hands the data to a **LangGraph Supervisor**. The supervisor runs six specialized agents — EDA, statistical modeling, behavioral checks, risk scoring, NLP analysis, and report generation. Outputs land in `reports/agent_runs/` — plots, scored CSVs, and a forensic PDF."

**[Optional code peek]**

> "The supervisor is the brain. It owns the shared investigation state — the dataframe, scores, and critically, the **audit log** — and routes work through a LangGraph StateGraph."

**[Slide: Phase map]**

> "We built this across **seven phases**: data prep, EDA, modeling, NLP, dashboard and API, forensic reports, and end-to-end testing with CI. Twenty-five pytest cases run on every push."

---

## SECTION 3 — Dataset & labels (1:00)


| Cue              | File                                          |
| ---------------- | --------------------------------------------- |
| Dataset slide    | `PROJECT_REPORT.md` §4.1, lines 54–65         |
| Class counts     | `data/processed/data_summary.json` lines 7–18 |
| Stratified split | `src/feature_engineer.py` lines 262–269       |
| Label usage rule | `PROJECT_REPORT.md` line 65                   |


**[Slide: Dataset table]**

> "Our data comes from Kaggle — the **Fake Social Media Account Detection Dataset**. Three thousand Instagram-style profiles, twenty-four raw columns."

**[SHOW: `data/processed/data_summary.json`]**

> "The ground-truth label is `**is_fake`**. Zero means authentic — we have one thousand nine hundred forty-one of those. One means fake — one thousand fifty-nine. That is roughly sixty-five percent authentic, thirty-five percent fake."

**[SHOW: `src/feature_engineer.py` lines 262–269]**

> "Phase 1 does an **eighty-twenty stratified split** on `is_fake`, with random seed forty-two. That gives us two thousand four hundred training rows and six hundred held-out test rows. We also engineer sixteen new features — log transforms, ratios, engagement anomalies — bringing the total to **forty columns**."

**[SHOW: `PROJECT_REPORT.md` line 65]**

> "This is the most important point about labels: `**is_fake` is used only for held-out evaluation**. Our unsupervised models never see labels during scoring. When a client uploads a portfolio, we score it the same way we would in production — without peeking at ground truth."

---

## SECTION 4 — Agent logic & how data flows (2:00)

### Agent logic (1:10)


| Cue              | File                                               |
| ---------------- | -------------------------------------------------- |
| Agent graph      | `supervisor/langgraph_supervisor.py` lines 202–217 |
| ML score formula | `src/unsupervised_modeling.py` lines 105–113       |
| NLP blend        | `src/nlp_analyzer.py` lines 30–32, 314–323         |


**[SHOW: `supervisor/langgraph_supervisor.py` lines 202–217]**

> "The agent pipeline is a LangGraph StateGraph with six nodes. Execution order is:"

> "**One — Forensic Analyst.** Runs EDA and log-normal validation on followers, following, and posts."

> "**Two — Statistician.** Applies RobustScaler, PCA at ninety-five percent variance, then Isolation Forest and Local Outlier Factor."

> "**Three — Behavioral Analyst.** Ensures behavioral feature columns exist so downstream steps do not fail."

> "**Four — Risk Scoring Agent.** Maps anomaly scores into risk bands — low, medium, or high."

> "**Five — NLP Investigator.** Scores caption similarity, spam comment rates, username randomness."

> "**Six — Report Writer.** Produces Markdown and PDF forensic reports."

**[SHOW: `src/unsupervised_modeling.py` lines 105–113]**

> "The ML authenticity score is: **one minus normalized anomaly score, times one hundred**."

**[SHOW: `src/nlp_analyzer.py` lines 30–32 and 314–323]**

> "When NLP is enabled, the final score blends **eighty-five percent ML** and **fifteen percent behavioral/NLP**. That is explicit in `nlp_analyzer.py`."

> "If LangGraph fails, we fall back to a deterministic `InvestigationPipeline` — same tools, same artifacts. No LLM API key is required for the default demo."

### How the agent gets data (0:50)


| Cue              | File                                      |
| ---------------- | ----------------------------------------- |
| Kaggle download  | `src/data_loader.py` lines 27–43          |
| Sample data path | `src/dashboard.py` line 39                |
| Dashboard → API  | `src/dashboard.py` lines 185–199, 265–268 |
| API → supervisor | `api/main.py` lines 199–218               |


**[SHOW: `src/data_loader.py` lines 27–43]**

> "Data enters three ways. **Offline:** Phase 1 downloads from Kaggle via `run_phase1_data_prep.py --download` and writes processed splits to `data/processed/`."

**[SHOW: `src/dashboard.py` line 39]**

> "**Demo path:** the dashboard loads `train_features.csv` as the sample — two thousand four hundred profiles."

**[SHOW: `src/dashboard.py` lines 185–199]**

> "When the analyst clicks **Run forensic investigation**, the dashboard POSTs the CSV to `POST /api/v1/investigate`."

**[SHOW: `api/main.py` lines 199–218]**

> "The API reads the CSV, validates it, and calls `supervisor.investigate(df)`. The same dataframe flows through all six LangGraph nodes via shared `InvestigationState`. If the API is offline, the dashboard runs the supervisor locally — same pipeline, same audit log."

---

## SECTION 5 — Special component: audit log (1:00)


| Cue           | File                                             |
| ------------- | ------------------------------------------------ |
| Trace example | `AGENT_DECISION_TRACES.md` lines 14–32           |
| Log builder   | `supervisor/langgraph_supervisor.py` lines 79–83 |
| Dashboard UI  | `src/dashboard.py` lines 534–538                 |


**[SHOW: `AGENT_DECISION_TRACES.md` lines 14–32]**

> "The component we want to highlight is the **audit log** — our answer to the black-box problem."

> "Every investigation returns an ordered list of human-readable steps. For example: Forensic Analyst started EDA, Statistician completed with mean authenticity seventy-two percent, NLP Investigator finished, Report Writer wrote the PDF path. This is not logging for developers — it is **B2B transparency** for compliance teams."

**[SHOW: `supervisor/langgraph_supervisor.py` lines 79–83]**

> "Each agent node calls `_log()`, which appends to `InvestigationState['audit_log']`. The API returns it in JSON. The dashboard renders it. Disk writes it to `investigation_summary.json`."

> "Most ML demos show a score. We show **how** the score was produced — plus PCA coordinates, behavioral flags, and held-out metrics in the PDF."

---

## SECTION 6 — Live demo (3:30)

**[DEMO: [http://localhost:8501]**](http://localhost:8501])


| Step | Time | Action                                  | Say                                                            |
| ---- | ---- | --------------------------------------- | -------------------------------------------------------------- |
| 1    | 0:30 | Sidebar → **Load sample dataset**       | "We load 2,400 profiles. In production, this is a client CSV." |
| 2    | 0:40 | **Run forensic investigation**          | "Triggers LangGraph via FastAPI — six agents, plots, PDF."     |
| 3    | 0:40 | Tab: **Leaderboard**                    | "Top 10 most / least authentic — triage list, not auto-ban."   |
| 4    | 0:40 | Tab: **PCA & Outliers**                 | "Visual outlier evidence in 2D PCA space."                     |
| 5    | 0:50 | Tab: **Agent Audit Log** ★              | **Highlight — every step is traceable.**                       |
| 6    | 0:30 | Tab: **Forensic Report** → Download PDF | "Audit-ready deliverable for compliance."                      |


### Step 1 — Load data (0:30)

> "Let me walk through the analyst workflow."

> *[Sidebar → **Load sample dataset**]*

> "We load two thousand four hundred profiles from our processed training cohort. In production, this would be a client-uploaded CSV."

### Step 2 — Run investigation (0:40)

> *[Click **Run forensic investigation**]*

> "This triggers the LangGraph supervisor through our API. Six agents run in sequence — EDA, modeling, behavioral, risk, NLP, report. This takes a moment because we generate plots and a PDF."

### Step 3 — Leaderboard (0:40)

> *[Tab: **Leaderboard**]*

> "Here are the top ten most and least authentic accounts. This is a **triage list** — analysts review flagged profiles, not auto-reject them."

### Step 4 — PCA & outliers (0:40)

> *[Tab: **PCA & Outliers**]*

> "Outliers appear in two-dimensional PCA space. You can see *where* an account sits relative to the cohort — visual evidence, not just a percentage."

### Step 5 — Audit log (0:50) ★ HIGHLIGHT

> *[Tab: **Agent Audit Log**]*

> "This is our differentiator. Every agent step is listed in order — which tool ran, how many profiles were scored, where the PDF was written. A compliance officer can trace the full investigation without reading Python."

### Step 6 — Forensic report (0:30)

> *[Tab: **Forensic Report** → **Download forensic PDF report**]*

> "The deliverable includes log-normal validation, held-out PR/ROC metrics, per-account evidence tables, and marketing recommendations. Markdown is also available."

> "That is the end-to-end workflow: upload, investigate, triage, audit, export."

---

## SECTION 7 — Results, future work, duration (0:30)


| Cue              | File                                    |
| ---------------- | --------------------------------------- |
| Results table    | `PROJECT_REPORT.md` §7, lines 191–208   |
| Honest eval code | `src/holdout_evaluation.py` lines 75–90 |
| Future work      | `PROJECT_REPORT.md` §12, lines 354–360  |
| Phase timeline   | `PROJECT_REPORT.md` §8.1, lines 227–238 |


### Results (0:10)

**[Slide: Results]**

> "On our six-hundred-profile holdout, Isolation Forest at contamination zero-point-zero-five gives **F1 zero-point-four-four**, precision zero-point-three-six, recall zero-point-five-six. ROC AUC is near zero-point-five."

**[SHOW: `src/holdout_evaluation.py` lines 75–90]**

> "We are honest about this: unsupervised outlier detection does not equal supervised classification. Metrics are computed **only** on `test_features.csv` — never on the upload batch. The value is transparent triage, not a legal fraud verdict."

### Future improvements (0:10)

**[Slide: Future work]**

> "Given more time, we would: connect a **live Instagram API**; add **semi-supervised tuning** from analyst feedback; expand **SHAP explainability** in reports; support **TikTok and YouTube**; and add **async job queues** and cloud storage for production scale."

### Project duration (0:10)

**[Slide: Phase timeline]**

> "The project took roughly **seven weeks** — Phase 1 data prep in late April, modeling in early May, agent architecture and dashboard in late May, tests and documentation in early June. Seven phases, twenty-five tests, GitHub Actions CI."

> "Thank you. We are happy to take questions."

---

## Q&A

### Quick one-liners


| Question                             | Answer                                                                           |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| Why unsupervised if you have labels? | Clients won't give labels; we validate honestly on holdout only.                 |
| Is 36% precision enough?             | Triage tool — flags candidates for human review, not auto-ban.                   |
| Need an LLM?                         | No. LangGraph runs deterministically; Grok/CrewAI is optional.                   |
| Production-ready?                    | Prototype with Docker, API, 25 tests, CI — needs live API + job queue for scale. |


### Extended answers (if asked)

**Q: Why not train a supervised classifier since you have labels?**

> "In production, B2B clients will not give us labeled fraud data. We deliberately built an unsupervised pipeline and used labels only to validate on a fixed holdout. That matches real deployment."

**Q: Can legitimate influencers be flagged as outliers?**

> "Yes — that is a known limitation of outlier detection. A niche influencer with unusual follower ratios might score low. That is why we position this as **triage for human review**, supported by per-account evidence in the PDF."

**Q: Do you need Grok or an LLM?**

> "No. The default LangGraph path is fully deterministic. CrewAI plus Grok is an optional advisory layer — toggle in the sidebar, requires `GROK_API_KEY`."

**Q: How is this different from a simple sklearn script?**

> "Three things: the **multi-agent orchestration** with audit trail, the **B2B dashboard and API**, and **forensic reports** with log-normal proof and held-out evaluation rigor. It is a complete analyst workflow, not a notebook."

**Q: What would you demo if the API is down?**

> "Disable **Use API endpoint** in the sidebar. The dashboard runs `LangGraphSupervisor` in-process — same agents, same audit log, with a visible warning banner."

