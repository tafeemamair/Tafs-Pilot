"""Visual generation and asset resolution service for Taf's Pilot.

Supports AWS Titan Image Generator via Amazon Bedrock as well as a local
procedural motion-graphic compositor for deterministic offline assembly.
"""

import base64
import json
import os
import subprocess
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from tafs_pilot.config import check_aws_credentials, get_configured_aws_region
from tafs_pilot.models import ScenePlanItem, VisualResult, VisualSceneResult


def _escape_drawtext(s: str) -> str:
    """Escapes special characters for FFmpeg drawtext filter."""
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace(",", "\\,")
        .replace("'", "\\'")
        .replace("%", "%%")
    )


def _build_scene_filters(scene: ScenePlanItem, width: int, height: int) -> List[str]:
    """Builds developer-oriented motion graphic filtergraphs for each scene."""
    if scene.scene_id == 1:
        # Scene 1: Git diff deletion container + hero title "THEY DELETE IT."
        return [
            "format=yuv420p",
            "drawbox=x=0:y=0:w=1080:h=1920:color=0x0A0D14:t=fill",
            # Terminal Window Container
            "drawbox=x=80:y=180:w=920:h=420:color=0x111622@0.95:t=fill",
            "drawbox=x=80:y=180:w=920:h=420:color=0x222E46@0.6:t=2",
            # Header bar
            "drawbox=x=80:y=180:w=920:h=48:color=0x192132@0.95:t=fill",
            "drawbox=x=105:y=198:w=14:h=14:color=0xEF4444@0.9:t=fill",
            "drawbox=x=130:y=198:w=14:h=14:color=0xF59E0B@0.9:t=fill",
            "drawbox=x=155:y=198:w=14:h=14:color=0x10B981@0.9:t=fill",
            f"drawtext=text='{_escape_drawtext('git diff core/service.py')}':font=Consolas:fontsize=20:fontcolor=0x94A3B8:x=200:y=195",
            # Diff code lines
            f"drawtext=text='{_escape_drawtext('@@ -128,45 +128,4 @@')}':font=Consolas:fontsize=22:fontcolor=0x64748B:x=110:y=255",
            f"drawtext=text='{_escape_drawtext('- class LegacyComplexPipelineManager:')}':font=Consolas:fontsize=24:fontcolor=0xF87171:x=110:y=300",
            f"drawtext=text='{_escape_drawtext('-   def process_slowly(self, req):')}':font=Consolas:fontsize=24:fontcolor=0xF87171:x=110:y=345",
            f"drawtext=text='{_escape_drawtext('-   # 420 lines of bloat deleted')}':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=390",
            f"drawtext=text='{_escape_drawtext('+ return simplified_clean_engine(req)')}':font=Consolas:fontsize=26:fontcolor=0x34D399:x=110:y=450",
            # Diff summary tag
            "drawbox=x=80:y=625:w=920:h=70:color=0x1E293B@0.9:t=fill",
            f"drawtext=text='{_escape_drawtext('450 deletions(-)  |  4 additions(+)')}':font=Consolas:fontsize=26:fontcolor=0xF87171:x=110:y=648",
            # Hero Title Callout
            f"drawtext=text='{_escape_drawtext('THEY DELETE IT.')}':font=Arial:fontsize=64:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=800",
            f"drawtext=text='{_escape_drawtext('Senior Engineering Mindset')}':font=Arial:fontsize=24:fontcolor=0x38BDF8:x=(w-text_w)/2:y=890",
            # Bottom subtle accent line
            "drawbox=x=0:y=1890:w=1080:h=12:color=0x3B82F6@0.9:t=fill",
        ]
    elif scene.scene_id == 2:
        # Scene 2: High contrast comparison cards: Junior vs Senior Metrics
        return [
            "format=yuv420p",
            "drawbox=x=0:y=0:w=1080:h=1920:color=0x080A10:t=fill",
            # Card 1: Junior metric
            "drawbox=x=80:y=180:w=920:h=310:color=0x161C2E@0.95:t=fill",
            "drawbox=x=80:y=180:w=920:h=310:color=0xF59E0B@0.35:t=2",
            "drawbox=x=110:y=205:w=200:h=36:color=0xF59E0B@0.2:t=fill",
            f"drawtext=text='{_escape_drawtext('JUNIOR METRIC')}':font=Arial:fontsize=18:fontcolor=0xFBBF24:x=130:y=214",
            f"drawtext=text='{_escape_drawtext('Lines Committed: +2,480')}':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=265",
            f"drawtext=text='{_escape_drawtext('Complexity: High   Review Time: 3 Days')}':font=Consolas:fontsize=22:fontcolor=0x94A3B8:x=110:y=335",
            f"drawtext=text='{_escape_drawtext('Result: 4 Breaking Regressions in Prod')}':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=385",
            # VS divider badge
            "drawbox=x=480:y=520:w=120:h=50:color=0x38BDF8@0.2:t=fill",
            "drawbox=x=480:y=520:w=120:h=50:color=0x38BDF8@0.5:t=1",
            f"drawtext=text='{_escape_drawtext('VS')}':font=Arial:fontsize=24:fontcolor=0x38BDF8:x=(w-text_w)/2:y=532",
            # Card 2: Senior metric
            "drawbox=x=80:y=600:w=920:h=320:color=0x102324@0.95:t=fill",
            "drawbox=x=80:y=600:w=920:h=320:color=0x10B981@0.4:t=2",
            "drawbox=x=110:y=625:w=200:h=36:color=0x10B981@0.2:t=fill",
            f"drawtext=text='{_escape_drawtext('SENIOR METRIC')}':font=Arial:fontsize=18:fontcolor=0x34D399:x=130:y=634",
            f"drawtext=text='{_escape_drawtext('Problems Prevented: 100%%')}':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=685",
            f"drawtext=text='{_escape_drawtext('Outages: 0   Maintenance Cost: Zero')}':font=Consolas:fontsize=22:fontcolor=0x6EE7B7:x=110:y=755",
            f"drawtext=text='{_escape_drawtext('Architecture: 400 Lines Deleted & Simplified')}':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=805",
            # Bottom accent
            "drawbox=x=0:y=1890:w=1080:h=12:color=0x10B981@0.9:t=fill",
        ]
    elif scene.scene_id == 3:
        # Scene 3: Clean terminal simplification motif + callout
        return [
            "format=yuv420p",
            "drawbox=x=0:y=0:w=1080:h=1920:color=0x0C0B16:t=fill",
            # Terminal Window Container
            "drawbox=x=80:y=180:w=920:h=400:color=0x141226@0.95:t=fill",
            "drawbox=x=80:y=180:w=920:h=400:color=0x8B5CF6@0.4:t=2",
            # Header bar
            "drawbox=x=80:y=180:w=920:h=48:color=0x1E1B38@0.95:t=fill",
            "drawbox=x=105:y=198:w=14:h=14:color=0xEF4444@0.9:t=fill",
            "drawbox=x=130:y=198:w=14:h=14:color=0xF59E0B@0.9:t=fill",
            "drawbox=x=155:y=198:w=14:h=14:color=0x10B981@0.9:t=fill",
            f"drawtext=text='{_escape_drawtext('terminal -- zsh')}':font=Consolas:fontsize=20:fontcolor=0xC4B5FD:x=200:y=195",
            # Terminal text
            f"drawtext=text='{_escape_drawtext('> tafs-pilot --simplify-architecture')}':font=Consolas:fontsize=24:fontcolor=0xA78BFA:x=110:y=255",
            f"drawtext=text='{_escape_drawtext('[OK] Analyzing codebase footprint...')}':font=Consolas:fontsize=22:fontcolor=0x94A3B8:x=110:y=305",
            f"drawtext=text='{_escape_drawtext('[OK] Removed 1,200 redundant lines')}':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=350",
            f"drawtext=text='{_escape_drawtext('[DONE] Zero tech debt. Zero complexity.')}':font=Consolas:fontsize=22:fontcolor=0x67E8F9:x=110:y=395",
            # Hero Question Callout
            "drawbox=x=80:y=620:w=920:h=260:color=0x1E153D@0.85:t=fill",
            "drawbox=x=80:y=620:w=920:h=260:color=0xA78BFA@0.5:t=2",
            f"drawtext=text='{_escape_drawtext('WHAT CAN I SIMPLIFY TODAY?')}':font=Arial:fontsize=48:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=680",
            f"drawtext=text='{_escape_drawtext('Eliminate bloat. Ship with clarity.')}':font=Arial:fontsize=26:fontcolor=0xC4B5FD:x=(w-text_w)/2:y=765",
            # Bottom accent
            "drawbox=x=0:y=1890:w=1080:h=12:color=0x8B5CF6@0.9:t=fill",
        ]
    else:
        # Generic developer motion graphic card
        return [
            "format=yuv420p",
            "drawbox=x=0:y=0:w=1080:h=1920:color=0x0B0F19:t=fill",
            "drawbox=x=80:y=180:w=920:h=400:color=0x161E2E@0.95:t=fill",
            "drawbox=x=80:y=180:w=920:h=400:color=0x3B82F6@0.4:t=2",
            f"drawtext=text='{_escape_drawtext(scene.visual_description[:60])}':font=Arial:fontsize=28:fontcolor=0xFFFFFF:x=120:y=240",
            "drawbox=x=0:y=1890:w=1080:h=12:color=0x3B82F6@0.9:t=fill",
        ]


def render_procedural_scene_clip(
    scene: ScenePlanItem,
    output_path: str,
    duration: float = 5.0,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Generates a high-quality 1080x1920 vertical motion graphic MP4 clip using FFmpeg.

    Features developer-oriented kinetic visual storytelling matching scene narrative.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    filters = _build_scene_filters(scene, width, height)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0A0D14:s={width}x{height}:r=30:d={duration}",
        "-vf", ",".join(filters),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg procedural clip generation failed: {result.stderr.strip()}")

    return output_path


def generate_titan_image_bedrock(
    prompt: str,
    output_path: str,
    region: Optional[str] = None,
) -> str:
    """Generates a visual asset via Amazon Titan Image Generator on Bedrock."""
    has_creds, cred_msg = check_aws_credentials()
    if not has_creds:
        raise RuntimeError(f"Amazon Titan visual generation blocked: {cred_msg}")

    region_name = region or get_configured_aws_region()
    try:
        session = boto3.Session(region_name=region_name)
        runtime = session.client("bedrock-runtime", region_name=region_name)

        model_id = os.getenv("TITAN_IMAGE_MODEL_ID", "amazon.titan-image-generator-v2:0")
        request_body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": f"{prompt}, vertical 9:16 portrait composition, 4k cinematic quality, photorealistic",
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 1152,
                "width": 768,  # Vertical portrait
                "cfgScale": 8.0,
            }
        })

        response = runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=request_body,
        )

        resp_json = json.loads(response["body"].read())
        image_base64 = resp_json["images"][0]
        image_bytes = base64.b64decode(image_base64)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return output_path

    except Exception as e:
        raise RuntimeError(f"Bedrock Titan Image generation failed: {str(e)}") from e


def resolve_scene_visuals(
    scenes: List[ScenePlanItem],
    output_dir: str,
    provider: Optional[str] = None,
) -> VisualResult:
    """Resolves or synthesizes a visual asset for each scene in the plan."""
    chosen_provider = provider or os.getenv("VISUAL_PROVIDER", "procedural").lower()
    os.makedirs(output_dir, exist_ok=True)

    results: List[VisualSceneResult] = []

    for s in scenes:
        scene_clip_path = os.path.join(output_dir, f"scene_{s.scene_id}.mp4")

        if chosen_provider in {"titan", "bedrock_titan"}:
            img_path = os.path.join(output_dir, f"scene_{s.scene_id}.png")
            generate_titan_image_bedrock(
                prompt=s.visual_description,
                output_path=img_path,
            )
            # Convert static image to 1080x1920 video clip
            subprocess.run([
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img_path,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
                "-c:v", "libx264",
                "-t", str(max(1.0, s.estimated_duration)),
                "-pix_fmt", "yuv420p",
                scene_clip_path,
            ], check=True, capture_output=True)
        else:
            # Procedural visual clip generator (reliable, deterministic)
            render_procedural_scene_clip(
                scene=s,
                output_path=scene_clip_path,
                duration=max(1.0, s.estimated_duration),
            )

        mode = "aws" if chosen_provider in {"titan", "bedrock_titan"} else "local_fallback"
        results.append(
            VisualSceneResult(
                scene_id=s.scene_id,
                visual_path=os.path.abspath(scene_clip_path),
                provider=chosen_provider,
                mode=mode,
                format="mp4",
                duration=s.estimated_duration,
            )
        )

    mode = "aws" if chosen_provider in {"titan", "bedrock_titan"} else "local_fallback"
    return VisualResult(
        status="success",
        provider=chosen_provider,
        mode=mode,
        scenes=results,
    )
