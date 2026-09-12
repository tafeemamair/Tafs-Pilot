import json
import os
import shutil
from tafs_pilot.models import (
    CreatorBrief,
    HookProposal,
    ProductionPlan,
    ProjectState,
    ProjectStatus,
    ScenePlanItem,
)
from tafs_pilot.tools.planning import set_active_project_state
from tafs_pilot.tools.production import (
    assemble_video,
    audit_video,
    resolve_visuals,
    synthesize_voiceover,
)

project_id = "74ed7661"
artifact_dir = os.path.abspath(os.path.join("artifacts", project_id))

brief = CreatorBrief(
    topic="Why Senior Engineers Write Less Code Than Juniors",
    audience="Software engineers, tech leads, and developers",
    goal="Demonstrate that senior engineering impact comes from simplicity, code deletion, and preventing outages.",
    tone="Direct, authoritative, punchy, insightful",
    approximate_duration=21,
    platform="YouTube Shorts",
)

scenes = [
    ScenePlanItem(
        scene_id=1,
        scene_type="MG",
        visual_description="Terminal git diff showing 450 lines of legacy bloat deleted, with bold hero punch: 'THEY DELETE IT.'",
        narration_text="The best senior engineers don't write more code. They delete it.",
        estimated_duration=5.1,
    ),
    ScenePlanItem(
        scene_id=2,
        scene_type="DEMO",
        visual_description="High-contrast comparison cards: Junior Metric (+2,480 Lines Committed) vs Senior Metric (Problems Prevented: 100%).",
        narration_text="Juniors measure their value in lines of code committed. Seniors measure their value in problems prevented and systems simplified.",
        estimated_duration=8.6,
    ),
    ScenePlanItem(
        scene_id=3,
        scene_type="MG",
        visual_description="Terminal command execution 'tafs-pilot --simplify-architecture' with hero callout 'WHAT CAN I SIMPLIFY TODAY?'",
        narration_text="Before you write another line of code today, ask yourself: What can I simplify or delete right now?",
        estimated_duration=7.0,
    ),
]

plan = ProductionPlan(
    objective="Demonstrate that senior engineering value comes from simplicity and code deletion.",
    audience="Software engineers, tech leads, and developers",
    platform="YouTube Shorts",
    target_duration=21,
    tone="Direct, authoritative, punchy, insightful",
    hook_options=[
        "The best senior engineers don't write more code. They delete it.",
        "Juniors count lines committed. Seniors count problems prevented.",
        "The fastest code in production is the code you never wrote.",
    ],
    recommended_hook="The best senior engineers don't write more code. They delete it.",
    selected_angle="Counterintuitive senior engineering philosophy",
    scene_plan=scenes,
    success_criteria=[
        "Hook immediately challenges conventional developer productivity metrics within 3 seconds",
        "Clear visual contrast between code volume and system stability",
        "Actionable closing question urging simplicity and code reduction",
    ],
)

state = ProjectState(
    project_id=project_id,
    status=ProjectStatus.HOOK_APPROVED,
    brief=brief,
    production_plan=plan,
    artifact_dir=artifact_dir,
)

set_active_project_state(state)

print("=== 1. Synthesizing Voiceovers ===")
# Attempt Polly first via configured AWS credential chain
vo_res = synthesize_voiceover(provider="polly")
print("Voiceover result:", json.dumps(vo_res, indent=2))

print("\n=== 2. Resolving Visuals ===")
vis_res = resolve_visuals(provider="procedural")
print("Visuals result:", json.dumps(vis_res, indent=2))

print("\n=== 3. Assembling Final Deliverable ===")
asm_res = assemble_video()
print("Assembly result:", json.dumps(asm_res, indent=2))

print("\n=== 4. Running QC Audit ===")
qc_res = audit_video()
print("QC Audit result:", json.dumps(qc_res, indent=2))

# Also create final_defect.mp4 copy for the UI fast-forward if not already present
final_mp4 = os.path.join(artifact_dir, "final.mp4")
defect_mp4 = os.path.join(artifact_dir, "final_defect.mp4")
if os.path.exists(final_mp4):
    shutil.copy2(final_mp4, defect_mp4)
    print(f"\nCreated defect reference copy: {defect_mp4}")
