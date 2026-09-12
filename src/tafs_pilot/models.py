"""Domain models and schemas for Taf's Pilot.

Defines Pydantic v2 schemas for creator briefs, hook proposals,
production plans, scene specifications, media artifacts, QC reports,
autonomous revision requests, and state machine lifecycle.
"""

from enum import Enum
import json
import os
import uuid
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ProjectStatus(str, Enum):
    """Lifecycle states for Taf's Pilot production pipeline."""

    BRIEF_RECEIVED = "BRIEF_RECEIVED"
    AWAITING_HOOK_APPROVAL = "AWAITING_HOOK_APPROVAL"
    HOOK_APPROVED = "HOOK_APPROVED"
    SCENE_PLAN_READY = "SCENE_PLAN_READY"
    PRODUCING = "PRODUCING"
    AUDITING = "AUDITING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    REVISION_IN_PROGRESS = "REVISION_IN_PROGRESS"
    FAILED = "FAILED"


class CreatorBrief(BaseModel):
    """Input brief supplied by the professional creator or marketing team."""

    topic: str = Field(
        ...,
        description="The subject matter, core thesis, or educational topic of the video.",
        min_length=3,
    )
    audience: str = Field(
        ...,
        description="Target demographic, persona, or professional audience.",
        min_length=3,
    )
    goal: str = Field(
        ...,
        description="Primary business or engagement goal (e.g., lead gen, retention, authority, conversion).",
        min_length=3,
    )
    tone: str = Field(
        default="educational and engaging",
        description="Delivery style and emotional resonance (e.g., authoritative, witty, urgent, calm).",
    )
    approximate_duration: int = Field(
        default=60,
        description="Target video length in seconds (typically 15 to 90 seconds for short-form).",
        ge=10,
        le=300,
    )
    platform: str = Field(
        default="YouTube Shorts",
        description="Primary distribution channel (e.g., YouTube Shorts, Instagram Reels, TikTok, LinkedIn Video).",
    )


class ScenePlanItem(BaseModel):
    """Specification for an individual scene within the video production plan."""

    scene_id: int = Field(
        ...,
        description="1-indexed sequence identifier of the scene.",
        ge=1,
    )
    scene_type: str = Field(
        default="MG",
        description="Visual style code: 'CIN' (cinematic b-roll), 'MG' (motion graphics / typography), 'DEMO' (screen walk-through).",
    )
    visual_description: str = Field(
        ...,
        description="Creative director directive describing what appears on screen.",
        min_length=5,
    )
    narration_text: str = Field(
        ...,
        description="Spoken voiceover script or dialogue for this specific beat.",
        min_length=2,
    )
    estimated_duration: float = Field(
        ...,
        description="Target duration in seconds for this scene (must align with natural speech cadence).",
        gt=0.0,
    )

    @field_validator("scene_type")
    @classmethod
    def normalize_scene_type(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper in {"CIN", "MG", "DEMO", "TALKING_HEAD"}:
            return v_upper
        return "MG"


class HookProposal(BaseModel):
    """Proposed hooks formulated by the autonomous agent awaiting human approval."""

    topic: str = Field(..., description="The brief topic being addressed.")
    hook_options: List[str] = Field(
        ...,
        description="At least 3 differentiated hook angles (e.g., counter-intuitive, problem agitation, bold claim).",
    )
    recommended_hook: str = Field(
        ...,
        description="The primary hook recommended by the agent based on retention strategy.",
    )
    selected_angle: str = Field(
        ...,
        description="The narrative or psychological angle uniting the hook options.",
    )
    reasoning: str = Field(
        ...,
        description="Strategic justification explaining why these hooks will retain the target audience.",
    )

    @field_validator("hook_options")
    @classmethod
    def validate_hooks_count(cls, v: List[str]) -> List[str]:
        cleaned = [h.strip() for h in v if h and h.strip()]
        if len(cleaned) < 3:
            raise ValueError(
                f"Hook proposal requires at least 3 distinct hook options (received {len(cleaned)})."
            )
        return cleaned

    @model_validator(mode="after")
    def validate_recommended_in_options(self) -> "HookProposal":
        if self.recommended_hook not in self.hook_options:
            self.hook_options.append(self.recommended_hook)
        return self


class ProductionPlan(BaseModel):
    """Comprehensive, validated blueprint created by the agent for video production."""

    objective: str = Field(
        ...,
        description="Synthesized strategic objective aligning creator goal and audience demand.",
        min_length=5,
    )
    audience: str = Field(
        ...,
        description="Target audience persona addressed by this plan.",
    )
    platform: str = Field(
        ...,
        description="Target platform formatting and constraint context.",
    )
    target_duration: int = Field(
        ...,
        description="Total planned runtime in seconds.",
        ge=10,
    )
    tone: str = Field(
        ...,
        description="Editorial voice and aesthetic pacing tone.",
    )
    hook_options: List[str] = Field(
        ...,
        description="List of at least 3 distinct opening hook angles.",
    )
    recommended_hook: str = Field(
        ...,
        description="The primary recommended hook.",
    )
    selected_angle: str = Field(
        ...,
        description="The working narrative thesis or psychological framing.",
    )
    scene_plan: List[ScenePlanItem] = Field(
        ...,
        description="Ordered sequence of scenes covering the full duration.",
    )
    success_criteria: List[str] = Field(
        ...,
        description="Auditable benchmarks defining what makes this deliverable successful.",
    )

    @field_validator("hook_options")
    @classmethod
    def validate_hooks_count(cls, v: List[str]) -> List[str]:
        cleaned = [h.strip() for h in v if h and h.strip()]
        if len(cleaned) < 3:
            raise ValueError(
                f"Production plan requires at least 3 distinct hook options (received {len(cleaned)})."
            )
        return cleaned

    @field_validator("scene_plan")
    @classmethod
    def validate_scenes_present(cls, v: List[ScenePlanItem]) -> List[ScenePlanItem]:
        if not v:
            raise ValueError("Production plan must have at least one scene.")
        return v

    @field_validator("success_criteria")
    @classmethod
    def validate_criteria_present(cls, v: List[str]) -> List[str]:
        cleaned = [c.strip() for c in v if c and c.strip()]
        if not cleaned:
            raise ValueError("Production plan must define at least one success criterion.")
        return cleaned

    @model_validator(mode="after")
    def validate_hook_coherence(self) -> "ProductionPlan":
        if self.recommended_hook not in self.hook_options:
            self.hook_options.append(self.recommended_hook)
        return self


# ------------------------------------------------------------------------------
# Real Media Production & QC Schemas with Provider Transparency
# ------------------------------------------------------------------------------

class VoiceoverSceneResult(BaseModel):
    """Artifact metadata for an individual scene's synthesized voiceover."""

    scene_id: int
    audio_path: str
    duration: float = Field(..., gt=0.0, description="Actual measured audio duration in seconds.")
    provider: str
    mode: Literal["aws", "local_fallback", "mock"] = "local_fallback"
    file_size_bytes: int = Field(default=0)


class VoiceoverResult(BaseModel):
    """Aggregated result of the voiceover synthesis stage."""

    status: str = "success"
    provider: str
    mode: Literal["aws", "local_fallback", "mock"] = "local_fallback"
    total_duration: float
    scenes: List[VoiceoverSceneResult]


class VisualSceneResult(BaseModel):
    """Artifact metadata for an individual scene's resolved visual asset."""

    scene_id: int
    visual_path: str
    provider: str
    mode: Literal["aws", "local_fallback", "mock"] = "local_fallback"
    format: str = "mp4"
    duration: float = Field(default=0.0)


class VisualResult(BaseModel):
    """Aggregated result of the visual resolution stage."""

    status: str = "success"
    provider: str
    mode: Literal["aws", "local_fallback", "mock"] = "local_fallback"
    scenes: List[VisualSceneResult]


class VideoQCReport(BaseModel):
    """Structured quality-control report generated by auditing the final MP4."""

    status: Literal["PASS", "FAIL"]
    file_path: str
    file_size_bytes: int
    duration: float
    width: int
    height: int
    has_video_stream: bool
    has_audio_stream: bool
    subtitles_present: bool = True
    duration_tolerance_delta: float
    issues: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RevisionRequest(BaseModel):
    """Specification for revising an audited video that failed QC or needs creator adjustments."""

    revision_number: int = Field(default=1, description="Sequential revision index.")
    issues: List[str] = Field(default_factory=list, description="Specific QC issues being addressed.")
    target_scene_ids: List[int] = Field(default_factory=list, description="Specific scene IDs to regenerate.")
    requested_change: str = Field(
        default="regenerate_audio",
        description="Action to take: 'regenerate_audio', 'regenerate_visual', 'retime_scene', 'rebuild_captions'.",
    )
    reason: str = Field(default="", description="Strategic reasoning for this specific revision.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional parameters for revision execution.")


class ProjectState(BaseModel):
    """Typed, stateful project model tracking the complete production lifecycle."""

    project_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: ProjectStatus = Field(default=ProjectStatus.BRIEF_RECEIVED)
    brief: CreatorBrief
    hook_proposal: Optional[HookProposal] = None
    selected_hook: Optional[str] = None
    approval_notes: Optional[str] = None
    production_plan: Optional[ProductionPlan] = None
    voiceover_result: Optional[VoiceoverResult] = None
    visual_result: Optional[VisualResult] = None
    final_video_path: Optional[str] = None
    qc_report: Optional[VideoQCReport] = None
    revision_count: int = Field(default=0)
    max_revisions: int = Field(default=2)
    revision_history: List[RevisionRequest] = Field(default_factory=list)
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list)

    @property
    def artifact_dir(self) -> str:
        """Returns the project's dedicated artifact directory path."""
        path = os.path.join("artifacts", self.project_id)
        for sub in ["audio", "visuals", "captions", "renders", "revisions"]:
            os.makedirs(os.path.join(path, sub), exist_ok=True)
        return path

    def transition_to_awaiting_approval(self, proposal: HookProposal) -> None:
        """Transitions state to AWAITING_HOOK_APPROVAL with the given proposal."""
        self.hook_proposal = proposal
        self.status = ProjectStatus.AWAITING_HOOK_APPROVAL
        self.history.append("Generated 3 hook options. Awaiting creator sign-off.")

    def approve_hook(self, chosen_hook: str, notes: str = "") -> None:
        """Records creator's chosen hook and transitions state to HOOK_APPROVED."""
        if self.status != ProjectStatus.AWAITING_HOOK_APPROVAL:
            raise ValueError(
                f"Cannot approve hook while in state '{self.status}'. Expected '{ProjectStatus.AWAITING_HOOK_APPROVAL}'."
            )
        self.selected_hook = chosen_hook.strip()
        self.approval_notes = notes.strip()
        self.status = ProjectStatus.HOOK_APPROVED
        self.history.append(f"Creator approved hook: '{self.selected_hook}'. Ready for scene planning.")

    def finalize_scene_plan(
        self,
        objective: str,
        scene_plan: List[ScenePlanItem],
        success_criteria: List[str],
    ) -> ProductionPlan:
        """Validates the scene plan and transitions state to SCENE_PLAN_READY."""
        if self.status != ProjectStatus.HOOK_APPROVED:
            raise ValueError(
                f"Cannot finalize scene plan while in state '{self.status}'. Expected '{ProjectStatus.HOOK_APPROVED}'."
            )
        if not self.selected_hook:
            raise ValueError("No approved hook found in state.")
        if not self.hook_proposal:
            raise ValueError("No hook proposal found in state.")

        plan = ProductionPlan(
            objective=objective,
            audience=self.brief.audience,
            platform=self.brief.platform,
            target_duration=self.brief.approximate_duration,
            tone=self.brief.tone,
            hook_options=self.hook_proposal.hook_options,
            recommended_hook=self.selected_hook,
            selected_angle=self.hook_proposal.selected_angle,
            scene_plan=scene_plan,
            success_criteria=success_criteria,
        )

        self.production_plan = plan
        self.status = ProjectStatus.SCENE_PLAN_READY
        self.history.append(
            f"Finalized scene plan with {len(scene_plan)} scenes and {len(success_criteria)} success criteria."
        )
        return plan

    def record_voiceover(self, vo: VoiceoverResult) -> None:
        """Updates state with voiceover synthesis artifacts."""
        self.voiceover_result = vo
        self.status = ProjectStatus.PRODUCING
        self.history.append(f"Voiceover generated via {vo.provider} ({vo.mode}): {vo.total_duration:.2f}s total.")

    def record_visuals(self, vr: VisualResult) -> None:
        """Updates state with resolved visual assets."""
        self.visual_result = vr
        self.history.append(f"Visuals resolved via {vr.provider} ({vr.mode}) for {len(vr.scenes)} scenes.")

    def record_final_video(self, video_path: str) -> None:
        """Updates state with assembled MP4 deliverable."""
        self.final_video_path = video_path
        self.status = ProjectStatus.AUDITING
        self.history.append(f"Assembled final deliverable: {video_path}")

    def record_qc_report(self, report: VideoQCReport) -> None:
        """Updates state with QC audit results."""
        self.qc_report = report
        entry = {
            "audit_index": len(self.audit_history) + 1,
            "status": report.status,
            "duration": report.duration,
            "issues": list(report.issues),
            "revision_count": self.revision_count,
        }
        self.audit_history.append(entry)

        # Persist audit history
        history_file = os.path.join(self.artifact_dir, "audit_history.json")
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.audit_history, f, indent=2)
        except Exception:
            pass

        if report.status == "PASS":
            self.status = ProjectStatus.READY_FOR_REVIEW
            self.history.append(f"QC Passed ({report.duration:.2f}s, {report.width}x{report.height}). Ready for review.")
        else:
            self.status = ProjectStatus.REVISION_REQUIRED
            self.history.append(f"QC Failed with issues: {report.issues}. Revision required.")

    def request_revision(self, revision: RevisionRequest) -> None:
        """Registers a revision request if within budget; otherwise enforces budget boundary."""
        if self.revision_count >= self.max_revisions:
            self.status = ProjectStatus.REVISION_REQUIRED
            raise ValueError(
                f"Maximum revision budget ({self.max_revisions}) exhausted. Cannot initiate further automatic revisions."
            )
        self.revision_count += 1
        revision.revision_number = self.revision_count
        self.revision_history.append(revision)
        self.status = ProjectStatus.REVISION_IN_PROGRESS
        self.history.append(
            f"Revision #{self.revision_count} initiated: '{revision.requested_change}' on scenes {revision.target_scene_ids} ({revision.reason})"
        )
