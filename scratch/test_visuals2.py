import os
import subprocess

def esc(s: str) -> str:
    # FFmpeg drawtext parameter escaping: colons, commas, backslashes, percent
    return s.replace("\\", "\\\\").replace(":", "\\:").replace(",", "\\,").replace("'", "\\'").replace("%", "\\%")

os.makedirs("scratch", exist_ok=True)

# Test Scene 1 Visual
filters_s1 = [
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
    f"drawtext=text='{esc('git diff core/service.py')}':font=Consolas:fontsize=20:fontcolor=0x94A3B8:x=200:y=195",
    # Diff code lines
    f"drawtext=text='{esc('@@ -128,45 +128,4 @@')}':font=Consolas:fontsize=22:fontcolor=0x64748B:x=110:y=255",
    f"drawtext=text='{esc('- class LegacyComplexPipelineManager:')}':font=Consolas:fontsize=24:fontcolor=0xF87171:x=110:y=300",
    f"drawtext=text='{esc('-   def process_slowly(self, req):')}':font=Consolas:fontsize=24:fontcolor=0xF87171:x=110:y=345",
    f"drawtext=text='{esc('-   # 420 lines of bloat deleted')}':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=390",
    f"drawtext=text='{esc('+ return simplified_clean_engine(req)')}':font=Consolas:fontsize=26:fontcolor=0x34D399:x=110:y=450",
    # Diff summary tag
    "drawbox=x=80:y=625:w=920:h=70:color=0x1E293B@0.9:t=fill",
    f"drawtext=text='{esc('450 deletions(-)  |  4 additions(+)')}':font=Consolas:fontsize=26:fontcolor=0xF87171:x=110:y=648",
    # Hero Title Callout
    f"drawtext=text='{esc('THEY DELETE IT.')}':font=Arial:fontsize=64:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=800",
    f"drawtext=text='{esc('Senior Engineering Mindset')}':font=Arial:fontsize=24:fontcolor=0x38BDF8:x=(w-text_w)/2:y=890",
    # Bottom subtle accent line
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x3B82F6@0.9:t=fill",
]

cmd1 = [
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x0A0D14:s=1080x1920:d=1",
    "-vf", ",".join(filters_s1),
    "-frames:v", "1",
    "scratch/test_scene1_vis.png"
]
subprocess.run(cmd1, check=True)
print("Rendered Scene 1 visual!")

# Test Scene 2 Visual
filters_s2 = [
    "format=yuv420p",
    "drawbox=x=0:y=0:w=1080:h=1920:color=0x080A10:t=fill",
    # Card 1: Junior metric
    "drawbox=x=80:y=180:w=920:h=310:color=0x161C2E@0.95:t=fill",
    "drawbox=x=80:y=180:w=920:h=310:color=0xF59E0B@0.35:t=2",
    "drawbox=x=110:y=205:w=200:h=36:color=0xF59E0B@0.2:t=fill",
    f"drawtext=text='{esc('JUNIOR METRIC')}':font=Arial:fontsize=18:fontcolor=0xFBBF24:x=130:y=214",
    f"drawtext=text='{esc('Lines Committed: +2,480')}':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=265",
    f"drawtext=text='{esc('Complexity: High   Review Time: 3 Days')}':font=Consolas:fontsize=22:fontcolor=0x94A3B8:x=110:y=335",
    f"drawtext=text='{esc('Result: 4 Breaking Regressions in Prod')}':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=385",
    # VS divider badge
    "drawbox=x=480:y=520:w=120:h=50:color=0x38BDF8@0.2:t=fill",
    "drawbox=x=480:y=520:w=120:h=50:color=0x38BDF8@0.5:t=1",
    f"drawtext=text='{esc('VS')}':font=Arial:fontsize=24:fontcolor=0x38BDF8:x=(w-text_w)/2:y=532",
    # Card 2: Senior metric
    "drawbox=x=80:y=600:w=920:h=320:color=0x102324@0.95:t=fill",
    "drawbox=x=80:y=600:w=920:h=320:color=0x10B981@0.4:t=2",
    "drawbox=x=110:y=625:w=200:h=36:color=0x10B981@0.2:t=fill",
    f"drawtext=text='{esc('SENIOR METRIC')}':font=Arial:fontsize=18:fontcolor=0x34D399:x=130:y=634",
    f"drawtext=text='{esc('Problems Prevented: 100%')}':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=685",
    f"drawtext=text='{esc('Outages: 0   Maintenance Cost: Zero')}':font=Consolas:fontsize=22:fontcolor=0x6EE7B7:x=110:y=755",
    f"drawtext=text='{esc('Architecture: 400 Lines Deleted & Simplified')}':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=805",
    # Bottom accent
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x10B981@0.9:t=fill",
]

cmd2 = [
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x080A10:s=1080x1920:d=1",
    "-vf", ",".join(filters_s2),
    "-frames:v", "1",
    "scratch/test_scene2_vis.png"
]
subprocess.run(cmd2, check=True)
print("Rendered Scene 2 visual!")

# Test Scene 3 Visual
filters_s3 = [
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
    f"drawtext=text='{esc('terminal -- zsh')}':font=Consolas:fontsize=20:fontcolor=0xC4B5FD:x=200:y=195",
    # Terminal text
    f"drawtext=text='{esc('> tafs-pilot --simplify-architecture')}':font=Consolas:fontsize=24:fontcolor=0xA78BFA:x=110:y=255",
    f"drawtext=text='{esc('[OK] Analyzing codebase footprint...')}':font=Consolas:fontsize=22:fontcolor=0x94A3B8:x=110:y=305",
    f"drawtext=text='{esc('[OK] Removed 1,200 redundant lines')}':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=350",
    f"drawtext=text='{esc('[DONE] Zero tech debt. Zero complexity.')}':font=Consolas:fontsize=22:fontcolor=0x67E8F9:x=110:y=395",
    # Hero Question Callout
    "drawbox=x=80:y=620:w=920:h=260:color=0x1E153D@0.85:t=fill",
    "drawbox=x=80:y=620:w=920:h=260:color=0xA78BFA@0.5:t=2",
    f"drawtext=text='{esc('WHAT CAN I SIMPLIFY TODAY?')}':font=Arial:fontsize=48:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=680",
    f"drawtext=text='{esc('Eliminate bloat. Ship with clarity.')}':font=Arial:fontsize=26:fontcolor=0xC4B5FD:x=(w-text_w)/2:y=765",
    # Bottom accent
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x8B5CF6@0.9:t=fill",
]

cmd3 = [
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x0C0B16:s=1080x1920:d=1",
    "-vf", ",".join(filters_s3),
    "-frames:v", "1",
    "scratch/test_scene3_vis.png"
]
subprocess.run(cmd3, check=True)
print("Rendered Scene 3 visual!")
