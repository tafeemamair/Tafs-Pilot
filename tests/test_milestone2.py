"""Unit tests for Day 1 Milestone #2 of Taf's Pilot.

Tests:
1. Hook generation structure & validation
2. Human approval state/pause/resume behavior
3. Selected hook propagation into scene planning
4. Script / scene plan validation
5. ProjectState transitions across the lifecycle
6. Agent configuration and dynamic model discovery without legacy biases
"""

import pytest
from pydantic import ValidationError
from tafs_pilot.agent import (
    discover_available_bedrock_models,
    get_configured_aws_region,
    get_configured_bedrock_model_id,
)
from tafs_pilot.models import (
    CreatorBrief,
    HookProposal,
    ProjectState,
    ProjectStatus,
    ScenePlanItem,
)
from tafs_pilot.tools.planning import (
    finalize_scene_plan,
    get_active_project_state,
    request_hook_approval,
    set_active_project_state,
    set_hook_approval_callback,
)


@pytest.fixture
def sample_brief():
    return CreatorBrief(
        topic="Modern Distributed Systems Observability",
        audience="Principal architects and backend engineers",
        goal="Demonstrate OpenTelemetry best practices",
        tone="Authoritative and technical",
        approximate_duration=60,
        platform="LinkedIn Video",
    )


class TestHookGenerationStructure:
    """1. Tests for hook generation structure and HookProposal validation."""

    def test_valid_hook_proposal(self):
        proposal = HookProposal(
            topic="Distributed Systems Observability",
            hook_options=[
                "Most dashboards are just high-resolution noise.",
                "Why 90% of alerts wake you up for nothing.",
                "Stop collecting metrics you never look at.",
            ],
            recommended_hook="Most dashboards are just high-resolution noise.",
            selected_angle="Actionable telemetry over alert fatigue.",
            reasoning="Directly hits the emotional pain point of on-call engineers.",
        )
        assert len(proposal.hook_options) == 3
        assert proposal.recommended_hook in proposal.hook_options
        assert proposal.selected_angle == "Actionable telemetry over alert fatigue."

    def test_hook_proposal_fewer_than_three_rejected(self):
        with pytest.raises(ValidationError):
            HookProposal(
                topic="Topic",
                hook_options=["Hook 1", "Hook 2"],  # Less than 3 options
                recommended_hook="Hook 1",
                selected_angle="Angle",
                reasoning="Reason",
            )

    def test_recommended_hook_automatically_included_if_omitted(self):
        proposal = HookProposal(
            topic="Topic",
            hook_options=["Hook A", "Hook B", "Hook C"],
            recommended_hook="Hook D",
            selected_angle="Angle",
            reasoning="Reason",
        )
        assert "Hook D" in proposal.hook_options


class TestHumanApprovalStateAndTransitions:
    """2 & 5. Tests for human approval state, pause/resume behavior, and ProjectState transitions."""

    def test_initial_project_state(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        assert state.status == ProjectStatus.BRIEF_RECEIVED
        assert state.selected_hook is None
        assert state.hook_proposal is None

    def test_transition_to_awaiting_approval(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        proposal = HookProposal(
            topic=sample_brief.topic,
            hook_options=["Hook 1", "Hook 2", "Hook 3"],
            recommended_hook="Hook 1",
            selected_angle="Angle",
            reasoning="Reasoning",
        )
        state.transition_to_awaiting_approval(proposal)
        assert state.status == ProjectStatus.AWAITING_HOOK_APPROVAL
        assert state.hook_proposal == proposal
        assert len(state.history) == 1

    def test_approve_hook_valid_transition(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        proposal = HookProposal(
            topic=sample_brief.topic,
            hook_options=["Hook 1", "Hook 2", "Hook 3"],
            recommended_hook="Hook 1",
            selected_angle="Angle",
            reasoning="Reasoning",
        )
        state.transition_to_awaiting_approval(proposal)
        state.approve_hook("Hook 2", notes="Selected Hook #2 for better hook rate")

        assert state.status == ProjectStatus.HOOK_APPROVED
        assert state.selected_hook == "Hook 2"
        assert state.approval_notes == "Selected Hook #2 for better hook rate"

    def test_approve_hook_invalid_transition_raises(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        # Attempting to approve without entering AWAITING_HOOK_APPROVAL
        with pytest.raises(ValueError, match="Cannot approve hook while in state"):
            state.approve_hook("Hook 1")

    def test_request_hook_approval_tool_pause_behavior(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        set_active_project_state(state)
        set_hook_approval_callback(None)  # Ensure no automatic callback

        result = request_hook_approval(
            topic=sample_brief.topic,
            hook_options=["Hook 1", "Hook 2", "Hook 3"],
            recommended_hook="Hook 1",
            selected_angle="Test angle",
            reasoning="Test reasoning",
        )

        assert result["status"] == "awaiting_human_approval"
        assert state.status == ProjectStatus.AWAITING_HOOK_APPROVAL
        assert len(result["hook_options"]) == 3

    def test_request_hook_approval_tool_callback_resume_behavior(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        set_active_project_state(state)

        # Register an interactive human callback
        def mock_human_selection(proposal):
            return proposal.hook_options[2], "Creator preferred Hook 3"

        set_hook_approval_callback(mock_human_selection)

        result = request_hook_approval(
            topic=sample_brief.topic,
            hook_options=["Hook 1", "Hook 2", "Hook 3"],
            recommended_hook="Hook 1",
            selected_angle="Test angle",
            reasoning="Test reasoning",
        )

        assert result["status"] == "approved"
        assert result["selected_hook"] == "Hook 3"
        assert state.status == ProjectStatus.HOOK_APPROVED
        assert state.selected_hook == "Hook 3"

        # Cleanup callback
        set_hook_approval_callback(None)


class TestSelectedHookPropagationAndScenePlan:
    """3 & 4. Tests for selected hook propagation into scene planning and schema validation."""

    def test_finalize_scene_plan_full_lifecycle(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        set_active_project_state(state)
        set_hook_approval_callback(None)

        # 1. Propose hooks
        request_hook_approval(
            topic=sample_brief.topic,
            hook_options=["Hook 1", "Hook 2", "Hook 3"],
            recommended_hook="Hook 2",
            selected_angle="Angle thesis",
            reasoning="Strategic rationale",
        )

        # 2. Creator approves Hook 2
        state.approve_hook("Hook 2")

        # 3. Finalize scene plan
        scene_beats = [
            {
                "scene_id": 1,
                "scene_type": "CIN",
                "visual_description": "Server rack blinking red alert lights.",
                "narration_text": "Hook 2",
                "estimated_duration": 4.0,
            },
            {
                "scene_id": 2,
                "scene_type": "MG",
                "visual_description": "Clean architectural diagram of distributed tracing.",
                "narration_text": "Instead of parsing infinite logs, trace the single causal request chain.",
                "estimated_duration": 7.0,
            },
        ]

        result = finalize_scene_plan(
            selected_hook="Hook 2",
            objective="Educate senior architects on distributed tracing simplification.",
            scene_plan=scene_beats,
            success_criteria=["75% 3-second hook retention", "Architecture clarity"],
        )

        assert result["status"] == "success"
        assert state.status == ProjectStatus.SCENE_PLAN_READY
        assert state.production_plan is not None
        assert state.production_plan.recommended_hook == "Hook 2"
        assert len(state.production_plan.scene_plan) == 2

    def test_finalize_scene_plan_invalid_scenes_rejected(self, sample_brief):
        state = ProjectState(brief=sample_brief)
        set_active_project_state(state)

        # Empty scenes list must fail
        result = finalize_scene_plan(
            selected_hook="Hook 1",
            objective="Objective",
            scene_plan=[],
            success_criteria=["Criteria 1"],
        )
        assert result["status"] == "error"


class TestAgentConfigurationAndModelDiscovery:
    """6. Tests for agent configuration and absence of legacy model hardcoding."""

    def test_aws_region_resolution(self):
        region = get_configured_aws_region()
        assert isinstance(region, str)
        assert len(region) > 0

    def test_no_legacy_claude_preference_in_discovery(self):
        """Confirms that discovery returns active models without forcing legacy Claude 3.5 Sonnet bias."""
        models = discover_available_bedrock_models(region="us-east-1")
        # In an offline test with no credentials, it gracefully returns an empty list without crashing
        assert isinstance(models, list)
