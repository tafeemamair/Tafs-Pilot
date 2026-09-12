"""Strands planning and human-approval tools for Taf's Pilot.

Contains the @tool decorated functions used by the Strands autonomous producer
agent to propose hooks, pause for human approval, and finalize structured scene plans.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import ValidationError
from strands import tool
from tafs_pilot.models import (
    HookProposal,
    ProductionPlan,
    ProjectState,
    ProjectStatus,
    ScenePlanItem,
)

# Global or thread-local active project context reference (optional hook for agent runs)
_ACTIVE_PROJECT_STATE: Optional[ProjectState] = None
_HOOK_APPROVAL_CALLBACK: Optional[Callable[[HookProposal], Tuple[str, str]]] = None


def set_active_project_state(state: Optional[ProjectState]) -> None:
    """Sets the active ProjectState instance for the current agent execution session."""
    global _ACTIVE_PROJECT_STATE
    _ACTIVE_PROJECT_STATE = state


def get_active_project_state() -> Optional[ProjectState]:
    """Retrieves the active ProjectState instance."""
    global _ACTIVE_PROJECT_STATE
    return _ACTIVE_PROJECT_STATE


def set_hook_approval_callback(callback: Optional[Callable[[HookProposal], Tuple[str, str]]]) -> None:
    """Sets an interactive callback to resolve creator hook approval dynamically.

    The callback takes a HookProposal and returns (selected_hook, notes).
    """
    global _HOOK_APPROVAL_CALLBACK
    _HOOK_APPROVAL_CALLBACK = callback


@tool
def request_hook_approval(
    topic: str,
    hook_options: List[str],
    recommended_hook: str,
    selected_angle: str,
    reasoning: str,
) -> Dict[str, Any]:
    """Proposes 3 differentiated hooks to the creator and pauses for human approval.

    The autonomous agent calls this tool after analyzing the creator's brief
    to present opening retention hooks before producing scenes.

    Args:
        topic: The video subject matter.
        hook_options: At least 3 creative, differentiated opening hook variations
                      (e.g., counter-intuitive, problem-agitation, bold declaration).
        recommended_hook: The top recommended opening hook to test.
        selected_angle: Working narrative thesis or psychological frame.
        reasoning: Strategic rationale explaining why these hooks capture viewer attention.

    Returns:
        dict: Approval state status, presented options, and selection outcome.
    """
    try:
        proposal = HookProposal(
            topic=topic,
            hook_options=hook_options,
            recommended_hook=recommended_hook,
            selected_angle=selected_angle,
            reasoning=reasoning,
        )

        global _ACTIVE_PROJECT_STATE, _HOOK_APPROVAL_CALLBACK
        if _ACTIVE_PROJECT_STATE is not None:
            _ACTIVE_PROJECT_STATE.transition_to_awaiting_approval(proposal)

        # Check if an interactive creator callback is registered (e.g. CLI interactive prompt or test)
        if _HOOK_APPROVAL_CALLBACK is not None:
            chosen_hook, notes = _HOOK_APPROVAL_CALLBACK(proposal)
            if _ACTIVE_PROJECT_STATE is not None:
                _ACTIVE_PROJECT_STATE.approve_hook(chosen_hook, notes)

            return {
                "status": "approved",
                "message": f"Creator reviewed hooks and approved: '{chosen_hook}'.",
                "selected_hook": chosen_hook,
                "approval_notes": notes,
                "next_step": "Proceed to scene planning using finalize_scene_plan with the approved hook.",
                "proposal": proposal.model_dump(),
            }

        # Otherwise, pause for human selection
        return {
            "status": "awaiting_human_approval",
            "message": (
                "Hook proposal formulated and registered. Execution paused awaiting creator selection. "
                "The creator must select one of the hook options before scene production can begin."
            ),
            "hook_options": proposal.hook_options,
            "recommended_hook": proposal.recommended_hook,
            "selected_angle": proposal.selected_angle,
            "reasoning": proposal.reasoning,
            "proposal": proposal.model_dump(),
        }

    except ValidationError as e:
        return {
            "status": "error",
            "message": f"Validation error in hook proposal: {e.errors()}",
            "errors": e.errors(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error during hook approval request: {str(e)}",
        }


@tool
def finalize_scene_plan(
    selected_hook: str,
    objective: str,
    scene_plan: List[Dict[str, Any]],
    success_criteria: List[str],
) -> Dict[str, Any]:
    """Finalizes and validates the scene breakdown building upon the creator's approved hook.

    The autonomous agent calls this tool once a hook has been approved by the creator,
    translating the brief and selected angle into a cohesive short-form script.

    Args:
        selected_hook: The creator-approved opening hook.
        objective: Strategic objective aligning creator goals and audience demand.
        scene_plan: Ordered list of scene beats, each containing:
            - 'scene_id': int sequence identifier
            - 'scene_type': 'CIN' (cinematic) or 'MG' (kinetic motion graphics)
            - 'visual_description': Concrete visual guidance for editing/generation
            - 'narration_text': Spoken voiceover script for this beat
            - 'estimated_duration': Duration in seconds for this scene
        success_criteria: List of benchmarks defining production success.

    Returns:
        dict: Standardized, validated production plan dictionary.
    """
    try:
        parsed_scenes: List[ScenePlanItem] = []
        for i, raw_scene in enumerate(scene_plan):
            if not isinstance(raw_scene, dict):
                raise ValueError(f"Scene at index {i} must be a dictionary.")
            scene_dict = dict(raw_scene)
            if "scene_id" not in scene_dict:
                scene_dict["scene_id"] = i + 1
            parsed_scenes.append(ScenePlanItem(**scene_dict))

        global _ACTIVE_PROJECT_STATE
        if _ACTIVE_PROJECT_STATE is not None:
            # If state is awaiting approval, ensure it gets approved with this hook
            if _ACTIVE_PROJECT_STATE.status == ProjectStatus.AWAITING_HOOK_APPROVAL:
                _ACTIVE_PROJECT_STATE.approve_hook(selected_hook)

            plan = _ACTIVE_PROJECT_STATE.finalize_scene_plan(
                objective=objective,
                scene_plan=parsed_scenes,
                success_criteria=success_criteria,
            )
            return {
                "status": "success",
                "message": "Production plan finalized and registered in ProjectState.",
                "plan": plan.model_dump(),
                "project_status": _ACTIVE_PROJECT_STATE.status.value,
            }

        # Standalone validation if no active ProjectState is attached
        if not parsed_scenes:
            raise ValueError("Scene plan must contain at least one scene.")

        return {
            "status": "success",
            "message": "Scene plan validated successfully.",
            "selected_hook": selected_hook,
            "scene_count": len(parsed_scenes),
            "scenes": [s.model_dump() for s in parsed_scenes],
            "success_criteria": success_criteria,
        }

    except ValidationError as e:
        return {
            "status": "error",
            "message": f"Validation error while finalizing scene plan: {e.errors()}",
            "errors": e.errors(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error while finalizing scene plan: {str(e)}",
        }


@tool
def create_production_plan(
    objective: str,
    audience: str,
    platform: str,
    target_duration: int,
    tone: str,
    hook_options: List[str],
    recommended_hook: str,
    selected_angle: str,
    scene_plan: List[Dict[str, Any]],
    success_criteria: List[str],
) -> Dict[str, Any]:
    """Single-shot production plan creator (Milestone 1 compatibility)."""
    try:
        parsed_scenes: List[ScenePlanItem] = []
        for i, raw_scene in enumerate(scene_plan):
            if not isinstance(raw_scene, dict):
                raise ValueError(f"Scene item at index {i} must be a dictionary.")
            scene_dict = dict(raw_scene)
            if "scene_id" not in scene_dict:
                scene_dict["scene_id"] = i + 1
            parsed_scenes.append(ScenePlanItem(**scene_dict))

        plan = ProductionPlan(
            objective=objective,
            audience=audience,
            platform=platform,
            target_duration=int(target_duration),
            tone=tone,
            hook_options=hook_options,
            recommended_hook=recommended_hook,
            selected_angle=selected_angle,
            scene_plan=parsed_scenes,
            success_criteria=success_criteria,
        )

        return {
            "status": "success",
            "message": "Production plan validated and registered successfully.",
            "plan": plan.model_dump(),
        }

    except ValidationError as e:
        return {
            "status": "error",
            "message": f"Schema validation error while creating production plan: {e.errors()}",
            "errors": e.errors(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error during plan creation: {str(e)}",
        }
