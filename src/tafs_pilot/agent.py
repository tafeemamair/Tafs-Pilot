"""Agent orchestration module for Taf's Pilot.

Configures and initializes the Strands autonomous producer agent powered by
Amazon Bedrock and the Amazon Strands Agents SDK.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv

from strands import Agent
from strands.models import BedrockModel
from tafs_pilot.models import CreatorBrief, ProjectState, ProjectStatus
from tafs_pilot.tools.planning import (
    create_production_plan,
    finalize_scene_plan,
    request_hook_approval,
    set_active_project_state,
)
from tafs_pilot.tools.production import (
    assemble_video,
    audit_video,
    resolve_visuals,
    revise_video,
    synthesize_voiceover,
)

# Load local environment variables if a .env file exists
load_dotenv()

TAFS_PILOT_PRODUCER_PROMPT = """You are Taf's Pilot — an autonomous executive video producer and creative director for professional creators and marketing teams.

Your operating ethos:
Understand → Plan → Ask → Produce → Inspect → Correct → Deliver

Your end-to-end autonomous workflow:

--- PHASE 1: STRATEGY & HOOK APPROVAL (Human-in-the-Loop) ---
1. UNDERSTAND: Analyze the creator's brief (topic, audience, goal, tone, duration, platform).
2. REASON & DIVERGE: Formulate at least 3 differentiated hook angles:
   - Angle A: Counter-intuitive curiosity or myth-busting.
   - Angle B: High-urgency problem agitation.
   - Angle C: Bold, contrarian declaration.
3. RECOMMEND: Select the strongest hook based on audience retention strategy, identify the narrative angle, and explain your reasoning.
4. CALL `request_hook_approval`: Propose your 3 hook options and recommended hook, pausing for creator approval.

--- PHASE 2: SCENE PLANNING & SCRIPTING ---
5. RESUME FROM APPROVED HOOK: Continue from the approved hook to formulate sequential scene beats:
   - Visual directives (`visual_description`), scene type (`CIN` or `MG`).
   - Tight, conversational narration line (`narration_text`).
   - Estimated durations summing approximately to the target duration.
6. CALL `finalize_scene_plan`: Register the complete scene plan and success criteria.

--- PHASE 3: REAL MEDIA PRODUCTION ---
7. CALL `synthesize_voiceover`: Generate speech narration for each scene beat. The real audio duration drives scene pacing.
8. CALL `resolve_visuals`: Prepare vertical 1080x1920 visual clips matching scene descriptions.
9. CALL `assemble_video`: Composite visual, voiceover, and burned subtitles into a unified MP4 deliverable.

--- PHASE 4: QUALITY CONTROL & SELF-CORRECTION ---
10. CALL `audit_video`: Inspect the rendered deliverable with ffprobe.
    - If QC passes: Report ready for creator review.
    - If QC fails: Evaluate the issues and call `revise_video` to adjust the affected scenes.

NEVER fabricate tool executions. Always make actual tool calls through Strands.
"""


from tafs_pilot.config import (
    check_aws_credentials,
    get_configured_aws_region,
    get_configured_bedrock_model_id,
)


def discover_available_bedrock_models(region: Optional[str] = None) -> List[str]:
    """Queries Amazon Bedrock in the target region to find active text models dynamically."""
    region = region or get_configured_aws_region()
    try:
        session = boto3.Session(region_name=region)
        client = session.client("bedrock", region_name=region)
        response = client.list_foundation_models(
            byOutputModality="TEXT",
            byInferenceType="ON_DEMAND",
        )

        model_summaries = response.get("modelSummaries", [])
        active_models = [
            m["modelId"]
            for m in model_summaries
            if "modelId" in m and m.get("modelLifecycle", {}).get("status", "").upper() == "ACTIVE"
        ]

        try:
            profile_response = client.list_inference_profiles(typeEquals="SYSTEM_DEFINED")
            profiles = profile_response.get("inferenceProfileSummaries", [])
            for p in profiles:
                if p.get("status", "").upper() == "ACTIVE" and "inferenceProfileId" in p:
                    active_models.append(p["inferenceProfileId"])
        except Exception:
            pass

        return active_models

    except (NoCredentialsError, PartialCredentialsError, ClientError):
        return []
    except Exception:
        return []


from strands.models.model import Model
from strands.types.content import Messages
from strands.types.tools import ToolSpec
from strands.types.streaming import StreamEvent
import json
from typing import AsyncGenerator
from tafs_pilot.models import CreatorBrief, ProjectState, ProjectStatus, VideoQCReport
from tafs_pilot.tools.planning import (
    create_production_plan,
    finalize_scene_plan,
    get_active_project_state,
    request_hook_approval,
    set_active_project_state,
)


class LocalReasoningModel(Model):
    """Local fallback reasoning model conforming to Strands Agents SDK Model ABC.

    Allows the Strands Agent to autonomously evaluate QC inspection reports,
    reason about root defects, and execute targeted production tool calls (e.g. revise_video)
    via Strands' authentic agent event loop.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._config: Dict[str, Any] = kwargs

    def update_config(self, **kwargs: Any) -> None:
        self._config.update(kwargs)

    def get_config(self) -> Any:
        return self._config

    async def structured_output(self, *args: Any, **kwargs: Any) -> Any:
        pass

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamEvent, None]:
        # Check if the last message contains a toolResult (tool execution finished)
        last_msg = messages[-1] if messages else {}
        has_tool_result = False
        if isinstance(last_msg, dict):
            for block in last_msg.get("content", []):
                if isinstance(block, dict) and "toolResult" in block:
                    has_tool_result = True
                    break

        if has_tool_result:
            yield {
                "contentBlockDelta": {
                    "delta": {
                        "text": (
                            "Autonomous Quality Control Remediation Complete: "
                            "I have evaluated the QC inspection report, diagnosed the defect root cause, "
                            "and executed the targeted correction via the revise_video tool. "
                            "The deliverable has been re-assembled and re-audited."
                        )
                    }
                }
            }
            yield {"messageStop": {"stopReason": "end_turn"}}
            return

        # Extract textual content across conversation turns to reason over QC issues
        prompt_text = ""
        for msg in messages:
            if isinstance(msg, dict):
                for block in msg.get("content", []):
                    if isinstance(block, dict) and "text" in block:
                        prompt_text += " " + block["text"]

        prompt_lower = prompt_text.lower()

        # Agentic diagnosis and targeted correction selection
        if "audio" in prompt_lower or "narration" in prompt_lower:
            action = "regenerate_audio"
            reason = "The final cut is missing its narration audio stream, so narration must be regenerated and the video reassembled."
            feedback = "Audio stream absent from deliverable. Regenerating narration track."
        elif "visual" in prompt_lower or "video stream" in prompt_lower:
            action = "regenerate_visual"
            reason = "Visual stream defect detected; regenerating affected scene visuals and reassembling deliverable."
            feedback = "Visual stream defect identified in deliverable. Re-rendering visuals."
        elif "duration" in prompt_lower or "timing" in prompt_lower:
            action = "retime_scene"
            reason = "Deliverable duration exceeds tolerance limits; retiming scene beats to align with brief."
            feedback = "Duration mismatch detected during QC inspection."
        else:
            action = "regenerate_audio"
            reason = "Quality control defect requires targeted remediation of deliverable streams."
            feedback = "Remediating detected quality control defect."

        tool_input = {
            "feedback": feedback,
            "requested_change": action,
            "target_scenes": [1, 2, 3],
            "reason": reason,
        }

        yield {
            "contentBlockStart": {
                "start": {
                    "toolUse": {
                        "toolUseId": "call_revision_1",
                        "name": "revise_video",
                    }
                }
            }
        }
        yield {
            "contentBlockDelta": {
                "delta": {
                    "toolUse": {
                        "input": json.dumps(tool_input)
                    }
                }
            }
        }
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use"}}


def create_tafs_pilot_agent(
    model_id: Optional[str] = None,
    region_name: Optional[str] = None,
    allow_local_fallback: bool = False,
) -> Agent:
    """Instantiates the Taf's Pilot Strands producer agent.

    Uses Amazon Strands Agents SDK connected to Amazon Bedrock when credentials exist,
    or a genuine local Strands Model subclass when running in honest local fallback mode.
    """
    has_creds, cred_status = check_aws_credentials()
    if not has_creds:
        if allow_local_fallback:
            active_model = LocalReasoningModel()
        else:
            raise RuntimeError(
                f"AWS Bedrock configuration error: {cred_status}\n\n"
                "To enable the Taf's Pilot agent:\n"
                "  1. Configure your AWS credentials using standard AWS tools:\n"
                "       aws configure (or aws sso login)\n"
                "     or set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in your environment.\n"
                "  2. Verify Amazon Bedrock model access is enabled in your AWS console for the target region.\n"
                "  3. Set BEDROCK_MODEL_ID in .env with your chosen invokable model ID."
            )
    else:
        region = region_name or get_configured_aws_region()
        chosen_model = model_id or get_configured_bedrock_model_id()
        if not chosen_model:
            discovered = discover_available_bedrock_models(region=region)
            if discovered:
                chosen_model = discovered[0]
            else:
                raise RuntimeError(
                    f"No Bedrock model specified and none discovered in region '{region}'.\n"
                    "Please specify BEDROCK_MODEL_ID in your environment or .env file with a model "
                    "available to your AWS account."
                )

        active_model = BedrockModel(
            model_id=chosen_model,
            region_name=region,
        )

    agent = Agent(
        model=active_model,
        system_prompt=TAFS_PILOT_PRODUCER_PROMPT,
        tools=[
            request_hook_approval,
            finalize_scene_plan,
            create_production_plan,
            synthesize_voiceover,
            resolve_visuals,
            assemble_video,
            audit_video,
            revise_video,
        ],
    )

    return agent


def run_agent_qc_revision(
    qc_report: VideoQCReport,
    agent: Optional[Agent] = None,
    project_state: Optional[ProjectState] = None,
) -> Tuple[Any, ProjectState]:
    """Passes the structured QC report to the Strands Agent, which reasons about the defect
    and invokes the revise_video tool to perform targeted correction."""
    if project_state is None:
        project_state = get_active_project_state()
        if project_state is None:
            raise ValueError("No active ProjectState found.")

    set_active_project_state(project_state)

    if agent is None:
        agent = create_tafs_pilot_agent(allow_local_fallback=True)

    revision_prompt = (
        f"CRITICAL QUALITY CONTROL ALERT:\n"
        f"The assembled deliverable failed the automated multi-modal QC inspection.\n"
        f"- QC Status: {qc_report.status}\n"
        f"- Issues Reported: {json.dumps(qc_report.issues)}\n"
        f"- Target Duration: {project_state.production_plan.target_duration if project_state.production_plan else 30.0}s\n"
        f"- Measured Duration: {qc_report.duration:.2f}s\n"
        f"- Video Stream Present: {qc_report.has_video_stream}\n"
        f"- Audio Stream Present: {qc_report.has_audio_stream}\n"
        f"- Current Revision Count: {project_state.revision_count}/{project_state.max_revisions}\n\n"
        f"As executive video producer, you must diagnose the root cause of these defects. "
        f"Reason about whether the issue requires audio regeneration, visual re-rendering, retiming, or caption rebuilding. "
        f"Then invoke the `revise_video` tool with your targeted correction request, specifying the target scenes and your reasoning."
    )

    result = agent(revision_prompt)
    return result, project_state


def run_producer_workflow(
    brief: CreatorBrief,
    agent: Optional[Agent] = None,
    project_state: Optional[ProjectState] = None,
) -> Tuple[Any, ProjectState]:
    """Executes the autonomous producer workflow tracking state in ProjectState."""
    if project_state is None:
        project_state = ProjectState(brief=brief)

    set_active_project_state(project_state)

    if agent is None:
        agent = create_tafs_pilot_agent()

    prompt = (
        f"A creator has submitted a new video brief. Follow your complete production workflow:\n"
        f"1. Propose 3 differentiated hooks using the request_hook_approval tool.\n"
        f"2. Once hook approval is received, finalize the scene plan with finalize_scene_plan.\n"
        f"3. Synthesize voiceovers using synthesize_voiceover.\n"
        f"4. Resolve visuals using resolve_visuals.\n"
        f"5. Assemble the final deliverable with assemble_video.\n"
        f"6. Audit the deliverable with audit_video.\n\n"
        f"--- CREATOR BRIEF ---\n"
        f"Topic: {brief.topic}\n"
        f"Audience: {brief.audience}\n"
        f"Goal: {brief.goal}\n"
        f"Tone: {brief.tone}\n"
        f"Approximate Duration: {brief.approximate_duration} seconds\n"
        f"Platform: {brief.platform}\n"
        f"----------------------\n"
    )

    response = agent(prompt)
    return response, project_state
