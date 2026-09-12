"""Unit tests for Taf's Pilot planning models and Strands tools.

Tests Pydantic validation, schema normalization, and tool execution.
"""

import pytest
from pydantic import ValidationError
from tafs_pilot.agent import check_aws_credentials, get_configured_aws_region
from tafs_pilot.models import CreatorBrief, ProductionPlan, ScenePlanItem
from tafs_pilot.tools.planning import create_production_plan


class TestCreatorBrief:
    """Tests for the CreatorBrief schema."""

    def test_valid_brief_creation(self):
        brief = CreatorBrief(
            topic="Effective SRE Incident Management",
            audience="DevOps engineers and reliability leaders",
            goal="Promote post-mortem culture best practices",
            tone="Urgent yet pragmatic",
            approximate_duration=60,
            platform="YouTube Shorts",
        )
        assert brief.topic == "Effective SRE Incident Management"
        assert brief.approximate_duration == 60
        assert brief.platform == "YouTube Shorts"

    def test_invalid_duration_rejected(self):
        with pytest.raises(ValidationError):
            CreatorBrief(
                topic="Shorts test",
                audience="Developers",
                goal="Education",
                approximate_duration=5,  # Below 10 second minimum
            )

    def test_empty_topic_rejected(self):
        with pytest.raises(ValidationError):
            CreatorBrief(
                topic="",
                audience="Developers",
                goal="Education",
            )


class TestScenePlanItem:
    """Tests for individual scene specifications."""

    def test_valid_scene_normalization(self):
        scene = ScenePlanItem(
            scene_id=1,
            scene_type="cin",  # Lowercase should be normalized to CIN
            visual_description="Cinematic shot of a monitor showing server graphs.",
            narration_text="When production goes down, seconds feel like hours.",
            estimated_duration=3.5,
        )
        assert scene.scene_type == "CIN"
        assert scene.scene_id == 1
        assert scene.estimated_duration == 3.5

    def test_invalid_scene_duration(self):
        with pytest.raises(ValidationError):
            ScenePlanItem(
                scene_id=1,
                scene_type="MG",
                visual_description="Animated diagram.",
                narration_text="Quick text beat.",
                estimated_duration=0.0,  # Must be > 0
            )


class TestProductionPlan:
    """Tests for the complete ProductionPlan schema."""

    @pytest.fixture
    def sample_scenes(self):
        return [
            ScenePlanItem(
                scene_id=1,
                scene_type="CIN",
                visual_description="Developer staring at terminal alert.",
                narration_text="Your database is locked. What do you do first?",
                estimated_duration=3.0,
            ),
            ScenePlanItem(
                scene_id=2,
                scene_type="MG",
                visual_description="3-step triage checklist animating on screen.",
                narration_text="Never restart blindly. Here is the 3-step triage rule.",
                estimated_duration=5.0,
            ),
        ]

    def test_valid_production_plan(self, sample_scenes):
        plan = ProductionPlan(
            objective="Educate on incident triage protocols without panic.",
            audience="Software engineers on-call",
            platform="LinkedIn Video",
            target_duration=45,
            tone="Pragmatic and calm",
            hook_options=[
                "Your database is locked. What do you do first?",
                "Stop restarting servers blindly during an outage.",
                "The 3-minute rule that saves production systems.",
            ],
            recommended_hook="Your database is locked. What do you do first?",
            selected_angle="Actionable protocol beats panic.",
            scene_plan=sample_scenes,
            success_criteria=["Retain 65% viewers at 5s mark", "Direct comment discussions"],
        )
        assert len(plan.hook_options) >= 3
        assert plan.recommended_hook in plan.hook_options
        assert len(plan.scene_plan) == 2

    def test_fewer_than_three_hooks_rejected(self, sample_scenes):
        with pytest.raises(ValidationError):
            ProductionPlan(
                objective="Objective here",
                audience="Audience here",
                platform="YouTube Shorts",
                target_duration=30,
                tone="Clear",
                hook_options=["Only one hook", "Second hook"],  # Requires at least 3
                recommended_hook="Only one hook",
                selected_angle="Angle",
                scene_plan=sample_scenes,
                success_criteria=["Benchmark 1"],
            )

    def test_empty_scenes_rejected(self):
        with pytest.raises(ValidationError):
            ProductionPlan(
                objective="Objective here",
                audience="Audience here",
                platform="YouTube Shorts",
                target_duration=30,
                tone="Clear",
                hook_options=["Hook 1", "Hook 2", "Hook 3"],
                recommended_hook="Hook 1",
                selected_angle="Angle",
                scene_plan=[],  # Empty scenes list rejected
                success_criteria=["Benchmark 1"],
            )


class TestPlanningTool:
    """Tests for the Strands create_production_plan tool execution."""

    def test_tool_successful_execution(self):
        result = create_production_plan(
            objective="Deliver clear guidance on writing cleaner unit tests.",
            audience="Junior developers",
            platform="YouTube Shorts",
            target_duration=45,
            tone="Friendly and instructive",
            hook_options=[
                "If your test is 100 lines long, it's not a unit test.",
                "Why 90% of developers write unit tests wrong.",
                "The Arrange-Act-Assert secret for bulletproof code.",
            ],
            recommended_hook="If your test is 100 lines long, it's not a unit test.",
            selected_angle="Test clarity over complexity.",
            scene_plan=[
                {
                    "scene_id": 1,
                    "scene_type": "CIN",
                    "visual_description": "Frustrated coder squinting at a massive test file.",
                    "narration_text": "If your test is 100 lines long, it's not a unit test.",
                    "estimated_duration": 4.0,
                },
                {
                    "scene_id": 2,
                    "scene_type": "MG",
                    "visual_description": "Code snippet showing Arrange, Act, and Assert clearly partitioned.",
                    "narration_text": "Use the AAA pattern: Arrange your data, Act on the method, Assert the outcome.",
                    "estimated_duration": 6.5,
                },
            ],
            success_criteria=["Viewer retention above 70%", "Code snippet legibility in vertical format"],
        )

        assert result["status"] == "success"
        assert "plan" in result
        plan = result["plan"]
        assert plan["target_duration"] == 45
        assert len(plan["hook_options"]) == 3
        assert len(plan["scene_plan"]) == 2

    def test_tool_validation_error_handling(self):
        # Pass fewer than 3 hooks to trigger schema validation
        result = create_production_plan(
            objective="Short",
            audience="Audience",
            platform="Shorts",
            target_duration=30,
            tone="Direct",
            hook_options=["Hook 1", "Hook 2"],  # Invalid (< 3)
            recommended_hook="Hook 1",
            selected_angle="Angle",
            scene_plan=[
                {
                    "scene_id": 1,
                    "scene_type": "MG",
                    "visual_description": "Visual",
                    "narration_text": "Line",
                    "estimated_duration": 5.0,
                }
            ],
            success_criteria=["Criteria 1"],
        )

        assert result["status"] == "error"
        assert "validation error" in result["message"].lower()


class TestAgentConfiguration:
    """Tests for agent configuration helpers."""

    def test_aws_region_resolution(self):
        region = get_configured_aws_region()
        assert isinstance(region, str)
        assert len(region) > 0

    def test_check_aws_credentials_runs_safely(self):
        has_creds, msg = check_aws_credentials()
        assert isinstance(has_creds, bool)
        assert isinstance(msg, str)
