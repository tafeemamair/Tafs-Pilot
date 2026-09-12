"""Unit tests for Taf's Pilot Day 2 Real Media Production Pipeline.

Tests:
1. Voiceover result schema & duration propagation
2. Visual result schema & asset resolution
3. Artifact path handling & subdirectories
4. Assembly configuration & subtitle formatting
5. QC result parsing & ffprobe inspection
6. Invalid/missing media handling
7. State transitions across production, auditing, and revision
8. Mocked AWS generation
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from tafs_pilot.media.assembly import create_scene_srt, format_srt_timestamp
from tafs_pilot.media.audio import generate_procedural_speech_wav, get_audio_duration
from tafs_pilot.media.qc import inspect_video_deliverable
from tafs_pilot.media.visuals import render_procedural_scene_clip
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
    synthesize_voiceover,
)


@pytest.fixture
def test_project_state(tmp_path):
    brief = CreatorBrief(
        topic="Modern Incident Management",
        audience="DevOps and SRE leaders",
        goal="Post-mortem cultural adoption",
        tone="Pragmatic",
        approximate_duration=30,
        platform="YouTube Shorts",
    )
    state = ProjectState(brief=brief)

    # Set up approved hook and finalized scene plan
    proposal = HookProposal(
        topic=brief.topic,
        hook_options=["Hook 1", "Hook 2", "Hook 3"],
        recommended_hook="Hook 1",
        selected_angle="Actionable protocol",
        reasoning="Emotional pain point",
    )
    state.transition_to_awaiting_approval(proposal)
    state.approve_hook("Hook 1")

    scenes = [
        ScenePlanItem(
            scene_id=1,
            scene_type="CIN",
            visual_description="Server rack with blinking alert lights.",
            narration_text="When production goes down, every second counts.",
            estimated_duration=3.5,
        ),
        ScenePlanItem(
            scene_id=2,
            scene_type="MG",
            visual_description="Kinetic typography displaying incident triage rules.",
            narration_text="Follow the 3-minute triage rule to isolate the root cause.",
            estimated_duration=4.5,
        ),
    ]

    state.finalize_scene_plan(
        objective="Educate SREs on rapid incident triage.",
        scene_plan=scenes,
        success_criteria=["70% 3-second hook retention"],
    )

    return state


class TestVoiceoverSynthesis:
    """1. Tests for voiceover generation schema, duration propagation, and mocked AWS Polly."""

    def test_procedural_audio_generation(self, tmp_path):
        out_wav = str(tmp_path / "test_speech.wav")
        duration = generate_procedural_speech_wav(
            text="Testing procedural voiceover generation for Taf's Pilot.",
            output_path=out_wav,
            target_duration=3.0,
        )
        assert os.path.exists(out_wav)
        assert duration >= 2.5
        measured = get_audio_duration(out_wav)
        assert abs(measured - duration) < 0.1

    def test_synthesize_voiceover_tool_execution(self, test_project_state):
        set_active_project_state(test_project_state)
        result = synthesize_voiceover(provider="procedural")

        assert result["status"] == "success"
        assert result["provider"] == "procedural"
        assert len(result["scenes"]) == 2
        assert test_project_state.status == ProjectStatus.PRODUCING
        assert test_project_state.voiceover_result is not None
        assert test_project_state.voiceover_result.total_duration > 0

    @patch("tafs_pilot.media.audio.check_aws_credentials")
    @patch("boto3.Session")
    def test_mocked_aws_polly_generation(self, mock_boto, mock_creds, tmp_path):
        mock_creds.return_value = (True, "AWS credentials found")
        mock_client = MagicMock()
        mock_boto.return_value.client.return_value = mock_client

        # Mock Polly response stream
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"\x00" * 1000
        mock_client.synthesize_speech.return_value = {"AudioStream": mock_stream}

        from tafs_pilot.media.audio import synthesize_polly_audio

        out_mp3 = str(tmp_path / "polly_test.mp3")
        with patch("tafs_pilot.media.audio.get_audio_duration", return_value=4.2):
            duration = synthesize_polly_audio(
                text="Polly speech test",
                output_path=out_mp3,
                voice_id="Danielle",
            )
            assert duration == 4.2
            assert os.path.exists(out_mp3)


class TestVisualResolution:
    """2. Tests for visual asset resolution and schema validation."""

    def test_procedural_clip_generation(self, tmp_path):
        out_clip = str(tmp_path / "test_visual.mp4")
        scene = ScenePlanItem(
            scene_id=1,
            scene_type="MG",
            visual_description="Kinetic typography background.",
            narration_text="Sample text",
            estimated_duration=2.0,
        )
        rendered = render_procedural_scene_clip(scene, out_clip, duration=2.0)
        assert os.path.exists(rendered)
        assert os.path.getsize(rendered) > 1000

    def test_resolve_visuals_tool_execution(self, test_project_state):
        set_active_project_state(test_project_state)
        result = resolve_visuals(provider="procedural")

        assert result["status"] == "success"
        assert len(result["scenes"]) == 2
        assert test_project_state.visual_result is not None
        assert os.path.exists(result["scenes"][0]["visual_path"])


class TestArtifactPathHandling:
    """3. Tests for project artifact directories and layout isolation."""

    def test_project_artifact_directory_layout(self, test_project_state):
        artifact_dir = test_project_state.artifact_dir
        assert os.path.exists(artifact_dir)
        assert test_project_state.project_id in artifact_dir


class TestAssemblyAndSubtitles:
    """4. Tests for subtitle formatting, timestamp conversion, and assembly configuration."""

    def test_format_srt_timestamp(self):
        assert format_srt_timestamp(0.0) == "00:00:00,000"
        assert format_srt_timestamp(4.5) == "00:00:04,500"
        assert format_srt_timestamp(65.123) == "00:01:05,123"

    def test_create_scene_srt(self, tmp_path):
        scene = ScenePlanItem(
            scene_id=1,
            scene_type="CIN",
            visual_description="Visual shot",
            narration_text="When production breaks, act quickly.",
            estimated_duration=4.0,
        )
        srt_file = str(tmp_path / "test.srt")
        create_scene_srt(scene, 4.0, srt_file)
        assert os.path.exists(srt_file)
        content = open(srt_file, encoding="utf-8").read()
        assert "00:00:00,000 --> 00:00:04,000" in content
        assert "When production breaks, act quickly." in content

    def test_assemble_video_end_to_end(self, test_project_state):
        set_active_project_state(test_project_state)
        # 1. Synthesize audio
        synthesize_voiceover(provider="procedural")
        # 2. Resolve visuals
        resolve_visuals(provider="procedural")
        # 3. Assemble final deliverable
        res = assemble_video()

        assert res["status"] == "success"
        final_mp4 = res["final_video_path"]
        assert os.path.exists(final_mp4)
        assert os.path.getsize(final_mp4) > 5000
        assert test_project_state.status == ProjectStatus.AUDITING


class TestQualityControlAndInspection:
    """5 & 6. Tests for ffprobe QC inspection, report parsing, and missing media handling."""

    def test_audit_video_on_valid_deliverable(self, test_project_state):
        set_active_project_state(test_project_state)
        synthesize_voiceover(provider="procedural")
        resolve_visuals(provider="procedural")
        assemble_video()

        res = audit_video()
        assert res["status"] == "success"
        assert res["qc_status"] == "PASS"

        report = test_project_state.qc_report
        assert report is not None
        assert report.status == "PASS"
        assert report.has_video_stream is True
        assert report.has_audio_stream is True
        assert report.width == 1080
        assert report.height == 1920
        assert test_project_state.status == ProjectStatus.READY_FOR_REVIEW

    def test_audit_missing_file_reports_failure(self):
        report = inspect_video_deliverable("non_existent_file.mp4")
        assert report.status == "FAIL"
        assert "does not exist" in report.issues[0]


class TestAutonomousRevisionHook:
    """7. Tests for revision initiation and state transitions."""

    def test_revise_video_state_transition(self, test_project_state):
        set_active_project_state(test_project_state)
        test_project_state.status = ProjectStatus.REVISION_REQUIRED

        rev_res = revise_video(
            feedback="Hook pacing is too slow in Scene 1; tighten voiceover delivery.",
            target_scenes=[1],
            action="adjust_scenes",
        )

        assert rev_res["status"] == "revision_initiated"
        assert test_project_state.status == ProjectStatus.REVISION_IN_PROGRESS
        assert len(test_project_state.revision_history) == 1
        assert test_project_state.revision_history[0].target_scene_ids == [1]
