"""
build_html.py —— 把「版面設定 + 圖片 + 音樂 + 歌詞 + 頻譜」組成一個單一 HTML 檔。

執行方式：
    python3 scripts/build_html.py <歌曲資料夾>

那個資料夾裡要有一份 project.json 說明素材在哪，例如：
    {
      "title": "全都與我無關",
      "subtitle": "IT HAS NOTHING TO DO WITH ME",
      "art":    "cover.png",
      "audio":  "song.mp3",
      "lyrics": "lyrics.txt",
      "layout": "16x9"
    }

為什麼要做成「單一檔案」？
    因為圖片和音樂都被轉成文字塞進 HTML 裡了，整個作品只有一個檔案。
    複製到隨身碟、傳給別人、丟到桌面，都不會破圖或沒聲音。
    代價是檔案比較大（約 8~9MB），但對本機播放來說完全沒問題。
"""

import base64
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lyrics as lyrics_mod
from env import css_font_stack
from layout import Layout, load_project, SKILL_DIR
from spectrum import compute_spectrum, DATA_FPS

TEMPLATE = os.path.join(SKILL_DIR, "assets", "template.html")


def b64_file(path):
    """把任何檔案讀成 base64 文字。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def build(project_dir, quiet=False):
    say = (lambda *a: None) if quiet else print

    proj = load_project(project_dir)
    lay  = Layout.load(proj["layout"], proj.get("overrides"))
    say(f"=== 產生網頁版：{proj['title']}（版面 {proj['layout']}）===")

    need = ["art", "audio"] + (["lyrics"] if lay.cfg.get("has_lyrics", True) else [])
    for key in need:
        if not proj.get(key) or not os.path.exists(proj[key]):
            sys.exit(f"找不到 {key} 檔案：{proj.get(key)}")

    # 1) 歌詞（無歌詞版面就跳過）
    has_lyrics = lay.cfg.get("has_lyrics", True)
    if has_lyrics:
        lines = lyrics_mod.parse(proj["lyrics"])
        say(f"[1/5] 歌詞解析完成：{len(lines)} 句，"
            f"第一句 {lines[0]['start']:.1f}s，最後一句結束 {lines[-1]['end']:.1f}s")
    else:
        lines = []
        say("[1/5] 這是無歌詞版面，跳過歌詞")

    # 2) 頻譜（事先把整首歌「聽」一遍算好）
    n_bars = lay.cfg["spectrum"]["bars"]
    spec, duration = compute_spectrum(proj["audio"], n_bars=n_bars, data_fps=DATA_FPS)
    for w in lyrics_mod.sanity_check(lines, duration) if has_lyrics else []:
        say("  ⚠ " + w)
    say(f"[2/5] 頻譜計算完成：{spec.shape[0]} 幀 × {spec.shape[1]} 柱，歌長 {duration:.2f}s")

    # 3) 圖片與音樂轉成文字
    art_b64 = b64_file(proj["art"])
    mp3_b64 = b64_file(proj["audio"])
    say(f"[3/5] 素材編碼完成：圖片 {len(art_b64)/1e6:.1f}MB 文字、"
        f"音樂 {len(mp3_b64)/1e6:.1f}MB 文字")

    # 4) 套進模板
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    # 無歌詞版面：把模板裡標記起來的歌詞區塊整段刪掉，
    # 這樣同一份模板就能同時服務「有歌詞」和「純音樂」兩種版面。
    if not has_lyrics:
        for a, b in (("<!--LYRICS_HTML_START-->", "<!--LYRICS_HTML_END-->"),
                     ("/*LYRICS_JS_START*/", "/*LYRICS_JS_END*/"),
                     ("/*LYRICS_CALL_START*/", "/*LYRICS_CALL_END*/"),
                     ("/*LYRICS_INIT_START*/", "/*LYRICS_INIT_END*/")):
            html = re.sub(re.escape(a) + r".*?" + re.escape(b), "", html, flags=re.S)
    else:
        for mark in ("<!--LYRICS_HTML_START-->", "<!--LYRICS_HTML_END-->",
                     "/*LYRICS_JS_START*/", "/*LYRICS_JS_END*/",
                     "/*LYRICS_CALL_START*/", "/*LYRICS_CALL_END*/",
                     "/*LYRICS_INIT_START*/", "/*LYRICS_INIT_END*/"):
            html = html.replace(mark, "")

    repl = {
        "__CSS_ROOT__":     lay.css_root_block(),
        "__FONT_STACK__":   css_font_stack(),
        "__TINT_CSS__":     lay.tint_css(),
        "__SHEEN_CSS__":    lay.sheen_css(),
        "__CFG_JSON__":     json.dumps(lay.js_config(), ensure_ascii=False),
        "__TITLE__":        proj["title"],
        "__SUBTITLE__":     proj.get("subtitle", ""),
        "__LYRICS_JSON__":  json.dumps(lines, ensure_ascii=False),
        "__SPEC_FPS__":     str(DATA_FPS),
        "__DURATION__":     f"{duration:.3f}",
        "__SPEC_B64__":     base64.b64encode(spec.tobytes()).decode("ascii"),
        "__ART_B64__":      art_b64,
        "__MP3_B64__":      mp3_b64,
    }
    for k, v in repl.items():
        if k not in html:
            sys.exit(f"模板裡找不到佔位符 {k}，請檢查 {TEMPLATE}")
        html = html.replace(k, v)

    left = re.findall(r"__[A-Z0-9_]+__", html)
    if left:
        sys.exit(f"還有沒填的佔位符：{set(left)}")
    say("[4/5] 模板組裝完成，所有佔位符都已填入")

    # 5) 輸出
    out = os.path.join(project_dir, f"{proj['out_prefix']}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    say(f"[5/5] 已輸出：{out}（{os.path.getsize(out)/1e6:.1f} MB）")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法：python3 build_html.py <歌曲資料夾>")
    build(sys.argv[1])
