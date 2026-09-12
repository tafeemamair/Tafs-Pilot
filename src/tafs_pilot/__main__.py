"""Main executable entry point for Taf's Pilot.

Demonstrates the complete end-to-end autonomous video production pipeline:
Brief → Hook Formulation → Human Approval → Scene Planning → Voiceover →
Visual Resolution → Video Assembly → Subtitle Burning → Quality Control (QC).

Can be run via:
    python -m tafs_pilot
"""

import argparse
import os
import sys
import json
from tafs_pilot.agent import (
    create_tafs_pilot_agent,
    discover_available_bedrock_models,
    run_agent_qc_revision,
    run_producer_workflow,
)
from tafs_pilot.config import (
    check_aws_credentials,
    get_configured_aws_region,
    get_configured_bedrock_model_id,
)
from tafs_pilot.models import CreatorBrief, ProjectState, ProjectStatus
from tafs_pilot.tools.planning import (
    finalize_scene_plan,
    request_hook_approval,
    set_active_project_state,
    set_hook_approval_callback,
)
from tafs_pilot.tools.production import (
    assemble_video,
    audit_video,
    resolve_visuals,
    revise_video,
    synthesize_voiceover,
)


def get_demo_brief() -> CreatorBrief:
    """Returns a realistic professional video brief for demonstration."""
    return CreatorBrief(
        topic="Why Senior Engineers Write Less Code Than Juniors",
        audience="Mid-level software engineers and tech leads aiming for staff/principal roles",
        goal="Establish thought leadership and drive retention for an engineering career series",
        tone="Insightful, counter-intuitive, and authoritative",
        approximate_duration=25,
        platform="YouTube Shorts",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Taf's Pilot - Autonomous Video Production Agent (Professional Agents Track)"
    )
    parser.add_argument("--topic", type=str, help="Video topic or subject matter")
    parser.add_argument("--audience", type=str, help="Target audience description")
    parser.add_argument("--goal", type=str, help="Primary business or engagement goal")
    parser.add_argument("--tone", type=str, help="Aesthetic and delivery tone")
    parser.add_argument("--duration", type=int, help="Approximate target duration in seconds")
    parser.add_argument("--platform", type=str, help="Target distribution platform")
    parser.add_argument("--interactive", action="store_true", help="Prompt user interactively for hook approval")
    parser.add_argument("--voiceover-provider", type=str, default="procedural", help="Voiceover provider: 'polly' or 'procedural'")
    parser.add_argument("--visual-provider", type=str, default="procedural", help="Visual provider: 'titan' or 'procedural'")
    parser.add_argument("--web", action="store_true", help="Launch the Taf's Pilot web production console")
    parser.add_argument("--port", type=int, default=8000, help="Web console port (default: 8000)")
    parser.add_argument("--open", action="store_true", help="Automatically open browser when launching web console")
    args = parser.parse_args()

    if args.web:
        from tafs_pilot.web.server import run_server
        run_server(port=args.port, open_browser=args.open)
        return

    print("=" * 72)
    print("  TAF'S PILOT - Autonomous Video Production Agent")
    print("  Amazon Agents for Humans Hackathon | Professional Agents Track")
    print("  Powered by Amazon Strands Agents SDK + Amazon Bedrock + FFmpeg")
    print("=" * 72)

    if args.topic:
        brief = CreatorBrief(
            topic=args.topic,
            audience=args.audience or "General professional audience",
            goal=args.goal or "Viewer education and engagement",
            tone=args.tone or "Engaging and clear",
            approximate_duration=args.duration or 30,
            platform=args.platform or "YouTube Shorts",
        )
        print("\n[INFO] Loaded custom brief from CLI arguments.")
    else:
        brief = get_demo_brief()
        print("\n[INFO] No CLI brief provided. Running verified professional demo brief.")

    print("\n--- CREATOR BRIEF ---")
    print(f"  Topic:      {brief.topic}")
    print(f"  Audience:   {brief.audience}")
    print(f"  Goal:       {brief.goal}")
    print(f"  Tone:       {brief.tone}")
    print(f"  Duration:   ~{brief.approximate_duration} seconds")
    print(f"  Platform:   {brief.platform}")
    print("-" * 22)

    region = get_configured_aws_region()
    configured_model = get_configured_bedrock_model_id()
    has_creds, cred_message = check_aws_credentials()

    print(f"\n[AWS BEDROCK CONFIGURATION]")
    print(f"  Region:               {region}")
    print(f"  Configured Model ID:  {configured_model or '(Auto-discovery / default)'}")
    print(f"  Credential State:     {cred_message}")

    # PART 1: AWS Environment Diagnostics
    from tafs_pilot.aws_diagnostics import run_aws_diagnostics
    from tafs_pilot.tools.production import simulate_qc_defect
    from tafs_pilot.media.qc import inspect_video_deliverable

    diag = run_aws_diagnostics()
    print("\n--- AWS ENVIRONMENT DIAGNOSTICS ---")
    print(f"  Region:                 {diag['region']}")
    print(f"  Credentials Available:  {diag['credentials_available']}")
    print(f"  Credential Source:      {diag['credential_source']}")
    print(f"  Bedrock Accessible:     {diag['bedrock_accessible']} ({len(diag['bedrock_models'])} active models)")
    print(f"  Polly Accessible:       {diag['polly_accessible']}")
    print(f"  Titan Image Accessible: {diag['titan_image_accessible']}")
    if diag["blockers"]:
        print("  Diagnostic Notes / Blockers:")
        for b in diag["blockers"]:
            print(f"    * {b}")
    print("-" * 35)

    project_state = ProjectState(brief=brief)
    set_active_project_state(project_state)

    if not has_creds:
        print("\n" + "!" * 72)
        print("  NOTICE: RUNNING IN HONEST LOCAL FALLBACK MODE")
        print("!" * 72)
        print("\n  AWS credentials are not configured in the current shell/environment.")
        print("  In accordance with hackathon integrity guidelines, no fake AWS calls are made.")
        print("  Running with genuine local media engines and full provider transparency.")
        print("=" * 72)

        # 1. Hook Proposal
        print("\n[STEP 1: HOOK FORMULATION]")
        hook_result = request_hook_approval(
            topic=brief.topic,
            hook_options=[
                "The best senior engineers don't write more code. They delete it.",
                "Why 10x engineers commit 90% less code than juniors.",
                "Stop measuring your developer productivity in GitHub green squares.",
            ],
            recommended_hook="The best senior engineers don't write more code. They delete it.",
            selected_angle="Architectural leverage and problem prevention beat raw code volume.",
            reasoning="Directly hits the counter-intuitive curiosity of mid-level engineers.",
        )
        print(f"  Status: {hook_result['status']}")
        print(f"  State:  {project_state.status.value}")

        # 2. Human Approval Gate
        print("\n[STEP 2: HUMAN-IN-THE-LOOP APPROVAL GATE]")
        chosen_hook = hook_result["hook_options"][0]
        project_state.approve_hook(chosen_hook, notes="Creator approved Hook #1 via review gate.")
        print(f"  Approved: '{chosen_hook}'")
        print(f"  State:    {project_state.status.value}")

        # 3. Scene Planning
        print("\n[STEP 3: SCENE PLANNING FROM APPROVED HOOK]")
        demo_scenes = [
            {
                "scene_id": 1,
                "scene_type": "CIN",
                "visual_description": "Close up of an engineer looking thoughtfully at an empty IDE editor.",
                "narration_text": chosen_hook,
                "estimated_duration": 4.5,
            },
            {
                "scene_id": 2,
                "scene_type": "MG",
                "visual_description": "Kinetic typography comparing junior code volume vs senior architectural impact.",
                "narration_text": "Junior developers measure progress in lines committed. Seniors measure progress in problems prevented.",
                "estimated_duration": 7.0,
            },
            {
                "scene_id": 3,
                "scene_type": "MG",
                "visual_description": "Diagram of architectural leverage and systemic simplification.",
                "narration_text": "Before you write another thousand lines of glue code, ask yourself: what can I simplify today?",
                "estimated_duration": 6.5,
            },
        ]
        scene_result = finalize_scene_plan(
            selected_hook=chosen_hook,
            objective="Deliver career guidance positioning engineering simplicity over raw code output.",
            scene_plan=demo_scenes,
            success_criteria=[
                "Hook retention exceeds 70% at 3-second mark",
                "Total runtime matches vertical deliverable",
                "Clear, actionable takeaway for engineering leads",
            ],
        )
        print(f"  Status: {scene_result['status']}")
        print(f"  State:  {project_state.status.value}")

        # 4. Voiceover Synthesis
        print("\n[STEP 4: VOICEOVER SYNTHESIS]")
        vo_res = synthesize_voiceover(provider=args.voiceover_provider)
        print(f"  Provider:       {vo_res['provider']} (mode: {vo_res.get('mode', 'local_fallback')})")
        print(f"  Total Duration: {vo_res['total_duration']:.2f}s")
        for s in vo_res.get("scenes", []):
            print(f"    Scene {s['scene_id']}: {s['duration']:.2f}s [{s.get('mode', 'local_fallback')}] -> {s['audio_path']}")
        print(f"  State:          {project_state.status.value}")

        # 5. Visual Resolution
        print("\n[STEP 5: VISUAL RESOLUTION / GENERATION]")
        vis_res = resolve_visuals(provider=args.visual_provider)
        print(f"  Provider: {vis_res['provider']} (mode: {vis_res.get('mode', 'local_fallback')})")
        for s in vis_res.get("scenes", []):
            print(f"    Scene {s['scene_id']}: [{s.get('mode', 'local_fallback')}] {s['visual_path']}")

        # 6. Assembly & Captioning
        print("\n[STEP 6: REAL VIDEO ASSEMBLY & SUBTITLE COMPOSITING]")
        asm_res = assemble_video()
        final_mp4 = asm_res["final_video_path"]
        print(f"  Assembly Status: {asm_res['status']}")
        print(f"  Initial MP4:     {final_mp4}")
        print(f"  File Size:       {os.path.getsize(final_mp4):,} bytes")
        print(f"  State:           {project_state.status.value}")

        # 7. Initial Quality Control Inspection
        print("\n[STEP 7: QUALITY CONTROL (QC) INSPECTION #1]")
        qc_res = audit_video()
        report = qc_res["report"]
        print(f"  QC Status:       {report['status']}")
        print(f"  Duration:        {report['duration']:.2f}s")
        print(f"  Resolution:      {report['width']}x{report['height']}")
        print(f"  Video Stream:    {report['has_video_stream']} ({report.get('metrics', {}).get('video_codec')})")
        print(f"  Audio Stream:    {report['has_audio_stream']} ({report.get('metrics', {}).get('audio_codec')})")
        print(f"  State:           {project_state.status.value}")

        # 8. Deterministic QC Defect Simulation & Autonomous Revision Demonstration
        print("\n[STEP 8: AUTONOMOUS QC FAILURE & REVISION DEMONSTRATION]")
        print("  Simulating production defect: intentional audio track removal...")
        defect = simulate_qc_defect(defect_type="missing_audio")
        print(f"  Post-Defect QC Status: {defect['qc_status']}")
        print(f"  State Transition:      {project_state.status.value}")
        print(f"  Reported Defect:       {defect['issues']}")

        print("\n  [STRANDS AGENT QC REVISION ORCHESTRATION]")
        print("  Dispatching structured QC report to the Strands Agent for autonomous diagnosis...")
        agent_result, updated_state = run_agent_qc_revision(
            qc_report=project_state.qc_report,
            project_state=project_state,
        )
        print(f"  Strands Agent Stop Reason: {agent_result.stop_reason}")
        print(f"  Revision Count:            {project_state.revision_count}/{project_state.max_revisions}")
        print(f"  Post-Revision QC Status:   {project_state.qc_report.status}")
        print(f"  Final Project State:       {project_state.status.value}")

        # Check and print persisted Agent Decision Evidence (Section 7)
        decision_path = os.path.join(project_state.artifact_dir, "revision_decision.json")
        if os.path.exists(decision_path):
            with open(decision_path, "r", encoding="utf-8") as f:
                decision_data = json.load(f)
            print("\n  [AGENT DECISION EVIDENCE (revision_decision.json)]")
            print(f"    Revision Number:  #{decision_data.get('revision_number')}")
            print(f"    QC Issue:         {decision_data.get('qc_issue')}")
            print(f"    Agent Decision:   {decision_data.get('agent_decision')}")
            print(f"    Tool Called:      {decision_data.get('tool_called')}")
            print(f"    Reason:           {decision_data.get('reason')}")
            print(f"    Result:           {decision_data.get('result')}")

        # 9. Final Deliverable Inspection
        final_deliverable = project_state.final_video_path
        final_qc = inspect_video_deliverable(final_deliverable, target_duration=float(project_state.production_plan.target_duration))

        print("\n" + "=" * 72)
        print("  DAY 3A AUTONOMOUS QC & REVISION MILESTONE COMPLETE")
        print("=" * 72)
        print(f"  Final Deliverable:     {final_deliverable}")
        print(f"  Deliverable Exists:    {os.path.exists(final_deliverable)}")
        print(f"  File Size:             {os.path.getsize(final_deliverable):,} bytes")
        print(f"  Duration:              {final_qc.duration:.2f} seconds")
        print(f"  Resolution:            {final_qc.width}x{final_qc.height}")
        print(f"  Video Codec:           {final_qc.metrics.get('video_codec', 'unknown')}")
        print(f"  Audio Codec:           {final_qc.metrics.get('audio_codec', 'unknown')}")
        print(f"  QC Status:             {final_qc.status}")
        print(f"  Revision Count:        {project_state.revision_count}")
        print(f"  Audit History Entries: {len(project_state.audit_history)}")
        print(f"  Audit Log Path:        {os.path.join(project_state.artifact_dir, 'audit_history.json')}")
        print("=" * 72)
        return

    # Live Bedrock + AWS Polly / Titan Execution
    print("\n[STARTING AGENT] Initializing Strands producer agent with Amazon Bedrock...")
    try:
        agent = create_tafs_pilot_agent()

        if args.interactive:
            def interactive_callback(proposal):
                print("\n" + "=" * 50)
                print("  CREATOR REVIEW GATEWAY: SELECT YOUR OPENING HOOK")
                print("=" * 50)
                for i, h in enumerate(proposal.hook_options, 1):
                    rec = " [RECOMMENDED]" if h == proposal.recommended_hook else ""
                    print(f"  [{i}] {h}{rec}")
                choice = input("\nSelect hook (1-3) or press Enter for recommended: ").strip()
                if choice in {"1", "2", "3"}:
                    selected = proposal.hook_options[int(choice) - 1]
                else:
                    selected = proposal.recommended_hook
                return selected, "Selected via interactive CLI"

            set_hook_approval_callback(interactive_callback)

        response, final_state = run_producer_workflow(brief, agent=agent, project_state=project_state)
        print("\n=== AGENT RESPONSE ===")
        print(response)
        print("======================")
        print(f"\nFinal Project State: {final_state.status.value}")

    except Exception as e:
        print(f"\n[ERROR] Failed during agent execution: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
