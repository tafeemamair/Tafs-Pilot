"""Taf's Pilot: Autonomous Video Production Agent for Professional Creators.

Built for the Amazon Agents for Humans Hackathon (Professional Agents track)
using Amazon Strands Agents SDK and Amazon Bedrock.
"""

__version__ = "0.1.0"

from tafs_pilot.models import CreatorBrief, ProductionPlan, ScenePlanItem

__all__ = [
    "CreatorBrief",
    "ProductionPlan",
    "ScenePlanItem",
    "__version__",
]
