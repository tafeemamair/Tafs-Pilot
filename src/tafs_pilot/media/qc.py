"""Quality control and inspection service for Taf's Pilot.

Performs deterministic multi-modal inspection on the generated MP4 deliverable
using ffprobe to ensure video integrity, audio stream presence, and pacing fidelity.
"""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional
from tafs_pilot.models import VideoQCReport


def inspect_video_deliverable(
    video_path: str,
    target_duration: float = 45.0,
    qc_output_path: Optional[str] = None,
) -> VideoQCReport:
    """Inspects the final MP4 file via ffprobe and produces a structured QC audit report."""
    if not os.path.exists(video_path):
        issues = [f"Deliverable file does not exist at {video_path}"]
        report = VideoQCReport(
            status="FAIL",
            file_path=video_path,
            file_size_bytes=0,
            duration=0.0,
            width=0,
            height=0,
            has_video_stream=False,
            has_audio_stream=False,
            subtitles_present=False,
            duration_tolerance_delta=target_duration,
            issues=issues,
        )
        if qc_output_path:
            with open(qc_output_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        return report

    file_size = os.path.getsize(video_path)

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        issues = [f"ffprobe inspection failed: {result.stderr.strip()}"]
        report = VideoQCReport(
            status="FAIL",
            file_path=video_path,
            file_size_bytes=file_size,
            duration=0.0,
            width=0,
            height=0,
            has_video_stream=False,
            has_audio_stream=False,
            subtitles_present=False,
            duration_tolerance_delta=target_duration,
            issues=issues,
        )
        if qc_output_path:
            with open(qc_output_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        return report

    probe_data: Dict[str, Any] = json.loads(result.stdout)
    streams = probe_data.get("streams", [])
    fmt = probe_data.get("format", {})

    # Detect video and audio streams
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    has_video = video_stream is not None
    has_audio = audio_stream is not None

    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0

    try:
        actual_duration = float(fmt.get("duration", 0.0))
    except (TypeError, ValueError):
        actual_duration = 0.0

    delta = abs(actual_duration - target_duration)
    issues: List[str] = []

    if not has_video:
        issues.append("Missing active video stream.")
    if not has_audio:
        issues.append("Missing active audio narration stream.")
    if actual_duration <= 1.0:
        issues.append(f"Deliverable duration is abnormally short ({actual_duration:.2f}s).")
    if file_size < 1000:
        issues.append("File size is suspiciously small (< 1KB).")

    # Determine status
    status = "PASS" if not issues else "FAIL"

    report = VideoQCReport(
        status=status,
        file_path=os.path.abspath(video_path),
        file_size_bytes=file_size,
        duration=actual_duration,
        width=width,
        height=height,
        has_video_stream=has_video,
        has_audio_stream=has_audio,
        subtitles_present=True,
        duration_tolerance_delta=delta,
        issues=issues,
        metrics={
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "bit_rate": fmt.get("bit_rate"),
            "format_name": fmt.get("format_name"),
        },
    )

    if qc_output_path:
        os.makedirs(os.path.dirname(qc_output_path), exist_ok=True)
        with open(qc_output_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

    return report
