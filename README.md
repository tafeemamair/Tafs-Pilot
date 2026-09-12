# Taf's Pilot: Autonomous Video Production Agent

> Built for the **Amazon Agents for Humans Hackathon** | **Track: Professional Agents**  
> Powered by the **Amazon Strands Agents SDK (`strands-agents`)**, **Amazon Bedrock**, **Amazon Polly**, and **FFmpeg**.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Strands: Agents SDK](https://img.shields.io/badge/Amazon_Strands-Agents_SDK-orange.svg)](https://github.com/awslabs/strands-agents)
[![Tests: 49 Passing](https://img.shields.io/badge/Tests-49%20Passing-success.svg)](tests/)

---

## Quick Links

- [Architecture Guide & Technical Deep Dive](docs/architecture.md)
- [Hackathon Demo Presentation Script (~2.5–3 min)](docs/demo-script.md)
- [Showcase Deliverable Artifacts](artifacts/74ed7661/)
- [Apache 2.0 License](LICENSE)

---

## Executive Summary & Problem Statement

Professional creators, educators, and enterprise marketing teams face an exhausting mechanical bottleneck: while conceptualizing ideas is fast, executing broadcast-grade short-form video deliverables (hook research, pacing calculations, voiceover generation, visual B-roll composition, subtitle styling, aspect-ratio enforcement, and quality assurance) consumes over 80% of their creative bandwidth.

Existing generative AI tools provide disjointed point solutions—an isolated script generator here, a standalone text-to-speech engine there, or an unconstrained text-to-video tool producing unusable artifacts. When an export has clipped subtitles, duration drift, or codec regressions, the creator is forced back into a manual editing timeline.

**Taf's Pilot** solves this by operating as an **Autonomous Executive Video Producer and Creative Director**. Built on the **Amazon Strands Agents SDK**, Taf's Pilot takes full end-to-end responsibility for the production job:
- Translates unstructured creative briefs into strategic, retention-optimized plans.
- Pauses at critical strategic junctures for **Human-in-the-Loop sign-off** on hook direction.
- Coordinates multi-track media synthesis across audio, visuals, and burn-in subtitle compositing.
- Autonomously audits its own rendered deliverables via deep **Quality Control (QC)** inspection.
- When defects are detected, **self-heals and revises the video automatically** without demanding creator troubleshooting.

---

## Core Agent Philosophy

```text
Understand  ──>  Plan  ──>  Ask  ──>  Produce  ──>  Inspect  ──>  Correct  ──>  Deliver
```

1. **Understand**: Analyze the creator's brief (topic, target persona, business goal, tone, platform constraints).
2. **Plan**: Reason through narrative retention strategies and diverge into 3 distinct psychological hook angles.
3. **Ask (Human-in-the-Loop)**: Pause execution to present the creator with differentiated hook proposals for explicit approval.
4. **Produce**: Coordinate multi-track generation—synthesizing voiceovers, generating visual assets, calculating exact spoken durations, and burning safe-zone subtitles into vertical 1080×1920 MP4s.
5. **Inspect (Autonomous QC)**: Run automated machine inspection with `ffprobe` to verify video dimensions, audio streams, subtitle presence, duration tolerance, and detect empty/black frames.
6. **Correct (Self-Healing Loop)**: If quality criteria fail, the agent diagnoses the defect, formulates a targeted `RevisionRequest`, re-renders only affected assets within a strict revision budget, and re-verifies.
7. **Deliver**: Present the verified final deliverable alongside complete telemetry, audit history, and publication-ready metadata.

---

## Key Capabilities

### 1. Autonomous Agent Orchestration (`strands-agents`)
- Powered by the **Amazon Strands Agents SDK** (`strands.Agent`) with native **Amazon Bedrock** foundation models (`Claude 3.5 Sonnet`, `Amazon Nova Pro`, `Amazon Nova Lite`).
- Typed `@tool` interfaces with strict **Pydantic v2** validation contracts:
  - `create_production_plan`: Formulates structured video blueprints.
  - `request_hook_approval`: Presents strategic hook proposals at the human-in-the-loop gate.
  - `finalize_scene_plan`: Registers scene-by-scene visual and narration directives.
  - `synthesize_voiceover`: Coordinates spoken voiceover audio and captures exact spoken durations.
  - `resolve_visuals`: Prepares 1080×1920 vertical visual assets matching creative descriptions.
  - `assemble_video`: Concatenates scenes with burned-in subtitles into an MP4 deliverable.
  - `audit_video`: Executes deep automated QC inspection against deliverable specifications.
  - `revise_video`: Executes targeted surgical scene regenerations when defects are found.
  - `simulate_qc_defect`: Test utility to simulate real-world QC defects for automated self-correction demonstrations.

### 2. Human-in-the-Loop Creative Approval Gate
- The agent does not blindly burn expensive media compute on unaligned creative direction.
- In Phase 1 ("Ask"), the agent pauses the pipeline in the `AWAITING_HOOK_APPROVAL` state, generating 3 differentiated hook angles:
  1. *Counter-intuitive curiosity / myth-busting*
  2. *High-urgency problem agitation*
  3. *Bold contrarian declaration*
- The creator selects or refines their preferred hook before media synthesis begins.

### 3. Multi-Track Media Production Pipeline
- **Spoken Voiceover Engine (`audio.py`)**:
  - Primary: **Amazon Polly** neural voiceover (`Danielle` / `Matthew`) with standard speech cadence.
  - Graceful Fallback: Natural offline spoken speech synthesis via local speech engine (`SAPI.SpVoice`) with pitch/formant wave fallback. Spoken word cadence directly drives exact scene pacing.
- **Visual Storytelling (`visuals.py`)**:
  - Primary: **Amazon Titan Image Generator** on Bedrock for AI-generated visual scene assets.
  - Motion Graphics: High-contrast developer-oriented kinetic typography and terminal animations using FFmpeg (window controls, syntax-highlighted git diffs, comparison cards, and command execution prompts).
- **Burned Subtitle Engine (`assembly.py`)**:
  - Natural phrasing beat splitting: Parses narrations into synchronized sentence beats rather than monolithic text blocks.
  - Mobile safe-zone compliance: Uses Libass styling (`FontSize=16`, `Bold=1`, `MarginV=65`, `Alignment=2`) positioned in the lower third with high-contrast outlines to guarantee 0% caption clipping on TikTok/Reels/Shorts.
- **FFmpeg Compositing Engine**:
  - Assembles broadcast-grade 1080×1920 vertical H.264 video with AAC audio at 30 fps.

### 4. Autonomous QC & Self-Healing Loop (`qc.py`, `agent.py`)
- Post-assembly, the agent automatically executes `audit_video` to inspect:
  - Aspect ratio: Exactly 9:16 vertical (1080×1920)
  - Stream health: Valid H.264 video stream + AAC audio stream present
  - Duration tolerance: Runtime matches target duration within ±1.5s tolerance
  - Subtitle visibility: Subtitle track verified as present and rendered
  - Frame integrity: Rejects black or empty frames
- If QC reports `FAIL`:
  - Pipeline transitions to `REVISION_REQUIRED`.
  - The agent evaluates the root cause and formulates a structured `RevisionRequest` specifying targeted scene adjustments.
  - The agent invokes `revise_video`, re-synthesizing only the flawed assets and re-assembling the deliverable under a strict revision budget (`MAX_REVISIONS = 2`).
  - Re-audits the updated deliverable until achieving verified `PASS` status.

### 5. Web Production Console (`tafs_pilot.web`)
- Dark, professional 3-column studio interface:
  - **Column 1 — Creative Direction**: Creator brief inputs, platform selection, and production lock indicators.
  - **Column 2 — Agent Activity & Live Studio**: Real-time agent event stream, step-by-step timeline, live video player with scanning inspection overlay, telemetry bar (resolution, FPS, duration, file size, codec), and interactive hook approval cards.
  - **Column 3 — Artifact & Audit Inspector**: Side-by-side QC report badges, revision history trail, and an interactive **Inspect Report Modal** showing the full JSON telemetry and audit trail.
- **One-Click Demo Fast-Forward**: A specialized trigger that demonstrates the complete defect-detection and self-correction loop in seconds for hackathon judging.

---

## Project Structure

```text
Tafs-Pilot/
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # Apache 2.0 Open Source License
├── README.md                        # Project documentation & overview
├── requirements.txt                 # Python dependencies
├── run_console.py                   # Convenience launcher for Web Production Console
├── docs/
│   ├── architecture.md              # Technical architecture & Mermaid diagrams
│   └── demo-script.md               # 2.5–3 minute presentation demo script
├── artifacts/
│   └── 74ed7661/                    # Verified showcase deliverable directory
│       ├── final.mp4                # 1080x1920 verified final deliverable (PASS)
│       ├── final_defect.mp4         # Pre-revision defect reference copy (FAIL)
│       ├── qc.json                  # Automated QC report metadata
│       ├── audit_history.json       # Immutable QC inspection audit history
│       ├── revision_decision.json   # Agent autonomous revision rationale
│       ├── audio/                   # Synthesized per-scene spoken audio stems
│       ├── visuals/                 # Per-scene vertical visual assets
│       ├── captions/                # Burned per-scene SRT subtitle files
│       └── renders/                 # Composite per-scene intermediate clips
├── src/
│   └── tafs_pilot/
│       ├── __init__.py              # Package exports
│       ├── __main__.py              # Full CLI entry point with end-to-end workflow
│       ├── agent.py                 # Strands producer agent & QC revision loop
│       ├── config.py                # Environment & AWS region configuration
│       ├── aws_diagnostics.py       # Safe, read-only AWS credential diagnostics
│       ├── models.py                # Pydantic v2 domain schemas & ProjectState
│       ├── tools/
│       │   ├── __init__.py          # Tool registry exports
│       │   ├── planning.py          # create_production_plan, request_hook_approval
│       │   └── production.py        # synthesize_voiceover, resolve_visuals, assemble_video, audit_video, revise_video
│       ├── media/
│       │   ├── __init__.py          # Media engines export
│       │   ├── assembly.py          # Video concatenation & burned subtitle compositing
│       │   ├── audio.py             # Amazon Polly & local spoken speech synthesis
│       │   ├── qc.py                # Automated ffprobe QC video inspection engine
│       │   └── visuals.py           # Amazon Titan & kinetic procedural motion graphics
│       └── web/
│           ├── __init__.py          # Web package export
│           ├── __main__.py          # Web server CLI runner
│           ├── server.py            # Starlette/Uvicorn ASGI API & static server
│           └── static/              # Dark professional UI dashboard (HTML/CSS/JS)
└── tests/
    ├── __init__.py
    ├── test_day3a.py                # AWS diagnostics & autonomous QC revision tests
    ├── test_media_pipeline.py         # Voiceover, visuals, subtitles & assembly tests
    ├── test_milestone2.py           # Production tools & ProjectState lifecycle tests
    └── test_planning.py             # Pydantic schemas & planning tool tests
```

---

## AWS Integration & Honest Provider Transparency

Taf's Pilot is natively architected for AWS services via the official Boto3 SDK:
- **Amazon Bedrock**: High-reasoning foundation models (`anthropic.claude-3-5-sonnet-20241022-v2:0`, `amazon.nova-pro-v1:0`, `amazon.nova-lite-v1:0`) for brief understanding, retention strategy, and revision decisions.
- **Amazon Polly**: Neural text-to-speech synthesis engine for broadcast-quality narration.
- **Amazon Titan Image Generator**: Photorealistic 9:16 portrait visual generation on Bedrock.
- **AWS STS**: Identity verification and credential chain inspection.

### Honest Fallback Handling
In adherence to hackathon submission integrity guidelines:
- If AWS credentials are configured and active, Taf's Pilot invokes Amazon Bedrock, Amazon Polly, and Amazon Titan natively.
- If AWS credentials are not present or account verification is pending in the running environment, **Taf's Pilot never fabricates AWS success**. Instead, it logs the exact diagnostic error, clearly discloses the fallback mode, and automatically routes synthesis to its deterministic local engines:
  - Speech synthesis routes to local spoken voice narration (`SAPI.SpVoice`) with formant synthesis fallback.
  - Visuals route to developer-oriented kinetic motion graphics built directly via FFmpeg.
  - Assembly, burned captions, and autonomous QC inspection execute identically across all environments.

Run the built-in diagnostic tool to inspect your current AWS environment:
```bash
python -c "from tafs_pilot.aws_diagnostics import run_aws_diagnostics; import json; print(json.dumps(run_aws_diagnostics(), indent=2))"
```

---

## Quick Start

### 1. Prerequisites
- **Python 3.11** or newer
- **FFmpeg** and **ffprobe** installed and accessible on your system `PATH` (used for video compositing and automated QC inspection)
- *(Optional)* AWS credentials configured with access to Amazon Bedrock and Amazon Polly

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/aisand/Tafs-Pilot.git
cd Tafs-Pilot

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.\.venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure AWS Credentials (Optional)
Taf's Pilot follows the standard AWS credential provider chain:
```bash
# Option A: AWS CLI
aws configure

# Option B: IAM Identity Center (SSO)
aws sso login

# Option C: Environment variables (.env)
cp .env.example .env
# Edit .env with AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
```

### 4. Run the Test Suite
Run all 49 unit, integration, and media pipeline tests:
```bash
pytest tests/ -v
```

---

## Running Taf's Pilot

### Option A: Web Production Console (Recommended for Demo)
Launch the interactive 3-column production studio:
```bash
python run_console.py
# Or via package CLI:
python -m tafs_pilot --web --port 8000 --open
```
Open your browser at `http://127.0.0.1:8000/`.

**Demo Highlights in the Console:**
1. Review the creator brief: *"Why Senior Engineers Write Less Code Than Juniors"*.
2. Click **Start Production** to watch the agent analyze the brief and propose 3 distinct hook angles.
3. Select an approved hook to advance the pipeline through scene planning, voiceover synthesis, and assembly.
4. Or click **Demo Fast-Forward: Jump to QC Defect** to trigger the killer demo moment: watch the agent inspect a duration/aspect defect, report `FAIL`, autonomously formulate a revision decision, re-render, and deliver a verified `PASS` video with zero human intervention.

### Option B: Command-Line Interface (CLI)
Execute the complete autonomous pipeline directly in your terminal:
```bash
# Run verified showcase brief
python -m tafs_pilot

# Or pass custom creative brief parameters
python -m tafs_pilot \
  --topic "Why Senior Engineers Write Less Code Than Juniors" \
  --audience "Software engineers and tech leads" \
  --goal "Promote architectural simplicity and problem prevention" \
  --tone "Direct, authoritative, punchy" \
  --duration 21 \
  --platform "YouTube Shorts"
```

---

## Verified Showcase Deliverable

The repository includes a fully rendered, verified showcase deliverable created through the autonomous production pipeline:

* **Artifact Directory**: [`artifacts/74ed7661/`](artifacts/74ed7661/)
* **Topic**: *"Why Senior Engineers Write Less Code Than Juniors"*
* **Core Hook**: *"The best senior engineers don't write more code. They delete it."*
* **Final Video**: [`artifacts/74ed7661/final.mp4`](artifacts/74ed7661/final.mp4)
* **Pre-Revision Defect Video**: [`artifacts/74ed7661/final_defect.mp4`](artifacts/74ed7661/final_defect.mp4)
* **Automated QC Report**: [`artifacts/74ed7661/qc.json`](artifacts/74ed7661/qc.json) (`status: PASS`, 0 defects)
* **Audit History**: [`artifacts/74ed7661/audit_history.json`](artifacts/74ed7661/audit_history.json)
* **Revision Decision**: [`artifacts/74ed7661/revision_decision.json`](artifacts/74ed7661/revision_decision.json)

### QC Verification Telemetry
```json
{
  "status": "PASS",
  "duration": 20.69,
  "width": 1080,
  "height": 1920,
  "aspect_ratio": "9:16",
  "video_codec": "h264",
  "audio_codec": "aac",
  "subtitles_present": true,
  "caption_clipping": "none",
  "issues": []
}
```

---

## Verification & Test Coverage

The test suite validates every layer of the autonomous architecture:
- `tests/test_planning.py`: Schema validation, domain constraints, Pydantic field validators, hook recommendation integrity.
- `tests/test_milestone2.py`: Strands tool execution, `ProjectState` lifecycle transitions, state serialization, and recovery.
- `tests/test_media_pipeline.py`: Voiceover duration propagation, SRT timestamp calculation, line wrapping, procedural visual generation, and end-to-end assembly.
- `tests/test_day3a.py`: AWS diagnostic inspection, provider metadata recording, simulated QC failure transitions, agent revision execution, revision budget enforcement (`MAX_REVISIONS = 2`), and artifact integrity.

```bash
$ pytest tests/ -v
======================= 49 passed in 248.44s (0:04:08) ========================
```

---

## License

This project is licensed under the **Apache 2.0 License**. See the [LICENSE](LICENSE) file for complete details.
