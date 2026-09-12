"""Strands real media production tools for Taf's Pilot.

Contains @tool decorated functions for:
- Voiceover synthesis (Amazon Polly / Procedural)
- Visual asset resolution (Bedrock Titan / Procedural)
- Video compositing & subtitle burning (FFmpeg)
- Multi-modal quality inspection (FFprobe)
- Autonomous revision handling & bounded self-correction
- Safe test/demo defect simulation for demonstrability
"""

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional
from strands import tool
from tafs_pilot.media.audio import generate_scene_voiceovers
from tafs_pilot.media.assembly import assemble_production_video
from tafs_pilot.media.qc import inspect_video_deliverable
from tafs_pilot.media.visuals import resolve_scene_visuals
from tafs_pilot.models import (
    ProjectState,
    ProjectStatus,
    RevisionRequest,
    ScenePlanItem,
)
from tafs_pilot.tools.planning import get_active_project_state


@tool
def synthesize_voiceover(
    scenes: Optional[List[Dict[str, Any]]] = None,
    provider: Optional[str] = None,
    voice_id: str = "Danielle",
) -> Dict[str, Any]:
    """Synthesizes speech narration audio files for each scene in the production plan.

    The autonomous agent calls this tool after the scene plan is finalized to generate
    spoken audio for each beat and calculate exact spoken durations.

    Args:
        scenes: Optional explicit list of scene dictionaries. If omitted, uses the active ProjectState scene plan.
        provider: Voice synthesis provider ('polly' for AWS Polly, or 'procedural' for local synthesis).
        voice_id: Voice identifier (e.g. 'Danielle', 'Matthew', 'Ruth').

    Returns:
        dict: Generated audio files, scene durations, and total duration.
    """
    try:
        state = get_active_project_state()
        parsed_scenes: List[ScenePlanItem] = []

        if scenes:
            for s in scenes:
                parsed_scenes.append(ScenePlanItem(**s))
        elif state and state.production_plan:
            parsed_scenes = state.production_plan.scene_plan
        else:
            raise ValueError("No scenes provided and no active production plan found in ProjectState.")

        artifact_dir = state.artifact_dir if state else os.path.join("artifacts", "default")
        audio_dir = os.path.join(artifact_dir, "audio")

        vo_result = generate_scene_voiceovers(
            scenes=parsed_scenes,
            output_dir=audio_dir,
            provider=provider,
            voice_id=voice_id,
        )

        if state:
            state.record_voiceover(vo_result)

        return {
            "status": "success",
            "provider": vo_result.provider,
            "mode": vo_result.mode,
            "total_duration": vo_result.total_duration,
            "scenes": [s.model_dump() for s in vo_result.scenes],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Voiceover synthesis failed: {str(e)}",
        }


@tool
def resolve_visuals(
    scenes: Optional[List[Dict[str, Any]]] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolves or generates vertical visual assets for every scene in the plan.

    The autonomous agent calls this tool to prepare 1080x1920 video assets
    matching each scene's creative visual description.

    Args:
        scenes: Optional explicit list of scene dictionaries. If omitted, uses active plan.
        provider: Visual provider ('titan' for AWS Bedrock Titan Image, or 'procedural' for local motion graphics).

    Returns:
        dict: Resolved visual asset paths and formats.
    """
    try:
        state = get_active_project_state()
        parsed_scenes: List[ScenePlanItem] = []

        if scenes:
            for s in scenes:
                parsed_scenes.append(ScenePlanItem(**s))
        elif state and state.production_plan:
            parsed_scenes = state.production_plan.scene_plan
        else:
            raise ValueError("No scenes provided and no active production plan found in ProjectState.")

        artifact_dir = state.artifact_dir if state else os.path.join("artifacts", "default")
        visuals_dir = os.path.join(artifact_dir, "visuals")

        vis_result = resolve_scene_visuals(
            scenes=parsed_scenes,
            output_dir=visuals_dir,
            provider=provider,
        )

        if state:
            state.record_visuals(vis_result)

        return {
            "status": "success",
            "provider": vis_result.provider,
            "mode": vis_result.mode,
            "scenes": [s.model_dump() for s in vis_result.scenes],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Visual resolution failed: {str(e)}",
        }


@tool
def assemble_video(
    output_filename: str = "final.mp4",
) -> Dict[str, Any]:
    """Combines scene visuals, narration voiceovers, and burned captions into a playable MP4.

    The autonomous agent calls this tool once voiceover and visuals are generated.
    The exact narration audio durations drive scene pacing and subtitle timing.

    Args:
        output_filename: Name of the deliverable MP4 file.

    Returns:
        dict: File path and assembly status.
    """
    try:
        state = get_active_project_state()
        if not state:
            raise ValueError("No active ProjectState found. Run planning and generation first.")
        if not state.production_plan:
            raise ValueError("No finalized production plan found in state.")
        if not state.voiceover_result:
            raise ValueError("Voiceover generation has not been executed yet.")
        if not state.visual_result:
            raise ValueError("Visual resolution has not been executed yet.")

        final_path = assemble_production_video(
            scenes=state.production_plan.scene_plan,
            voiceovers=state.voiceover_result,
            visuals=state.visual_result,
            project_artifacts_dir=state.artifact_dir,
            output_filename=output_filename,
        )

        state.record_final_video(final_path)

        return {
            "status": "success",
            "final_video_path": final_path,
            "message": "Video successfully assembled into playable MP4 deliverable.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Video assembly failed: {str(e)}",
        }


@tool
def audit_video(
    video_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Performs multi-modal quality inspection on the rendered MP4 deliverable using ffprobe.

    The autonomous agent calls this tool immediately after assembly to verify
    video streams, audio streams, pacing fidelity, and detect render failures.

    Args:
        video_path: Optional explicit video file path. If omitted, inspects final_video_path from state.

    Returns:
        dict: Structured VideoQCReport with PASS/FAIL status and metrics.
    """
    try:
        state = get_active_project_state()
        target_path = video_path or (state.final_video_path if state else None)
        if not target_path:
            raise ValueError("No video path provided and no final video found in ProjectState.")

        target_duration = (
            float(state.production_plan.target_duration)
            if state and state.production_plan
            else 45.0
        )
        qc_json_path = os.path.join(state.artifact_dir, "qc.json") if state else None

        qc_report = inspect_video_deliverable(
            video_path=target_path,
            target_duration=target_duration,
            qc_output_path=qc_json_path,
        )

        if state:
            state.record_qc_report(qc_report)

        return {
            "status": "success",
            "qc_status": qc_report.status,
            "report": qc_report.model_dump(),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Quality inspection failed: {str(e)}",
        }


@tool
def revise_video(
    feedback: str,
    target_scenes: Optional[List[int]] = None,
    requested_change: str = "regenerate_audio",
    action: Optional[str] = None,
    reason: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Autonomous revision tool executing targeted production corrections after a QC failure.

    The agent calls this tool when audit_video reports a FAIL status. The agent decides
    what production change is required (e.g. regenerating missing audio, fixing visuals, or retiming),
    and this tool executes the fix, re-assembles the deliverable, and re-audits it.

    Enforces a strict revision budget (MAX_REVISIONS = 2) to prevent infinite loops.

    Args:
        feedback: Explanation of the defect or director critique.
        target_scenes: List of scene IDs that require revision (e.g. [1]).
        requested_change: Action: 'regenerate_audio', 'regenerate_visual', 'retime_scene', 'rebuild_captions'.
        reason: Strategic reasoning for why this correction resolves the defect.
        parameters: Optional execution overrides.

    Returns:
        dict: Revision status, new QC result, and updated deliverable path.
    """
    try:
        state = get_active_project_state()
        if not state:
            raise ValueError("No active ProjectState found.")
        if not state.production_plan:
            raise ValueError("No production plan found in ProjectState.")

        # Check revision budget
        if state.revision_count >= state.max_revisions:
            state.status = ProjectStatus.REVISION_REQUIRED
            return {
                "status": "budget_exhausted",
                "message": (
                    f"Maximum revision budget ({state.max_revisions}) exhausted. "
                    "Halting autonomous loop to surface unresolved issues to the creator."
                ),
                "revision_count": state.revision_count,
                "project_status": state.status.value,
                "unresolved_issues": state.qc_report.issues if state.qc_report else [],
            }

        effective_change = action or requested_change

        # Register revision request
        revision_req = RevisionRequest(
            revision_number=state.revision_count + 1,
            issues=state.qc_report.issues if state.qc_report else [],
            target_scene_ids=target_scenes or [],
            requested_change=effective_change,
            reason=reason or feedback,
            parameters=parameters or {},
        )
        state.request_revision(revision_req)

        # If project has not assembled video yet, or if purely script/scene adjustment, initiate revision mode
        if effective_change == "adjust_scenes" or not state.final_video_path:
            return {
                "status": "revision_initiated",
                "revision_number": state.revision_count,
                "project_status": state.status.value,
                "target_scenes": target_scenes or [],
                "feedback": feedback,
                "action": effective_change,
            }

        # Archive prior deliverable if present
        if state.final_video_path and os.path.exists(state.final_video_path):
            rev_archive = os.path.join(
                state.artifact_dir, "revisions", f"pre_revision_{state.revision_count}.mp4"
            )
            shutil.copy(state.final_video_path, rev_archive)

        target_ids = set(target_scenes) if target_scenes else {s.scene_id for s in state.production_plan.scene_plan}
        scenes_to_fix = [s for s in state.production_plan.scene_plan if s.scene_id in target_ids]

        # Execute targeted production correction based on agent decision
        if effective_change in {"regenerate_audio", "missing_audio"}:
            provider = state.voiceover_result.provider if state.voiceover_result else "procedural"
            audio_dir = os.path.join(state.artifact_dir, "audio")
            vo_update = generate_scene_voiceovers(
                scenes=scenes_to_fix,
                output_dir=audio_dir,
                provider=provider,
            )
            # Merge into voiceover_result
            if state.voiceover_result:
                vo_dict = {s.scene_id: s for s in state.voiceover_result.scenes}
                for new_s in vo_update.scenes:
                    vo_dict[new_s.scene_id] = new_s
                state.voiceover_result.scenes = sorted(vo_dict.values(), key=lambda x: x.scene_id)
                state.voiceover_result.total_duration = sum(s.duration for s in state.voiceover_result.scenes)
            else:
                state.record_voiceover(vo_update)

        elif effective_change in {"regenerate_visual", "missing_visual"}:
            provider = state.visual_result.provider if state.visual_result else "procedural"
            visuals_dir = os.path.join(state.artifact_dir, "visuals")
            vis_update = resolve_scene_visuals(
                scenes=scenes_to_fix,
                output_dir=visuals_dir,
                provider=provider,
            )
            if state.visual_result:
                vis_dict = {s.scene_id: s for s in state.visual_result.scenes}
                for new_v in vis_update.scenes:
                    vis_dict[new_v.scene_id] = new_v
                state.visual_result.scenes = sorted(vis_dict.values(), key=lambda x: x.scene_id)
            else:
                state.record_visuals(vis_update)

        # Re-assemble deliverable
        new_final = assemble_production_video(
            scenes=state.production_plan.scene_plan,
            voiceovers=state.voiceover_result,
            visuals=state.visual_result,
            project_artifacts_dir=state.artifact_dir,
            output_filename="final.mp4",
        )
        state.record_final_video(new_final)

        # Automatically re-audit deliverable
        qc_json_path = os.path.join(state.artifact_dir, "qc.json")
        target_dur = float(state.production_plan.target_duration)
        new_qc = inspect_video_deliverable(
            video_path=new_final,
            target_duration=target_dur,
            qc_output_path=qc_json_path,
        )
        state.record_qc_report(new_qc)

        # Persist structured agent decision evidence (Section 7)
        decision_record = {
            "revision_number": state.revision_count,
            "qc_issue": (
                revision_req.issues[0]
                if revision_req.issues
                else "Quality control defect"
            ),
            "agent_decision": effective_change,
            "tool_called": "revise_video",
            "reason": reason or feedback,
            "result": "success" if new_qc.status == "PASS" else "revision_required",
        }
        decision_path = os.path.join(state.artifact_dir, "revision_decision.json")
        try:
            with open(decision_path, "w", encoding="utf-8") as f:
                json.dump(decision_record, f, indent=2)
        except Exception:
            pass

        return {
            "status": "revision_completed",
            "revision_number": state.revision_count,
            "action_taken": effective_change,
            "target_scenes": target_scenes or [],
            "new_qc_status": new_qc.status,
            "project_status": state.status.value,
            "issues_remaining": new_qc.issues,
            "final_video_path": new_final,
            "decision_evidence": decision_record,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Revision failed: {str(e)}",
        }


def simulate_qc_defect(defect_type: str = "missing_audio") -> Dict[str, Any]:
    """Safe test/demo helper that creates a deterministic defect in the current deliverable.

    Enables testing and demonstrating the agent's autonomous AUDIT -> FAIL -> REVISE -> AUDIT -> PASS loop.
    Does NOT corrupt permanent source assets.
    """
    state = get_active_project_state()
    if not state or not state.final_video_path or not os.path.exists(state.final_video_path):
        raise RuntimeError("Cannot simulate defect: No assembled final.mp4 found in active ProjectState.")

    video_path = state.final_video_path
    corrupt_temp = video_path + ".defect.mp4"

    # Safely archive pristine video so deliverable is never permanently damaged
    archive_dir = os.path.join(state.artifact_dir, "revisions")
    os.makedirs(archive_dir, exist_ok=True)
    clean_backup = os.path.join(archive_dir, "pre_defect_pristine.mp4")
    if not os.path.exists(clean_backup):
        shutil.copy(video_path, clean_backup)

    if defect_type == "missing_audio":
        # Strip audio stream completely from the MP4
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-an",  # Strip audio
            "-c:v", "copy",
            corrupt_temp,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        shutil.move(corrupt_temp, video_path)

    elif defect_type == "duration_mismatch":
        # Truncate deliverable to 0.8 seconds (triggering duration and size issues)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-t", "0.8",
            "-c", "copy",
            corrupt_temp,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        shutil.move(corrupt_temp, video_path)

    # Re-run audit to register FAIL in ProjectState
    qc_res = audit_video()
    return {
        "defect_type": defect_type,
        "qc_status": qc_res["qc_status"],
        "issues": qc_res["report"]["issues"],
        "project_status": state.status.value,
    }
