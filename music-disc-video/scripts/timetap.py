"""
timetap.py —— 產生一個「敲拍對時」網頁，把沒有時間軸的歌詞標上時間。

執行方式：
    python3 scripts/timetap.py <歌曲資料夾>

會在該資料夾產生「敲拍對時.html」，雙擊打開後：
    按空白鍵開始播放 → 每唱到一句新歌詞就敲一下空白鍵 → 標完按「匯出歌詞檔」

為什麼需要這個？
    網路上找得到的歌詞大多只有文字、沒有時間。
    要讓歌詞跟著音樂捲動、當前句變色，就一定要知道每一句是第幾秒開始唱的。
    自動辨識中文歌聲的準確度很差，人耳跟著敲反而又快又準 ——
    一首四分鐘的歌，跟著哼一遍就標完了。
"""

import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lyrics as lyrics_mod
from layout import load_project, SKILL_DIR

TEMPLATE = os.path.join(SKILL_DIR, "assets", "timetap.html")


def build(project_dir):
    proj = load_project(project_dir)

    if not proj.get("lyrics") or not os.path.exists(proj["lyrics"]):
        sys.exit(f"找不到歌詞檔：{proj.get('lyrics')}\n"
                 "請先放一份純文字歌詞（一句一行）進去。")

    # 歌詞可能已經有時間軸了 —— 那就拿現有的文字來重標
    try:
        parsed = lyrics_mod.parse(proj["lyrics"])
        texts = [L["text"] for L in parsed]
        print(f"注意：{os.path.basename(proj['lyrics'])} 已經有時間軸了。")
        print("這次會拿裡面的文字重新對時，原檔不會被動到。")
    except lyrics_mod.NoTimestamps as e:
        texts = e.texts

    if not texts:
        sys.exit("歌詞是空的。")

    with open(proj["audio"], "rb") as f:
        mp3 = base64.b64encode(f.read()).decode("ascii")

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    base = os.path.splitext(os.path.basename(proj["lyrics"]))[0]
    out_name = f"{base}_已對時.txt"
    for k, v in {
        "__TITLE__": proj["title"],
        "__TEXTS_JSON__": json.dumps(texts, ensure_ascii=False),
        "__OUTNAME__": out_name,
        "__MP3_B64__": mp3,
    }.items():
        html = html.replace(k, v)

    out = os.path.join(project_dir, "敲拍對時.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n已產生：{out}（{os.path.getsize(out)/1e6:.1f} MB，共 {len(texts)} 句）")
    print("\n接下來：")
    print("  1. 雙擊打開它")
    print("  2. 按空白鍵開始播放")
    print("  3. 每唱到一句新歌詞的第一個字，就敲一下空白鍵")
    print("  4. 敲錯按 Backspace 退回；點清單任一句可以從那裡重來")
    print("  5. 標完按「匯出歌詞檔」，會下載一份 " + out_name)
    print(f"  6. 把下載到的檔案放回 {project_dir}，")
    print(f"     並把 project.json 的 lyrics 改成 \"{out_name}\"")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法：python3 timetap.py <歌曲資料夾>")
    build(sys.argv[1])
