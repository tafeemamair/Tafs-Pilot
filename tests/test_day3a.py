"""Unit tests for Taf's Pilot Day 3A: Real AWS Smoke Test & Autonomous QC/Revision.

Covers:
1. AWS credential diagnostics (safe, secret-free)
2. Provider metadata (mode: 'aws' vs 'local_fallback')
3. Real/mock Polly result handling
4. Real/mock Bedrock result handling
5. Real/mock Titan result handling
6. QC failure state transition
7. Agent revision decision schema (RevisionRequest)
8. Revision execution (targeted regeneration & re-assembly)
9. Revision history in ProjectState
10. Maximum revision budget enforcement (MAX_REVISIONS = 2)
11. Successful PASS after revision
12. Unresolved failure after revision budget
13. Artifact integrity (directory structure & files)
14. Final MP4 QC verification
"""

import json
import os
from unittest.mock import MagicMock, patch
import pytest

from tafs_pilot.aws_diagnostics import run_aws_diagnostics
from tafs_pilot.media.assembly import assemble_production_video
from tafs_pilot.media.qc import inspect_video_deliverable
from tafs_pilot.models import (
    CreatorBrief,
    HookProposal,
    ProjectState,
    ProjectStatus,
    RevisionRequest,
    ScenePlanItem,
    VideoQCReport,
    VisualResult,
    VisualSceneResult,
    VoiceoverResult,
    VoiceoverSceneResult,
)
from tafs_pilot.tools.planning import set_active_project_state
from tafs_pilot.tools.production import (
    assemble_video,
    audit_video,
    resolve_visuals,
    revise_video,
    simulate_qc_defect,
    synthesize_voiceover,
)


@pytest.fixture
def active_state(tmp_path):
    brief = CreatorBrief(
        topic="SRE Post-Mortem Best Practices",
        audience="Tech leads and DevOps engineers",
        goal="Improve incident response culture",
        tone="Clear and authoritative",
        approximate_duration=20,
        platform="YouTube Shorts",
    )
    state = ProjectState(brief=brief)

    proposal = HookProposal(
        topic=brief.topic,
        hook_options=["Hook A", "Hook B", "Hook C"],
        recommended_hook="Hook A",
        selected_angle="Blameless post-mortems",
        reasoning="Emotional connection to on-call engineers",
    )
    state.transition_to_awaiting_approval(proposal)
    state.approve_hook("Hook A")

    scenes = [
        ScenePlanItem(
            scene_id=1,
            scene_type="CIN",
            visual_description="Engineer looking at red alert on screen.",
            narration_text="When production breaks, blameless culture saves teams.",
            estimated_duration=3.5,
        ),
        ScenePlanItem(
            scene_id=2,
            scene_type="MG",
            visual_description="3 rules for effective post-mortems.",
            narration_text="Focus on systemic prevention rather than human error.",
            estimated_duration=4.5,
        ),
    ]

    state.finalize_scene_plan(
        objective="Educate on post-mortem best practices.",
        scene_plan=scenes,
        success_criteria=["75% retention at 3s"],
    )

    return state


class TestAWSDiagnosticsAndTransparency:
    """1 & 2. Tests for safe diagnostics and provider transparency."""

    def test_aws_diagnostics_runs_without_credentials(self):
        with patch("tafs_pilot.config.check_aws_credentials", return_value=(False, "No credentials")):
            report = run_aws_diagnostics(region="us-east-1")
            assert report["credentials_available"] is False
            assert len(report["blockers"]) > 0
            assert "account_id" in report

    def test_provider_transparency_mode_in_schemas(self):
        vo_scene = VoiceoverSceneResult(
            scene_id=1,
            audio_path="test.mp3",
            duration=4.2,
            provider="polly",
            mode="aws",
        )
        assert vo_scene.mode == "aws"

        vis_scene = VisualSceneResult(
            scene_id=1,
            visual_path="test.mp4",
            provider="procedural",
            mode="local_fallback",
        )
        assert vis_scene.mode == "local_fallback"


class TestMockedAWSProviders:
    """3, 4, 5. Tests for Polly, Bedrock, and Titan result handling."""

    @patch("tafs_pilot.media.audio.check_aws_credentials")
    @patch("boto3.Session")
    def test_polly_aws_mode_result(self, mock_boto, mock_creds, tmp_path):
        mock_creds.return_value = (True, "AWS credentials found")
        mock_client = MagicMock()
        mock_boto.return_value.client.return_value = mock_client
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"\x00" * 500
        mock_client.synthesize_speech.return_value = {"AudioStream": mock_stream}

        scenes = [
            ScenePlanItem(
                scene_id=1,
                scene_type="CIN",
                visual_description="Visual shot",
                narration_text="Polly narration test line.",
                estimated_duration=3.0,
            )
        ]
        from tafs_pilot.media.audio import generate_scene_voiceovers

        with patch("tafs_pilot.media.audio.get_audio_duration", return_value=3.2):
            result = generate_scene_voiceovers(
                scenes=scenes,
                output_dir=str(tmp_path),
                provider="polly",
            )
            assert result.provider == "polly"
            assert result.mode == "aws"
            assert len(result.scenes) == 1
            assert result.scenes[0].mode == "aws"

    @patch("tafs_pilot.media.visuals.check_aws_credentials")
    @patch("boto3.Session")
    def test_titan_aws_mode_result(self, mock_boto, mock_creds, tmp_path):
        mock_creds.return_value = (True, "AWS credentials found")
        mock_runtime = MagicMock()
        mock_boto.return_value.client.return_value = mock_runtime

        # Mock Titan JSON response
        mock_body = MagicMock()
        # 1x1 transparent PNG base64
        fake_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        mock_body.read.return_value = json.dumps({"images": [fake_b64]}).encode()
        mock_runtime.invoke_model.return_value = {"body": mock_body}

        from tafs_pilot.media.visuals import generate_titan_image_bedrock

        out_img = str(tmp_path / "titan_test.png")
        path = generate_titan_image_bedrock(
            prompt="A futuristic server rack",
            output_path=out_img,
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


class TestAutonomousQCLoopAndRevision:
    """6, 7, 8, 9, 10, 11, 12. Tests for autonomous QC failure, agent revision, and budget."""

    def test_qc_failure_state_transition(self, active_state):
        set_active_project_state(active_state)
        # Synthesize & assemble initial deliverable
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()

        # Simulate defect (missing audio stream)
        defect = simulate_qc_defect(defect_type="missing_audio")
        assert defect["qc_status"] == "FAIL"
        assert active_state.status == ProjectStatus.REVISION_REQUIRED
        assert active_state.qc_report.status == "FAIL"

    def test_revision_request_schema_validation(self):
        req = RevisionRequest(
            revision_number=1,
            issues=["Missing active audio narration stream."],
            target_scene_ids=[1, 2],
            requested_change="regenerate_audio",
            reason="Restore audio track",
        )
        assert req.revision_number == 1
        assert req.requested_change == "regenerate_audio"

    def test_successful_revision_cycle_to_pass(self, active_state):
        """11. Tests the full cycle: FAIL -> revise_video -> PASS."""
        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()

        # Create known defect
        simulate_qc_defect(defect_type="missing_audio")
        assert active_state.status == ProjectStatus.REVISION_REQUIRED

        # Agent decides to execute revision
        rev_res = revise_video(
            feedback="Audio stream was missing from deliverable. Regenerating narration track.",
            target_scenes=[1, 2],
            requested_change="regenerate_audio",
            reason="Fix audio stream defect",
        )

        assert rev_res["status"] == "revision_completed"
        assert rev_res["revision_number"] == 1
        assert rev_res["new_qc_status"] == "PASS"
        assert active_state.status == ProjectStatus.READY_FOR_REVIEW
        assert active_state.revision_count == 1
        assert len(active_state.revision_history) == 1

    def test_revision_budget_enforcement(self, active_state):
        """10 & 12. Tests max revision budget (MAX_REVISIONS = 2)."""
        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()

        # Manually set revision count to maximum
        active_state.revision_count = 2

        rev_res = revise_video(
            feedback="Another revision attempt",
            requested_change="regenerate_audio",
        )

        assert rev_res["status"] == "budget_exhausted"
        assert active_state.status == ProjectStatus.REVISION_REQUIRED
        assert "exhausted" in rev_res["message"].lower()


class TestArtifactIntegrityAndFinalMP4:
    """13 & 14. Tests for artifact structure and final MP4 QC properties."""

    def test_artifact_directories_and_audit_history(self, active_state):
        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()
        audit_video()

        artifact_dir = active_state.artifact_dir
        for expected in ["audio", "visuals", "captions", "renders", "revisions"]:
            assert os.path.exists(os.path.join(artifact_dir, expected))

        qc_json = os.path.join(artifact_dir, "qc.json")
        audit_history_json = os.path.join(artifact_dir, "audit_history.json")
        assert os.path.exists(qc_json)
        assert os.path.exists(audit_history_json)

        history_data = json.load(open(audit_history_json, encoding="utf-8"))
        assert len(history_data) >= 1
        assert history_data[0]["status"] == "PASS"

    def test_final_mp4_ffprobe_properties(self, active_state):
        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()

        qc = inspect_video_deliverable(active_state.final_video_path)
        assert qc.status == "PASS"
        assert qc.width == 1080
        assert qc.height == 1920
        assert qc.duration > 0
        assert qc.has_video_stream is True
        assert qc.has_audio_stream is True
        assert qc.file_size_bytes > 5000


class TestAgenticQCOrchestration:
    """Tests proving that the Strands Agent orchestrates the revision decision and persists decision evidence."""

    def test_strands_agent_qc_revision_orchestration(self, active_state):
        from tafs_pilot.agent import run_agent_qc_revision

        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()
        audit_video()

        # Simulate defect
        defect = simulate_qc_defect(defect_type="missing_audio")
        assert defect["qc_status"] == "FAIL"

        # Dispatch structured QC report to the Strands Agent
        agent_res, updated_state = run_agent_qc_revision(
            qc_report=active_state.qc_report,
            project_state=active_state,
        )

        assert agent_res.stop_reason == "end_turn"
        assert updated_state.status == ProjectStatus.READY_FOR_REVIEW
        assert updated_state.revision_count == 1
        assert updated_state.qc_report.status == "PASS"

    def test_agent_decision_evidence_persisted(self, active_state):
        from tafs_pilot.agent import run_agent_qc_revision

        set_active_project_state(active_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()
        audit_video()

        simulate_qc_defect(defect_type="missing_audio")
        run_agent_qc_revision(
            qc_report=active_state.qc_report,
            project_state=active_state,
        )

        decision_path = os.path.join(active_state.artifact_dir, "revision_decision.json")
        assert os.path.exists(decision_path)
        assert os.path.getsize(decision_path) > 0

        with open(decision_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["revision_number"] == 1
        assert "audio" in data["qc_issue"].lower()
        assert data["agent_decision"] == "regenerate_audio"
        assert data["tool_called"] == "revise_video"
        assert len(data["reason"]) > 0
        assert data["result"] == "success"

