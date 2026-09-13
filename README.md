# Taf's Pilot

### Autonomous AI Video Production Agent

An agentic video-production system that turns a creative brief into a verified short-form video through **planning, human approval, media production, automated QC, and self-correction**.

Built with **Amazon Strands Agents SDK, Amazon Bedrock, Amazon Polly, Amazon Titan, Python, and FFmpeg**.

> Built for the **Amazon Agents for Humans Hackathon** · Professional Agents Track

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Strands: Agents SDK](https://img.shields.io/badge/Amazon_Strands-Agents_SDK-orange.svg)](https://github.com/awslabs/strands-agents)
[![Tests: 49 Passing](https://img.shields.io/badge/Tests-49%20Passing-success.svg)](tests/)

---

## 🎬 Demo

**Watch Taf's Pilot move from creative direction to production, QC failure, autonomous revision, and verified delivery:**

▶️ [Watch the demo on YouTube](https://youtu.be/CEaaKyLaHJM)

The repository also includes a verified showcase artifact with the final video, pre-revision defect, QC report, audit history, and revision decision.

**Showcase:** [`artifacts/74ed7661/`](artifacts/74ed7661/)

---

## What Taf's Pilot Does

Professional short-form video production combines creative strategy with a large amount of mechanical execution: planning hooks, pacing narration, generating visuals, composing scenes, styling subtitles, enforcing output specifications, and checking the final render.

Taf's Pilot treats that workflow as an **agentic production system** rather than a collection of disconnected AI tools.

It can:

- Turn an unstructured creative brief into a structured production plan.
- Generate differentiated hook strategies and pause for **human approval** before expensive media generation.
- Coordinate narration, visuals, subtitles, scene assembly, and final rendering.
- Inspect the rendered video automatically against technical QC criteria.
- Diagnose failed QC checks and create a targeted revision request.
- Re-render affected content and re-run QC until the deliverable passes, within a bounded revision budget.
- Deliver the final asset together with telemetry, audit history, and revision reasoning.

---

## The Core Idea: Self-Healing Production

The most important part of Taf's Pilot is not simply generating a video. It is the **verification-and-correction loop**:

```text
GENERATE
   ↓
INSPECT
   ↓
FAIL ───────→ DIAGNOSE
                 ↓
              REVISE
                 ↓
             RE-INSPECT
                 ↓
                PASS
```

The full lifecycle is:

```text
Understand → Plan → Ask → Produce → Inspect → Correct → Deliver
```

1. **Understand** — Analyze topic, audience, goal, tone, and platform constraints.
2. **Plan** — Build a structured production plan and develop multiple hook directions.
3. **Ask** — Stop at a human-in-the-loop approval gate before media synthesis.
4. **Produce** — Generate narration and visuals, calculate scene timing, compose video, and burn safe-zone subtitles.
5. **Inspect** — Run automated `ffprobe`-based QC for dimensions, streams, duration, subtitles, and frame integrity.
6. **Correct** — If QC fails, formulate a structured `RevisionRequest`, revise affected content, and re-render within `MAX_REVISIONS = 2`.
7. **Deliver** — Return a verified final video with production telemetry and audit history.

---

## Why It Is Different

### 🤖 Agent orchestration, not a single generation call

Taf's Pilot uses the **Amazon Strands Agents SDK** to coordinate a multi-stage production workflow through typed tools and structured state.

### 👤 Human control at the right moment

The agent does not blindly generate an entire production. It pauses at `AWAITING_HOOK_APPROVAL`, presents three differentiated hook directions, and waits for the creator's decision before continuing.

### 🔍 Verification is part of the workflow

The final render is inspected programmatically rather than assumed to be correct. QC checks include:

- Exact 9:16 output at **1080×1920**
- H.264 video and AAC audio stream health
- Duration within **±1.5 seconds** of the target
- Subtitle presence and rendering
- Empty/black frame detection

### 🔧 Autonomous self-correction

A failed QC result moves the pipeline into `REVISION_REQUIRED`. The agent evaluates the failure, creates a targeted revision request, regenerates affected assets, and re-runs verification.

### 🧾 Auditable execution

The system keeps QC reports, audit history, revision decisions, and production telemetry so the final output is explainable rather than a black-box export.

---

## Architecture

```text
                    ┌──────────────────────┐
                    │   Creative Brief     │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Strands Agent       │
                    │  Understand / Plan   │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ Human Approval Gate  │
                    └──────────┬───────────┘
                               ↓
              ┌────────────────┴────────────────┐
              ↓                                 ↓
       Voiceover / Audio                 Visual Generation
       Amazon Polly / local              Amazon Titan / FFmpeg
              └────────────────┬────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │   FFmpeg Assembly    │
                    │  Video + Subtitles   │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   Automated QC       │
                    │      ffprobe         │
                    └──────────┬───────────┘
                               ↓
                         PASS / FAIL
                          ↙         ↘
                       PASS         FAIL
                        ↓             ↓
                    Deliver      RevisionRequest
                                      ↓
                                   Re-render
                                      ↓
                                   Re-check
```

For the complete architecture, state model, tool contracts, lifecycle details, and Mermaid diagrams, see [`docs/architecture.md`](docs/architecture.md).

---

## Engineering Highlights

| Area | Implementation |
| --- | --- |
| Agent orchestration | Amazon Strands Agents SDK (`strands.Agent`) |
| Foundation models | Amazon Bedrock · Claude 3.5 Sonnet · Amazon Nova Pro/Lite |
| Structured state | Pydantic v2 domain schemas and `ProjectState` |
| Tool calling | Typed `@tool` production and planning interfaces |
| Human-in-the-loop | Explicit hook approval state and production gate |
| Voice | Amazon Polly with deterministic local fallback |
| Visuals | Amazon Titan Image Generator with FFmpeg motion graphics fallback |
| Video assembly | FFmpeg · H.264 · AAC · 1080×1920 · 30 fps |
| Subtitle pipeline | Libass styling with mobile safe-zone positioning |
| Automated QC | `ffprobe`-based media inspection |
| Self-healing | Targeted revision loop with bounded revision budget |
| Auditability | QC reports · audit history · revision decisions · telemetry |
| Web interface | Starlette/Uvicorn production console |

---

## Key Tools

The agent exposes a typed production toolset including:

- `create_production_plan`
- `request_hook_approval`
- `finalize_scene_plan`
- `synthesize_voiceover`
- `resolve_visuals`
- `assemble_video`
- `audit_video`
- `revise_video`
- `simulate_qc_defect` — controlled demo/test utility for exercising the self-correction path

---

## Web Production Console

Taf's Pilot includes a dark three-column production studio for interactive execution and demonstrations.

- **Creative Direction** — brief inputs, platform selection, and production state.
- **Agent Activity & Live Studio** — event stream, production timeline, video preview, telemetry, and hook approval.
- **Artifact & Audit Inspector** — QC status, revision history, and detailed inspection telemetry.

The console also includes a **Demo Fast-Forward** control that intentionally introduces a controlled QC defect so the complete detection → revision → verification flow can be demonstrated quickly. This is a demonstration utility, not a claim that the production pipeline randomly generates defects.

---

## AWS Integration & Honest Fallbacks

Taf's Pilot is architected around AWS services through the official Boto3 SDK:

- **Amazon Bedrock** — foundation models for brief understanding, production strategy, and revision decisions.
- **Amazon Polly** — neural text-to-speech for narration.
- **Amazon Titan Image Generator** — AI-generated visual scene assets.
- **AWS STS** — identity and credential diagnostics.

When AWS credentials are available, the corresponding AWS services are invoked natively. When AWS access is unavailable or account verification is pending, Taf's Pilot does **not** fabricate provider success. It reports the diagnostic condition and routes supported synthesis steps through deterministic local fallbacks.

Local fallback paths include:

- `SAPI.SpVoice` / formant synthesis for spoken narration.
- FFmpeg-generated kinetic motion graphics for visuals.
- The same assembly and QC stages across environments.

Run the diagnostic tool with:

```bash
python -c "from tafs_pilot.aws_diagnostics import run_aws_diagnostics; import json; print(json.dumps(run_aws_diagnostics(), indent=2))"
```

---

## Verified Showcase

The repository contains a completed showcase production for:

**Topic:** *Why Senior Engineers Write Less Code Than Juniors*

**Core hook:** *The best senior engineers don't write more code. They delete it.*

Available evidence includes:

- [`final.mp4`](artifacts/74ed7661/final.mp4) — verified final deliverable
- [`final_defect.mp4`](artifacts/74ed7661/final_defect.mp4) — pre-revision defect reference
- [`qc.json`](artifacts/74ed7661/qc.json) — automated QC report
- [`audit_history.json`](artifacts/74ed7661/audit_history.json) — inspection history
- [`revision_decision.json`](artifacts/74ed7661/revision_decision.json) — autonomous revision rationale

The showcase is intentionally kept under `artifacts/` as a reproducible portfolio/demo reference rather than mixing generated media with development scratch files.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **FFmpeg** and **ffprobe** available on `PATH`
- *(Optional)* AWS credentials with access to Amazon Bedrock and Amazon Polly

### Install

```bash
git clone https://github.com/tafeemamair/Tafs-Pilot.git
cd Tafs-Pilot

python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r requirements.txt
```

### Configure AWS (Optional)

Taf's Pilot follows the standard AWS credential provider chain:

```bash
# AWS CLI
aws configure

# IAM Identity Center / SSO
aws sso login

# Or use a local .env based on .env.example
```

### Run Tests

```bash
pytest tests/ -v
```

The current repository test suite contains **49 unit, integration, and media-pipeline tests**.

---

## Run the Production Console

```bash
python run_console.py
```

Or:

```bash
python -m tafs_pilot --web --port 8000 --open
```

Then open `http://127.0.0.1:8000/`.

### CLI

```bash
python -m tafs_pilot \
  --topic "Why Senior Engineers Write Less Code Than Juniors" \
  --audience "Software engineers and tech leads" \
  --goal "Promote architectural simplicity and problem prevention" \
  --tone "Direct, authoritative, punchy" \
  --duration 21 \
  --platform "YouTube Shorts"
```

---

## Project Structure

```text
Tafs-Pilot/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── run_console.py
├── docs/
│   ├── architecture.md
│   └── demo-script.md
├── artifacts/
│   └── 74ed7661/
│       ├── final.mp4
│       ├── final_defect.mp4
│       ├── qc.json
│       ├── audit_history.json
│       ├── revision_decision.json
│       ├── audio/
│       ├── visuals/
│       ├── captions/
│       └── renders/
├── src/
│   └── tafs_pilot/
│       ├── agent.py
│       ├── config.py
│       ├── aws_diagnostics.py
│       ├── models.py
│       ├── tools/
│       │   ├── planning.py
│       │   └── production.py
│       ├── media/
│       │   ├── assembly.py
│       │   ├── audio.py
│       │   ├── qc.py
│       │   └── visuals.py
│       └── web/
│           ├── server.py
│           └── static/
└── tests/
    ├── test_day3a.py
    ├── test_media_pipeline.py
    ├── test_milestone2.py
    └── test_planning.py
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture, lifecycle, state model, tools, QC, and system design.
- [`docs/demo-script.md`](docs/demo-script.md) — hackathon presentation flow.
- [`artifacts/74ed7661/`](artifacts/74ed7661/) — verified showcase evidence.

---

## License

Apache 2.0. See [`LICENSE`](LICENSE).
