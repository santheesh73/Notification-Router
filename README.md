# AI-Powered WhatsApp Message Notification Router

Production-grade, modular, scalable AI-powered WhatsApp Message Notification Router designed to predict notification routing actions (`notify`, `digest`, `mute`) for incoming text, image, and voice messages.

---

## 1. System Architecture

```text
                                  INCOMING MESSAGE
                                         │
                                         ▼
                            Phase 3: Feature Engineering
                                   (FeatureVector)
                                         │
                                         ▼
                             Phase 4: Rule Engine (15 Rules)
                                         │
                        ┌────────────────┴────────────────┐
                 Resolved (80%)                    Unresolved (20%)
                        │                                 │
                        │                       Phase 5: Evidence Retrieval
                        │                       Phase 6: Multimodal Understanding
                        │                       Phase 7: AI Decision Orchestrator
                        │                                 │
                        └────────────────┬────────────────┘
                                         │
                                         ▼
                        Phase 8: Decision Fusion Engine
                          (Confidence Calibration [0..1])
                                         │
                                         ▼
                        Phase 9: Execution Pipeline & Output
                                  (output.csv)
                                         │
                                         ▼
                        Phase 10: Evaluation & Submission
                            (code.zip, reports, verifier)
                                         │
                                         ▼
                        Phase 11: Performance Optimization
                         (quality_audit, leaderboard_report)
```

---

## 2. Project Directory Structure

```text
notification-router/
├── config/                  # Configuration settings & environment variables
│   └── settings.py
├── dataset/                 # Evaluation dataset & sample messages
├── src/
│   ├── loaders/             # Phase 1: Data Repository & CSV Loaders
│   ├── models/              # Phase 2: Context Profile Data Models
│   ├── builders/            # Phase 2: User/Group/Business Profile Builders
│   ├── features/            # Phase 3: Feature Pipeline & FeatureVector Extraction
│   ├── rules/               # Phase 4: Deterministic Rule Engine (15 Rules)
│   ├── retrieval/           # Phase 5: Historical Evidence Retrieval Engine
│   ├── media/               # Phase 6: Multimodal Image & Voice Understanding Layer
│   ├── llm/                 # Phase 7: AI Decision Orchestrator & LLM Providers
│   ├── confidence/          # Phase 8: Decision Fusion & Confidence Calibration Engine
│   ├── output/              # Phase 9: Incremental CSV Output Writer & Schema Validator
│   ├── pipeline/            # Phase 9: End-to-End Execution Pipeline & Checkpoints
│   ├── evaluation/          # Phase 10: Performance Benchmarking & Profiler
│   ├── optimization/        # Phase 11: Performance Optimization & Leaderboard Audit Engine
│   └── utils/               # Loguru Singleton Logger & Helper Utilities
├── submission/              # Phase 10: Submission Packaging & Deliverables Verifier
├── tests/                   # Unit test suite (86+ Pytest unit tests)
├── output/                  # Final output CSV directory (output.csv)
├── reports/                 # Evaluation, Benchmark, Optimization, and Leaderboard Reports
├── chat_transcript.md       # Engineering Development Log
├── main.py                  # Main Entry Point
└── README.md                # Project Documentation
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.12+ (or Python 3.14)
- Virtual Environment (recommended)

### Installation
```bash
# 1. Clone repository
git clone <repository_url>
cd notification-router

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 4. Execution

To run the complete end-to-end pipeline, evaluate performance, optimize execution, generate all reports, package `code.zip`, and verify submission deliverables with a single command:

```bash
python main.py
```

### Generated Deliverable Files:
- `output/output.csv`: Complete prediction output CSV matching `dataset/output.csv`.
- `code.zip`: Submissible codebase zip package.
- `chat_transcript.md`: Complete engineering log.
- `reports/execution_report.json`: Execution throughput & metrics.
- `reports/benchmark_report.json`: Performance benchmark statistics.
- `reports/quality_report.json`: Data quality & confidence distribution report.
- `reports/optimization_report.json`: Phase 11 optimization metrics.
- `reports/performance_report.json`: Memory & CPU profiling report.
- `reports/quality_audit.md`: Deep quality audit report.
- `reports/submission_checklist.md`: Deliverables checklist.
- `reports/leaderboard_report.md`: Leaderboard competitive evaluation report.
- `reports/summary.md`: Executive summary markdown report.

---

## 5. Testing & Verification

Run the comprehensive unit test suite:

```bash
python -m pytest -p no:langsmith tests/ -v
```

All 86+ unit tests run in under 3 seconds with 100% pass rate.
