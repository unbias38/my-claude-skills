"""
regress.py —— 回歸測試：確認改了程式之後，畫面沒有跑掉。

這是整個開發過程的安全網。每次動完程式就跑一次，
它會用「合成的測試素材」把六套版面各畫幾格，跟上次確認過的結果比對。

執行方式：
    python3 tests/regress.py                    # 檢查全部六套版面
    python3 tests/regress.py --layouts 16x9,1x1 # 只檢查指定的
    python3 tests/regress.py --bless            # 把現在的結果訂為新基準

什麼時候該用 --bless（重新定基準）？
    當你「刻意」改了外觀而且確認新的比較好的時候。
    平常不要用 —— 那等於把測試的眼睛蒙起來。

基準怎麼存？
    存「指紋」（把整張圖算成一串代碼）而不是整張圖。
    原因：六套版面各七格的圖加起來超過 100MB，太肥而且不適合跟著 skill 散布。
    指紋只有幾十個位元組，卻能百分之百抓出任何一個像素的變化。
    另外附一張縮圖，測試沒過時可以用眼睛看個大概。

它同時檢查兩件事 —— 網頁版（瀏覽器截圖）和影片版（Python 畫圖）——
兩邊都比對，才能確保「共用設定檔」真的讓兩者同步。
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, SCRIPTS)

import webshot                                    # noqa: E402
from layout import Layout                         # noqa: E402

FIXTURE = os.path.join(HERE, "fixture")
BASELINE = os.path.join(HERE, "baseline")
WORK = os.path.join(HERE, "_work")
FAIL = os.path.join(HERE, "_fail")

ALL_LAYOUTS = ["16x9", "16x9-solo", "9x16", "9x16-solo", "1x1", "1x1-solo"]

# 挑這幾個時間點：還沒開唱、第一句、最長的一句、間奏（金色要收掉）、
# 間奏後回來、歌曲結束後。涵蓋所有會分支的狀況。
TIMES = [0.2, 1.2, 4.5, 9.0, 10.5, 11.8]

THUMB_W = 300   # 縮圖只是失敗時用眼睛看個大概，不用太大


def fingerprint(path):
    """把整張圖算成一串代碼。任何一個像素變了，代碼就會不同。"""
    a = np.asarray(Image.open(path).convert("RGB"))
    return hashlib.sha256(a.tobytes()).hexdigest()[:32], a.shape[1], a.shape[0]


def make_project(layout):
    """複製一份測試素材，把版面換成指定的那一套。"""
    d = os.path.join(WORK, layout)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(FIXTURE, d)
    p = os.path.join(d, "project.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["layout"] = layout
    json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return d


def run_layout(layout):
    """畫出這套版面的所有測試格，回傳 {檔名: 圖片路徑}。"""
    d = make_project(layout)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "prepare.py"), d],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "render_video.py"), d,
                    "--dump", ",".join(str(t) for t in TIMES),
                    "--dumpdir", os.path.join(d, "video")],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_html.py"), d],
                   check=True, stdout=subprocess.DEVNULL)
    webshot.shoot(os.path.join(d, "fixture.html"), TIMES, os.path.join(d, "web"))

    out = {}
    for kind in ("video", "web"):
        for n in sorted(os.listdir(os.path.join(d, kind))):
            if n.endswith(".png"):
                out[f"{kind}/{n}"] = os.path.join(d, kind, n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layouts", default=",".join(ALL_LAYOUTS))
    ap.add_argument("--bless", action="store_true")
    args = ap.parse_args()
    layouts = [x.strip() for x in args.layouts.split(",") if x.strip()]

    os.makedirs(BASELINE, exist_ok=True)
    shutil.rmtree(FAIL, ignore_errors=True)
    allok = True

    for layout in layouts:
        cfg = Layout.load(layout).cfg
        kind = "有歌詞" if cfg.get("has_lyrics", True) else "純音樂"
        print(f"\n【{layout}】{cfg['canvas']['w']}×{cfg['canvas']['h']}　{kind}")
        shots = run_layout(layout)

        bpath = os.path.join(BASELINE, f"{layout}.json")
        tdir = os.path.join(BASELINE, layout)

        if args.bless:
            base = {}
            shutil.rmtree(tdir, ignore_errors=True)
            os.makedirs(tdir, exist_ok=True)
            for name, p in shots.items():
                h, w, ht = fingerprint(p)
                base[name] = {"sha": h, "w": w, "h": ht}
                im = Image.open(p).convert("RGB")
                im.resize((THUMB_W, round(THUMB_W * im.height / im.width)),
                          Image.LANCZOS).save(
                    os.path.join(tdir, name.replace("/", "_") + ".jpg"),
                    quality=78)
            json.dump(base, open(bpath, "w", encoding="utf-8"), indent=2)
            print(f"  已建立基準：{len(base)} 格")
            continue

        if not os.path.exists(bpath):
            print("  還沒有基準，請先跑 --bless")
            allok = False
            continue
        base = json.load(open(bpath, encoding="utf-8"))
        bad = []
        for name, p in shots.items():
            h, w, ht = fingerprint(p)
            b = base.get(name)
            if b is None:
                bad.append(f"{name} 基準裡沒有這一格")
            elif (b["w"], b["h"]) != (w, ht):
                bad.append(f"{name} 尺寸變了 {b['w']}×{b['h']} → {w}×{ht}")
            elif b["sha"] != h:
                bad.append(f"{name} 畫面內容變了")
                os.makedirs(FAIL, exist_ok=True)
                shutil.copy(p, os.path.join(FAIL, f"{layout}_{name.replace('/','_')}"))
        missing = set(base) - set(shots)
        bad += [f"{m} 這次沒產生出來" for m in sorted(missing)]

        if bad:
            allok = False
            for m in bad:
                print("  ✗ " + m)
            print(f"  （不一致的畫面已存到 {FAIL} 可以直接看）")
        else:
            print(f"  ✓ {len(shots)} 格全部一致")

    shutil.rmtree(WORK, ignore_errors=True)
    print("\n" + "=" * 46)
    if args.bless:
        print("基準已建立完成")
        return 0
    print("回歸測試通過 ✅ 六套版面都跟基準一致" if allok
          else "回歸測試失敗 ❌ 上面列出了不一致的地方")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
