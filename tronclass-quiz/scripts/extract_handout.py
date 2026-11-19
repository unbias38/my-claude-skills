"""從講義 PPTX 抽出現成的練習題（隨堂小測驗、牛刀小試），輸出 JSON 供出題用。

用法：python extract_handout.py <deck.pptx> [out.json]

隨堂小測驗頁的辨識方式：
  - 題目框內有「N. 題幹」段落，後面接「(A) …」～「(D) …」四段
  - 答案形狀命名為 Ans{k}Num（內容「N.」）與 Ans{k}Letter（內容「A」～「D」）
牛刀小試頁的辨識方式：
  - 有一個文字恰為「牛刀小試」的標籤形狀，以及一個「解答」標籤
  - 題目是「牛刀小試」標籤之後第一個非空文字框，解答是「解答」標籤之後第一個非空文字框
  - 「答：」開頭的文字框是最後答案；標題形狀為「牛刀小試｜主題」
另外會標出題幹裡依賴課本或講義編號的措辭（圖 1.2、公式 2.7、定理、例題…），出題時要改寫。
"""
import json, re, sys
from pptx import Presentation

OPT = re.compile(r'^\s*\(([A-E])\)\s?(.*)$')
DEPEND = re.compile(r'(圖|表|公式|定理|例題|式)\s*[\d０-９]+[\.\-－．]?\d*|課本|教科書|講義第')


def section_of(texts):
    for t in texts:
        m = re.match(r'^(\d+\.\d+)', t.strip())
        if m:
            return m.group(1)
    return ''


def main(path, out=None):
    prs = Presentation(path)
    items, trial = [], 0
    for si, s in enumerate(prs.slides, 1):
        shapes = [sh for sh in s.shapes if sh.has_text_frame]
        texts = [sh.text_frame.text for sh in shapes if sh.text_frame.text.strip()]
        names = {sh.name: sh.text_frame.text.strip() for sh in shapes}
        sec = section_of(texts)
        if 'Ans1Letter' in names:
            letters = {}
            for k in range(1, 20):
                if 'Ans%dNum' % k in names:
                    letters[int(names['Ans%dNum' % k].rstrip('.'))] = names['Ans%dLetter' % k]
            box = next(sh for sh in shapes if re.match(r'^\d+\.\s', sh.text_frame.text) and '(A)' in sh.text_frame.text)
            cur = None
            for p in box.text_frame.paragraphs:
                t = p.text
                m = re.match(r'^(\d+)\.\s*(.*)$', t)
                om = OPT.match(t)
                if m and not om:
                    cur = dict(kind='quiz', no=int(m.group(1)), slide=si, section=sec, stem=m.group(2).strip(), options={})
                    items.append(cur)
                elif om and cur is not None:
                    cur['options'][om.group(1)] = om.group(2).strip()
                elif cur is not None and t.strip():
                    cur['stem'] += t.strip()
            for it in items:
                if it['kind'] == 'quiz' and it['slide'] == si:
                    it['answer'] = letters.get(it['no'], '?')
            continue
        st = [t.strip() for t in texts]
        if '牛刀小試' in st and '解答' in st:
            i, j = st.index('牛刀小試'), st.index('解答')
            trial += 1
            title = next((t for t in st if t.startswith('牛刀小試｜')), '').replace('牛刀小試｜', '')
            items.append(dict(kind='trial', no=trial, slide=si, section=sec, title=title,
                              question=st[i + 1], solution=st[j + 1],
                              answer_line=next((t for t in st if t.startswith('答：')), '')))
    for it in items:
        txt = it.get('stem', '') + ' ' + it.get('question', '')
        hits = sorted(set(m.group(0) for m in DEPEND.finditer(txt)))
        if hits:
            it['depends_on_book'] = hits
    js = json.dumps(items, ensure_ascii=False, indent=1)
    if out:
        open(out, 'w', encoding='utf-8').write(js)
    nq = sum(1 for x in items if x['kind'] == 'quiz'); nt = len(items) - nq
    print('隨堂小測驗 %d 題、牛刀小試 %d 題' % (nq, nt), file=sys.stderr)
    for x in items:
        if x.get('depends_on_book'):
            print('  依賴編號措辭：%s %s %s' % (x['kind'], x['no'], x['depends_on_book']), file=sys.stderr)
    if not out:
        print(js)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    main(*sys.argv[1:])
