import os
import subprocess

srt_text = """1
00:00:00,000 --> 00:00:07,000
Junior developers measure progress in lines committed.
Seniors measure progress in problems prevented.
"""
srt_file = os.path.abspath("scratch/test_sub.srt")
os.makedirs("scratch", exist_ok=True)
with open(srt_file, "w", encoding="utf-8") as f:
    f.write(srt_text)

escaped_srt = srt_file.replace("\\", "/").replace(":", "\\:")
out_png = "C:/Users/aisan/.gemini/antigravity-ide/brain/91a37b09-eb73-406b-9eeb-cbfeb5f9f553/scratch/test_sub_aligned.png"

# Test MarginV=100 with Alignment=2 and FontSize=16
cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=0x0B0F19:s=1080x1920:d=1",
    "-vf", f"subtitles='{escaped_srt}':force_style='FontSize=16,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=90'",
    "-frames:v", "1",
    out_png
]
subprocess.run(cmd, check=True)
print("SUCCESS rendering test_sub_aligned.png!")
