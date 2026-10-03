#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全形標點＋禁破折號驗證：文件產出後必跑，退出碼非 0 一律不交付。
抓出兩類問題：
  1) 「中文字旁邊出現半形標點」（數字／英文之間的半形標點不算錯）。
  2) 全文出現破折號（單個、雙連或 en dash）。硬性規則：一律不得使用破折號。
會先濾掉 <style>／<script> 與 HTML 標籤，只檢查可見文字。
用法：python scripts/validate_punct.py <檔案.md 或 .html>
"""
import re
import sys

HALF = {',': '，', ';': '；', ':': '：', '!': '！', '?': '？', '(': '（', ')': '）'}
CJK = r'\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'
DASH = re.compile(r'——|—|–')  # U+2014 雙／單 em dash、U+2013 en dash


def _blank_keep_lines(m):
    return '\n' * m.group(0).count('\n')


def check(path: str) -> int:
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    t = re.sub(r'<style[^>]*>.*?</style>', _blank_keep_lines, raw, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<script[^>]*>.*?</script>', _blank_keep_lines, t, flags=re.DOTALL | re.IGNORECASE)

    issues = []   # 半形標點夾中文
    dashes = []   # 破折號
    for lineno, line in enumerate(t.splitlines(), 1):
        text = re.sub(r'<[^>]+>', '', line)
        for ch, full in HALF.items():
            for m in re.finditer(re.escape(ch), text):
                i = m.start()
                before = text[i - 1] if i > 0 else ''
                after = text[i + 1] if i + 1 < len(text) else ''
                if re.match(f'[{CJK}]', before) or re.match(f'[{CJK}]', after):
                    snippet = text[max(0, i - 12):i + 12].strip()
                    issues.append((lineno, ch, full, snippet))
        for m in DASH.finditer(text):
            snippet = text[max(0, m.start() - 12):m.start() + 12].strip()
            dashes.append((lineno, m.group(0), snippet))

    if not issues and not dashes:
        print('✅ 全形標點驗證通過，中文裡沒有半形標點，也沒有破折號。')
        return 0

    if issues:
        print(f'⚠️  發現 {len(issues)} 處中文裡的半形標點（應改全形）：\n')
        for lineno, ch, full, snippet in issues:
            print(f'  L{lineno}: 半形「{ch}」應為全形「{full}」 → …{snippet}…')
    if dashes:
        print(f'\n⚠️  發現 {len(dashes)} 處破折號（硬性規則：一律不得使用，請改全形句號／逗號／冒號／頓號）：\n')
        for lineno, d, snippet in dashes:
            print(f'  L{lineno}: 破折號「{d}」 → …{snippet}…')
    return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法：python scripts/validate_punct.py <檔案.md 或 .html>')
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
