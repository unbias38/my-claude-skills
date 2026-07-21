"""
make_fixture.py —— 產生一組「合成的測試素材」給回歸測試用。

為什麼不直接拿真實的歌來測？
  1. 版權：skill 要分享給別人，不該夾帶別人的專輯封面和音樂。
  2. 體積：真實素材加上六套版面的基準圖會超過 100MB，太肥。
  3. 可控：合成的圖可以刻意做出「亮區、暗區、細節密集區」，
     專門去踩自動調校的規則；真實封面只是碰運氣。

產出（約 300KB，可以放心跟 skill 一起散布）：
    tests/fixture/cover.png    合成封面：漸層 + 亮塊 + 密集細節 + 文字
    tests/fixture/tone.mp3     合成音樂：12 秒，音量與音高都有變化
    tests/fixture/lyrics.txt   合成歌詞：含一句「刻意很長」的，用來測字級自動縮小
    tests/fixture/project.json

執行：python3 tests/make_fixture.py
"""

import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
from env import find_fonts, find_ffmpeg   # noqa: E402

OUT = os.path.join(HERE, "fixture")
SIZE = 1254
DUR = 12.0
SR = 44100


def make_cover():
    """畫一張刻意「有亮有暗、有平有密」的封面。"""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) / SIZE
    # 底：冷色調的斜向漸層（平順區，用來看遮罩會不會壓過頭）
    r = 20 + 70 * xx + 30 * yy
    g = 34 + 60 * yy + 20 * xx
    b = 58 + 90 * (1 - xx) * yy + 30 * xx
    a = np.dstack([r, g, b])
    # 右上角放一塊很亮的區域（模擬真實封面常見的亮紙、天空）
    m = np.exp(-(((xx - 0.78) ** 2 + (yy - 0.22) ** 2) / 0.012))
    a += (np.dstack([m, m, m]) * 190)
    # 左下角一圈暗角
    v = np.exp(-(((xx - 0.18) ** 2 + (yy - 0.85) ** 2) / 0.05))
    a -= np.dstack([v, v, v]) * 40
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    d = ImageDraw.Draw(im)
    # 密集細線：模擬封面上的文字與細節，逼自動調校把遮罩壓深
    for i in range(0, SIZE, 26):
        d.line([(i, SIZE * 0.62), (i + 60, SIZE * 0.95)], fill=(210, 220, 235), width=2)
    reg, bold = find_fonts()
    d.text((80, 90), "測試封面", font=ImageFont.truetype(bold, 132), fill=(245, 248, 252))
    d.text((84, 250), "SYNTHETIC TEST COVER", font=ImageFont.truetype(reg, 44),
           fill=(200, 212, 228))
    im.save(os.path.join(OUT, "cover.png"))
    return im


def make_audio():
    """合成一段音高與音量都會變的聲音，讓頻譜有東西可以畫。"""
    t = np.arange(int(DUR * SR)) / SR
    sig = np.zeros_like(t)
    for f0, amp in ((110, .5), (220, .35), (440, .25), (880, .15), (1760, .1)):
        # 音高緩慢起伏 + 音量呼吸，頻譜才不會是一條死線
        sig += amp * np.sin(2 * np.pi * f0 * t * (1 + 0.02 * np.sin(2 * np.pi * 0.2 * t)))
    beat = (np.sin(2 * np.pi * 2 * t) > 0.7).astype(float)     # 每半秒一個鼓點
    sig *= 0.35 + 0.65 * np.exp(-((t % 0.5) * 8))
    sig += beat * 0.25 * np.sin(2 * np.pi * 60 * t)
    sig = np.clip(sig / np.abs(sig).max() * 0.85, -1, 1)
    pcm = (sig * 32767).astype("<i2").tobytes()

    mp3 = os.path.join(OUT, "tone.mp3")
    subprocess.run([find_ffmpeg(), "-y", "-v", "error", "-f", "s16le", "-ar", str(SR),
                    "-ac", "1", "-i", "-", "-b:a", "96k", mp3],
                   input=pcm, check=True)
    return mp3


LYRICS = [
    ("第一句測試歌詞。", 0.6, 2.0),
    ("第二句，稍微長一點點。", 2.0, 3.6),
    ("這一句故意寫得非常非常長，用來測試字級會不會自動縮小以免被切掉。", 3.6, 6.0),
    ("短句。", 6.0, 7.0),
    ("間奏前的最後一句。", 7.0, 8.2),          # 8.2~10.0 是間奏，測金色收掉
    ("間奏之後回來了。", 10.0, 11.4),
]


def make_lyrics():
    def st(s):
        return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(round(s%1*1000)):03d}"
    body = "\n\n".join(f"{i+1} {st(a)} --> {st(b)} {t}"
                       for i, (t, a, b) in enumerate(LYRICS))
    path = os.path.join(OUT, "lyrics.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body + "\n")
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    make_cover()
    make_audio()
    make_lyrics()
    with open(os.path.join(OUT, "project.json"), "w", encoding="utf-8") as f:
        json.dump({"title": "測試曲目", "subtitle": "SYNTHETIC TEST TRACK",
                   "art": "cover.png", "audio": "tone.mp3", "lyrics": "lyrics.txt",
                   "layout": "16x9", "out_prefix": "fixture", "overrides": {}},
                  f, ensure_ascii=False, indent=2)
    total = sum(os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT))
    print(f"測試素材已產生於 {OUT}（共 {total/1024:.0f} KB）")


if __name__ == "__main__":
    main()
