"""Tools package for Taf's Pilot."""

from tafs_pilot.tools.planning import (
    create_production_plan,
    finalize_scene_plan,
    get_active_project_state,
    request_hook_approval,
    set_active_project_state,
    set_hook_approval_callback,
)
from tafs_pilot.tools.production import (
    assemble_video,
    audit_video,
    resolve_visuals,
    revise_video,
    simulate_qc_defect,
    synthesize_voiceover,
)

__all__ = [
    "assemble_video",
    "audit_video",
    "create_production_plan",
    "finalize_scene_plan",
    "get_active_project_state",
    "request_hook_approval",
    "resolve_visuals",
    "revise_video",
    "set_active_project_state",
    "set_hook_approval_callback",
    "simulate_qc_defect",
    "synthesize_voiceover",
]
