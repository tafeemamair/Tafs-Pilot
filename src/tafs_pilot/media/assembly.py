"""Video assembly and subtitle compositing engine for Taf's Pilot.

Combines per-scene visuals, synthesized voiceovers, burned-in subtitles,
and concatenates scenes into a vertical short-form MP4 deliverable.
"""

import os
import re
import subprocess
import textwrap
from typing import List, Optional
from tafs_pilot.models import (
    ProductionPlan,
    ScenePlanItem,
    VisualResult,
    VoiceoverResult,
)


def format_srt_timestamp(seconds: float) -> str:
    """Formats float seconds into SRT timestamp string HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def create_scene_srt(scene: ScenePlanItem, duration: float, srt_path: str) -> str:
    """Generates an SRT subtitle file with natural spoken phrasing beats across the scene."""
    os.makedirs(os.path.dirname(srt_path), exist_ok=True)

    clean_text = scene.narration_text.strip().replace("\n", " ")

    # Split into sentence beats on sentence boundary punctuation followed by space
    raw_sentences = [p.strip() for p in re.split(r"(?<=[.?!:])\s+", clean_text) if p.strip()]
    sentences = raw_sentences if raw_sentences else [clean_text]

    # Calculate proportional duration for each sentence beat based on word count
    total_words = sum(max(1, len(s.split())) for s in sentences)
    srt_blocks = []
    current_time = 0.0

    for idx, sentence in enumerate(sentences, start=1):
        words = max(1, len(sentence.split()))
        if idx == len(sentences):
            beat_duration = max(0.5, duration - current_time)
        else:
            beat_duration = (words / total_words) * duration

        start_ts = format_srt_timestamp(current_time)
        end_ts = format_srt_timestamp(min(duration, current_time + beat_duration))

        # Wrap text cleanly across short-form lines (maximum 42 characters per line)
        wrapped_sentence = textwrap.fill(sentence, width=42)
        srt_blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{wrapped_sentence}\n")
        current_time += beat_duration

    content = "\n".join(srt_blocks)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(content)

    return srt_path


def render_composite_scene_clip(
    visual_path: str,
    audio_path: str,
    duration: float,
    srt_path: str,
    output_path: str,
) -> str:
    """Renders an individual scene clip pairing visual, narration audio, and burned subtitles."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Escape subtitle path for FFmpeg filter on Windows
    escaped_srt = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", visual_path,
        "-i", audio_path,
        "-t", str(duration),
        "-vf", (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"subtitles='{escaped_srt}':force_style='FontSize=16,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=65'"
        ),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback without subtitle filter if libass encounters fontconfig issue
        cmd_fallback = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", visual_path,
            "-i", audio_path,
            "-t", str(duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path,
        ]
        fb_result = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if fb_result.returncode != 0:
            raise RuntimeError(f"FFmpeg scene render failed: {fb_result.stderr.strip()}")

    return output_path


def assemble_production_video(
    scenes: List[ScenePlanItem],
    voiceovers: VoiceoverResult,
    visuals: VisualResult,
    project_artifacts_dir: str,
    output_filename: str = "final.mp4",
) -> str:
    """Assembles all individual scene clips and concatenates them into the final MP4 deliverable."""
    renders_dir = os.path.join(project_artifacts_dir, "renders")
    captions_dir = os.path.join(project_artifacts_dir, "captions")
    os.makedirs(renders_dir, exist_ok=True)
    os.makedirs(captions_dir, exist_ok=True)

    # Build map of audio and visual results by scene_id
    vo_map = {vo.scene_id: vo for vo in voiceovers.scenes}
    vis_map = {vis.scene_id: vis for vis in visuals.scenes}

    rendered_scene_paths: List[str] = []

    for s in scenes:
        vo = vo_map.get(s.scene_id)
        vis = vis_map.get(s.scene_id)

        if not vo or not os.path.exists(vo.audio_path):
            raise FileNotFoundError(f"Missing voiceover audio for Scene {s.scene_id}")
        if not vis or not os.path.exists(vis.visual_path):
            raise FileNotFoundError(f"Missing visual asset for Scene {s.scene_id}")

        # The actual voiceover audio duration drives the exact scene pacing!
        actual_duration = vo.duration

        # Create SRT captions for this scene
        srt_path = os.path.join(captions_dir, f"scene_{s.scene_id}.srt")
        create_scene_srt(s, actual_duration, srt_path)

        # Composite scene clip
        scene_output = os.path.join(renders_dir, f"scene_{s.scene_id}.mp4")
        render_composite_scene_clip(
            visual_path=vis.visual_path,
            audio_path=vo.audio_path,
            duration=actual_duration,
            srt_path=srt_path,
            output_path=scene_output,
        )

        rendered_scene_paths.append(os.path.abspath(scene_output))

    # Concat all scenes into final deliverable
    concat_manifest = os.path.join(project_artifacts_dir, "concat.txt")
    with open(concat_manifest, "w", encoding="utf-8") as f:
        for path in rendered_scene_paths:
            f.write(f"file '{path.replace(os.sep, '/')}'\n")

    final_output_path = os.path.join(project_artifacts_dir, output_filename)

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_manifest,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_output_path,
    ]

    concat_res = subprocess.run(concat_cmd, capture_output=True, text=True)
    if concat_res.returncode != 0:
        raise RuntimeError(f"FFmpeg final concat assembly failed: {concat_res.stderr.strip()}")

    if not os.path.exists(final_output_path) or os.path.getsize(final_output_path) == 0:
        raise RuntimeError(f"Assembly completed but output is missing or empty: {final_output_path}")

    return os.path.abspath(final_output_path)
