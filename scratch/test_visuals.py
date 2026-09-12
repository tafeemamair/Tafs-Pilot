import os
import subprocess

out_dir = "C:/Users/aisan/.gemini/antigravity-ide/brain/91a37b09-eb73-406b-9eeb-cbfeb5f9f553/scratch"
os.makedirs(out_dir, exist_ok=True)

# -------------------------------------------------------------
# Scene 1: Senior Engineers Delete Code (-450 lines diff motif)
# -------------------------------------------------------------
vf_scene1 = (
    "format=yuv420p,"
    "drawbox=x=0:y=0:w=1080:h=1920:color=0x080A10:t=fill,"
    # Terminal Window Container
    "drawbox=x=70:y=200:w=940:h=900:color=0x0F1422@0.95:t=fill,"
    "drawbox=x=70:y=200:w=940:h=900:color=0x1E293B@0.8:t=2,"
    # Window Header Bar
    "drawbox=x=70:y=200:w=940:h=64:color=0x182032:t=fill,"
    # Traffic light dots
    "drawbox=x=105:y=224:w=16:h=16:color=0xEF4444:t=fill,"
    "drawbox=x=133:y=224:w=16:h=16:color=0xF59E0B:t=fill,"
    "drawbox=x=161:y=224:w=16:h=16:color=0x10B981:t=fill,"
    # Window Title
    "drawtext=text='senior-architect-rule.ts':font=Arial:fontsize=22:fontcolor=0x94A3B8:x=200:y=222,"
    # Code diff lines
    "drawtext=text='@@ -142,18 +142,2 @@ - Redundant Logic':font=Consolas:fontsize=24:fontcolor=0x64748B:x=110:y=300,"
    "drawbox=x=95:y=340:w=890:h=48:color=0x3B1219@0.7:t=fill,"
    "drawtext=text='-  return await retryManager.wrapWithCircuitBreaker(fn)':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=352,"
    "drawbox=x=95:y=396:w=890:h=48:color=0x3B1219@0.7:t=fill,"
    "drawtext=text='-  const fallbackCache = new DistributedCacheHandler()':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=408,"
    "drawbox=x=95:y=452:w=890:h=48:color=0x102A1E@0.7:t=fill,"
    "drawtext=text='+  return fn() // Simplified direct execution':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=464,"
    # Massive Diff Stat Badge
    "drawbox=x=200:y=540:w=680:h=110:color=0xEF4444@0.2:t=fill,"
    "drawbox=x=200:y=540:w=680:h=110:color=0xEF4444@0.6:t=2,"
    "drawtext=text='-450 LINES OF CODE DELETED':font=Arial:fontsize=36:fontcolor=0xFCA5A5:x=(w-text_w)/2:y=576,"
    # Dynamic emphasis badge for 'THEY DELETE IT.'
    "drawbox=x=180:y=700:w=720:h=120:color=0x38BDF8@0.15:t=fill,"
    "drawbox=x=180:y=700:w=720:h=120:color=0x38BDF8@0.7:t=2,"
    "drawtext=text='THEY DELETE IT.':font=Arial:fontsize=48:fontcolor=0x38BDF8:x=(w-text_w)/2:y=736,"
    # Bottom subtle blue accent pulse bar
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x38BDF8@0.9:t=fill"
)

cmd1 = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0x080A10:s=1080x1920:d=1",
    "-vf", vf_scene1,
    "-frames:v", "1",
    f"{out_dir}/test_scene1_vis.png"
]
subprocess.run(cmd1, check=True)
print("Rendered test_scene1_vis.png")

# -------------------------------------------------------------
# Scene 2: Contrast (Lines Committed vs Problems Prevented)
# -------------------------------------------------------------
vf_scene2 = (
    "format=yuv420p,"
    "drawbox=x=0:y=0:w=1080:h=1920:color=0x080A10:t=fill,"
    # Card 1: Junior Dev metric
    "drawbox=x=80:y=220:w=920:h=340:color=0x161C2E@0.95:t=fill,"
    "drawbox=x=80:y=220:w=920:h=340:color=0xF59E0B@0.35:t=2,"
    "drawbox=x=110:y=250:w=200:h=36:color=0xF59E0B@0.2:t=fill,"
    "drawtext=text='JUNIOR METRIC':font=Arial:fontsize=18:fontcolor=0xFBBF24:x=130:y=260,"
    "drawtext=text='Lines Committed: +2,480':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=310,"
    "drawtext=text='Complexity: High  |  Review time: 3 days':font=Consolas:fontsize=24:fontcolor=0x94A3B8:x=110:y=380,"
    "drawtext=text='Status: 4 Breaking Regressions':font=Consolas:fontsize=22:fontcolor=0xF87171:x=110:y=430,"
    # VS Divider
    "drawbox=x=480:y=590:w=120:h=50:color=0x38BDF8@0.2:t=fill,"
    "drawbox=x=480:y=590:w=120:h=50:color=0x38BDF8@0.5:t=1,"
    "drawtext=text='VS':font=Arial:fontsize=24:fontcolor=0x38BDF8:x=(w-text_w)/2:y=602,"
    # Card 2: Senior Engineer metric
    "drawbox=x=80:y=670:w=920:h=340:color=0x102324@0.95:t=fill,"
    "drawbox=x=80:y=670:w=920:h=340:color=0x10B981@0.4:t=2,"
    "drawbox=x=110:y=700:w=200:h=36:color=0x10B981@0.2:t=fill,"
    "drawtext=text='SENIOR METRIC':font=Arial:fontsize=18:fontcolor=0x34D399:x=130:y=710,"
    "drawtext=text='Problems Prevented: 100%':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=110:y=760,"
    "drawtext=text='Outages: 0  |  Maintenance Cost: Zero':font=Consolas:fontsize=24:fontcolor=0x6EE7B7:x=110:y=830,"
    "drawtext=text='Status: Deployed & Stable':font=Consolas:fontsize=22:fontcolor=0x34D399:x=110:y=880,"
    # Bottom accent line
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x10B981@0.9:t=fill"
)

cmd2 = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0x080A10:s=1080x1920:d=1",
    "-vf", vf_scene2,
    "-frames:v", "1",
    f"{out_dir}/test_scene2_vis.png"
]
subprocess.run(cmd2, check=True)
print("Rendered test_scene2_vis.png")

# -------------------------------------------------------------
# Scene 3: Simplification / What Can I Simplify Today?
# -------------------------------------------------------------
vf_scene3 = (
    "format=yuv420p,"
    "drawbox=x=0:y=0:w=1080:h=1920:color=0x080A10:t=fill,"
    # Terminal Container
    "drawbox=x=70:y=200:w=940:h=900:color=0x0F1422@0.95:t=fill,"
    "drawbox=x=70:y=200:w=940:h=900:color=0x6366F1@0.4:t=2,"
    # Window Header
    "drawbox=x=70:y=200:w=940:h=64:color=0x182032:t=fill,"
    "drawbox=x=105:y=224:w=16:h=16:color=0xEF4444:t=fill,"
    "drawbox=x=133:y=224:w=16:h=16:color=0xF59E0B:t=fill,"
    "drawbox=x=161:y=224:w=16:h=16:color=0x10B981:t=fill,"
    "drawtext=text='bash -- architecture-audit':font=Arial:fontsize=22:fontcolor=0x94A3B8:x=200:y=222,"
    # Terminal Prompt
    "drawtext=text='$ tafs-pilot --simplify-architecture':font=Consolas:fontsize=24:fontcolor=0x38BDF8:x=110:y=300,"
    "drawtext=text='[✓] 4 microservices condensed to 1 module':font=Consolas:fontsize=24:fontcolor=0x34D399:x=110:y=360,"
    "drawtext=text='[✓] 12 glue-code adapters eliminated':font=Consolas:fontsize=24:fontcolor=0x34D399:x=110:y=420,"
    "drawtext=text='[✓] Latency reduced by 64%':font=Consolas:fontsize=24:fontcolor=0x34D399:x=110:y=480,"
    # Final Action Callout Card
    "drawbox=x=140:y=580:w=800:h=140:color=0x6366F1@0.2:t=fill,"
    "drawbox=x=140:y=580:w=800:h=140:color=0x818CF8@0.6:t=2,"
    "drawtext=text='WHAT CAN I SIMPLIFY TODAY?':font=Arial:fontsize=36:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=635,"
    # Bottom accent line
    "drawbox=x=0:y=1890:w=1080:h=12:color=0x818CF8@0.9:t=fill"
)

cmd3 = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0x080A10:s=1080x1920:d=1",
    "-vf", vf_scene3,
    "-frames:v", "1",
    f"{out_dir}/test_scene3_vis.png"
]
subprocess.run(cmd3, check=True)
print("Rendered test_scene3_vis.png")
