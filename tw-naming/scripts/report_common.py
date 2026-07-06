"""三支報告腳本（analyze_name / score_candidates / suggest_changes）共用的 markdown 片段。

只放純函式與常數 — 不做任何 module-level 執行（不載資料、不 parse args），
避免 import 副作用。資料載入一律由呼叫端在需要時觸發。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lucky_81 import info_of as lucky_info  # noqa: E402
from zodiac_explain import format_reference as _zodiac_format_reference  # noqa: E402

ASSETS = Path(__file__).parent.parent / "assets"

WUGE_KEYS = ["天格", "人格", "地格", "外格", "總格"]
TIANGE_NOTE = "（祖蔭，不參與主判）"


def load_sancai_content() -> dict:
    """Load johnwu Sancai.json for richer 三才 explanations.

    失敗（檔案不存在 / 壞 JSON）時印 stderr 警告並回空 dict —
    報告仍可產出，只是缺三才詳細解釋。不靜默吞、也不 crash。
    """
    path = ASSETS / "Sancai.json"
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = json.load(f)
        return {k: v for k, v in raw.items() if v is not None}
    except Exception as e:
        print(f"⚠️ 無法載入三才解釋資料 ({path.name}): {e}；報告將缺少三才詳細說明",
              file=sys.stderr)
        return {}


def overall_verdict(result: dict, ignore_tiange: bool = True) -> tuple[str, list[str]]:
    """整體判定：回傳 (verdict, 不利的格 key 清單)。"""
    keys = ["人格吉凶", "地格吉凶", "外格吉凶", "總格吉凶", "三才吉凶"]
    if not ignore_tiange:
        keys.insert(0, "天格吉凶")

    bad_keys = [k for k in keys if result.get(k) in ("凶", "大凶", "凶帶吉")]
    soso_keys = [k for k in keys if result.get(k) == "半吉"]
    good_keys = [k for k in keys if result.get(k) in ("大吉", "中吉")]

    if len(bad_keys) >= 3:
        verdict = "❌ 多格不利，建議改名"
    elif len(bad_keys) >= 1:
        problems = "、".join(k.replace("吉凶", "") for k in bad_keys)
        verdict = f"⚠️ {problems} 不利，建議檢視"
    elif len(soso_keys) >= 2:
        verdict = "🔸 中等，部分格半吉"
    elif len(good_keys) == len(keys):
        verdict = "✅ 全吉"
    else:
        verdict = "✅ 整體良好"

    return verdict, bad_keys


def kangxi_line(chars: list[str], strokes: list[int]) -> str:
    """康熙筆劃 header 行。"""
    return "**康熙筆劃**：" + "　・　".join(
        f"{c} {s} 劃" for c, s in zip(chars, strokes))


def wuge_table_md(wuge_numbers: dict, ignore_tiange: bool = True) -> list[str]:
    """五格 + 81 數理 markdown 表。

    wuge_numbers: 含「天格/人格/地格/外格/總格」→ 數字 的 dict
    （compute_wuge() 的回傳值可直接餵入）。
    """
    lines = ["| 格 | 數 | 吉凶 | 數名 | 含義 |",
             "|---|---|---|---|---|"]
    for key in WUGE_KEYS:
        n = wuge_numbers[key]
        grade, gname, gdesc = lucky_info(n)
        note = TIANGE_NOTE if (key == "天格" and ignore_tiange) else ""
        lines.append(f"| {key}{note} | {n} | {grade} | {gname} | {gdesc} |")
    return lines


def sancai_content_of(content_db: dict, sancai) -> str:
    """從 Sancai.json dict 取該三才組合的解釋文字（無則回空字串）。"""
    entry = content_db.get("".join(sancai)) or {}
    return (entry.get("content") or "").strip()


def sancai_block_md(sancai, grade: str, content: str = "") -> list[str]:
    """三才行 + 解釋 blockquote。sancai 為 3 個五行字的序列。"""
    lines = [f"**三才**：{sancai[0]}-{sancai[1]}-{sancai[2]}　**{grade}**"]
    if content:
        lines.append("")
        for para in content.strip().split("\n"):
            if para.strip():
                lines.append(f"> {para.strip()}")
    return lines


def zodiac_tag(total: int) -> str:
    """生肖總分 → 偏吉 / 偏忌 / 中性。"""
    return "偏吉" if total >= 1 else "偏忌" if total <= -1 else "中性"


def zodiac_reference_md(zodiac: str, heading_level: int = 2) -> list[str]:
    """生肖字根層級宜忌參考段（含 code fence，避免 raw 文字弄壞 markdown 渲染）。"""
    return [
        "#" * heading_level + " 生肖字根層級宜忌參考",
        "",
        "```",
        _zodiac_format_reference(zodiac),
        "```",
        "",
    ]


def disclaimer_md(intro: str,
                  include_zodiac: bool = False,
                  include_xiyongshen: bool = False,
                  include_avoid_note: bool = False,
                  final_line: str = "重大命名（新生兒、改名）建議由專業命理師最後確認",
                  ) -> list[str]:
    """免責「## 說明」段（依 taiwan-naming.md § 8 — 無內部術語）。

    生肖 / 喜用神條目為條件式 — 只有該次分析真的用到才輸出。
    """
    lines = ["---", "", "## 說明", "", intro, ""]
    lines.append("- 三才五格僅是傳統姓名學六大派之一，預測準確度約 56.6%")
    if include_zodiac:
        lines.append("- 生肖派宜忌僅為附加參考，因派別爭議較大未列入主判定")
    lines.append("- 天格代表祖蔭，由姓氏決定不可改，主判定不納入")
    if include_xiyongshen:
        lines.append("- 喜用神判定靠粗略推算，非命理師判斷")
    if include_avoid_note:
        lines.append("- 父母 / 祖輩名字避諱請自行確認後告知")
    lines.append(f"- {final_line}")
    return lines
