#!/usr/bin/env python3
"""
codelab-handout：把 Markdown 講義變成 Google Codelabs 風格的單檔 HTML。

使用方式（從 skill 根目錄執行）：
    python3 scripts/build.py 輸入檔.md [-o 輸出檔.html]

如果沒給 -o，會自動用輸入檔同層的 .html 為預設輸出。
注意：成品不允許輸出到本 skill 資料夾內（避免污染 git repo）。

Markdown 格式範例：

    ---
    title: 我的講義
    duration: 90
    authors: 老師名字
    ---

    ## 第一步：暖身
    Duration: 5

    內容...

    ## 第二步：實作
    Duration: 15

    ```python
    print("hello")
    ```

每個 ## 就是一個章節（會在左側目錄出現一個項目）。
Duration 是該段預估分鐘數（會顯示在標題旁）。
"""

import sys
import re
import html
import argparse
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("缺少套件：請先執行 pip3 install --break-system-packages markdown")


# ──────────────────────────────────────────────────────────────
# 步驟 1：解析 frontmatter（檔案開頭 --- 之間的 YAML 風格設定）
# ──────────────────────────────────────────────────────────────
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """把 markdown 開頭的 --- 區塊抽出來變成字典，回傳 (meta, body)。"""
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
    return meta, body


# ──────────────────────────────────────────────────────────────
# 步驟 2：把 markdown 內文按 H2 切成一個個章節
# ──────────────────────────────────────────────────────────────
def split_steps(body: str) -> list[dict]:
    """
    把 markdown 按 ## 標題切開。
    每個章節包含 title、duration、md（章節主體）。
    """
    # 用 lookahead 把每個 H2 當切點，第一段（H2 之前）會被丟掉
    parts = re.split(r"(?m)^##\s+", body)
    steps = []
    for chunk in parts[1:]:  # 第 0 塊是 H2 之前的東西（通常是 H1），不要
        lines = chunk.split("\n", 1)
        title = lines[0].strip()
        rest = lines[1] if len(lines) > 1 else ""

        # 抓 Duration: 5  或  Duration: 0:05 這行
        duration = None
        m = re.search(r"(?im)^Duration:\s*(.+)$", rest)
        if m:
            raw = m.group(1).strip()
            # 0:05 → 5；單純數字直接用
            if ":" in raw:
                h, mi = raw.split(":", 1)
                try:
                    duration = int(h) * 60 + int(mi) if int(h) > 0 else int(mi)
                except ValueError:
                    duration = None
            else:
                try:
                    duration = int(raw.split()[0])
                except ValueError:
                    duration = None
            rest = re.sub(r"(?im)^Duration:.*\n?", "", rest, count=1)

        steps.append({
            "title": title,
            "duration": duration,
            "md": rest.strip(),
        })
    return steps


# ──────────────────────────────────────────────────────────────
# 步驟 3：把每個章節的 markdown 轉成 HTML，並包好 code-block 外框
# ──────────────────────────────────────────────────────────────
def md_to_html(md_text: str) -> str:
    """用 markdown 套件轉，並把 <pre> 外面包一層 .code-block 給 JS 加複製按鈕。"""
    md = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists"])
    raw = md.convert(md_text)
    # 把每個 <pre>...</pre> 包成 <div class="code-block"><pre>...</pre></div>
    raw = re.sub(
        r"(<pre>.*?</pre>)",
        r'<div class="code-block">\1</div>',
        raw,
        flags=re.DOTALL,
    )
    return raw


# ──────────────────────────────────────────────────────────────
# 步驟 4：產生目錄 (TOC) 和章節 HTML
# ──────────────────────────────────────────────────────────────
def slugify(text: str, idx: int) -> str:
    """把章節標題變成 anchor id，純英文比較保險，中文就用流水號。"""
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip()
    s = re.sub(r"\s+", "-", s)
    if not s or re.search(r"[一-鿿]", s):
        return f"step-{idx + 1}"
    return s.lower()


def build_toc(steps: list[dict]) -> str:
    lines = []
    for i, s in enumerate(steps):
        anchor = slugify(s["title"], i)
        lines.append(f'      <li><a href="#{anchor}">{html.escape(s["title"])}</a></li>')
    return "\n".join(lines)


def build_steps_html(steps: list[dict]) -> str:
    out = []
    for i, s in enumerate(steps):
        anchor = slugify(s["title"], i)
        dur = f'<div class="duration">{s["duration"]} 分鐘</div>' if s["duration"] else ""
        body = md_to_html(s["md"])

        # 上一步 / 下一步 連結
        nav_parts = ['<div class="step-nav">']
        if i > 0:
            prev_anchor = slugify(steps[i - 1]["title"], i - 1)
            nav_parts.append(f'<a href="#{prev_anchor}">← 上一步</a>')
        else:
            nav_parts.append('<span></span>')
        nav_parts.append('<div class="spacer"></div>')
        if i < len(steps) - 1:
            next_anchor = slugify(steps[i + 1]["title"], i + 1)
            nav_parts.append(f'<a href="#{next_anchor}">下一步 →</a>')
        else:
            nav_parts.append('<span></span>')
        nav_parts.append('</div>')
        nav_html = "\n".join(nav_parts)

        out.append(
            f'<section class="step" id="{anchor}">\n'
            f'  <h2>{html.escape(s["title"])}</h2>\n'
            f'  {dur}\n'
            f'  {body}\n'
            f'  {nav_html}\n'
            f'</section>'
        )
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Markdown 講義 → Codelabs 風 HTML")
    parser.add_argument("input", help="輸入的 .md 檔")
    parser.add_argument(
        "-o", "--output",
        help="輸出的 .html 檔（預設同名置於輸入檔旁；但不允許輸出在 skill 資料夾內）",
    )
    args = parser.parse_args()

    src = Path(args.input).resolve()
    # build.py 現在在 scripts/，所以 skill 資料夾要往上一層
    skill_dir = Path(__file__).parent.parent.resolve()

    if not src.exists():
        sys.exit(f"找不到檔案：{src}")

    out_path = (Path(args.output).resolve() if args.output
                else src.with_suffix(".html").resolve())

    # ── 守門：禁止把成品寫到 skill 資料夾裡 ──
    # （這個 skill 之後要分享到 GitHub，產出物會弄髒 repo）
    try:
        out_path.relative_to(skill_dir)
        sys.exit(
            "❌ 不允許把成品輸出到 skill 資料夾內。\n"
            f"   skill 資料夾：{skill_dir}\n"
            f"   想輸出到：     {out_path}\n\n"
            "   請用 -o 指定外部路徑，例如：\n"
            f"   python3 scripts/build.py {args.input} -o ~/Documents/講義.html"
        )
    except ValueError:
        pass  # 不在 skill 資料夾內，放行

    text = src.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    # 如果 frontmatter 沒給 title，就抓第一個 H1
    title = meta.get("title")
    if not title:
        m = re.search(r"(?m)^#\s+(.+)$", body)
        title = m.group(1).strip() if m else src.stem

    steps = split_steps(body)
    if not steps:
        sys.exit("找不到任何 ## 章節，請至少寫一個 ## 標題。")

    total_steps = len(steps)
    total_duration = sum(s["duration"] or 0 for s in steps)
    if not total_duration and meta.get("duration"):
        try:
            total_duration = int(meta["duration"])
        except ValueError:
            total_duration = 0

    template_path = skill_dir / "assets" / "template.html"
    template = template_path.read_text(encoding="utf-8")

    html_out = (
        template
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{TOTAL_STEPS}}", str(total_steps))
        .replace("{{TOTAL_DURATION}}", str(total_duration) if total_duration else "—")
        .replace("{{TOC_ITEMS}}", build_toc(steps))
        .replace("{{STEPS_HTML}}", build_steps_html(steps))
    )

    out_path.write_text(html_out, encoding="utf-8")
    print(f"✅ 輸出：{out_path}")
    print(f"   {total_steps} 個章節 · 共 {total_duration} 分鐘")


if __name__ == "__main__":
    main()
