"""把題目 JSON 寫成 TronClass 批次匯入 .xls（格式同官方範本「導入題庫官方範本.xls」）。

用法：python build_quiz.py <questions.json> <out.xls> [--seed N]

questions.json：
{
  "seed": 3,                       # 選填，答案重排的亂數種子
  "items": [
    {"src": "講義1",               # 來源標記：講義N／講義牛刀N／課本N（只用於報表與比例統計，不寫進 xls）
     "diff": "易",                 # 易／中／難
     "stem": "題幹（圖片寫 @@檔名.png@@）",
     "answer": "正解選項文字",
     "wrong": ["錯誤選項1", "錯誤選項2", "錯誤選項3"],
     "fixed": null,                # 或四個選項的固定順序（數字選項由小到大、含「以上皆是」「選項(A)(B)」者）
     "expl": "正確答案解釋（附講義節次）"}
  ]
}

做的事：
  - 可重排題的正解位置依計畫分配，讓 A～D 平均、同一字母最多連續 2 題；fixed 題保持原順序
  - 檢查：每題 4 個選項且不重複、正解在選項內、題幹圖片檔存在於輸出資料夾、題幹沒有依賴編號的措辭
  - 印出答案序列、講義／課本比例、難易度題數，以及讓總分剛好 100 的整數配分組合
"""
import json, os, random, re, sys
from collections import Counter
import xlwt

L = 'ABCD'
DEPEND = re.compile(r'(圖|表|公式|定理|例題)\s*[\d０-９]+[\.\-－．]?\d*|課本|教科書|依講義')
NOTE = ('注意事項：\n1.當前可以批量匯入的題目類型有：單選題，複選題，是非題三種。請嚴格按照這些專有名詞來填寫。\n'
        '2.下方列表的題型、題幹、難易度、答案為必填。題目選項和答案全部用英文大寫字母，是非題的答案用A,B表示，A是正確，B是錯誤。\n'
        '3.多選題答案多於一個時，答案之間用“,”(英文逗號)分隔。\n'
        '4.如果題幹或者選項中包含圖片，圖片用“@@1531106595775.jpg@@”。\n'
        '5.同一份試卷的圖片跟 Excel需放置於同一資料夾內。')
HEAD = ['題型*', '題幹*', '難易度*', '答案*', '正確答案解釋', '選項-A', '選項-B', '選項-C', '選項-D', '選項-E', '選項-F', '選項-G']


def plan(items, seed):
    fixed = {i: q['fixed'].index(q['answer']) for i, q in enumerate(items) if q.get('fixed')}
    rng = random.Random(seed)
    n = len(items)
    for _ in range(500000):
        base = [i % 4 for i in range(n)]
        rng.shuffle(base)
        ok = True
        for i, a in fixed.items():
            if base[i] != a:
                j = next((j for j in range(n) if j not in fixed and base[j] == a), None)
                if j is None:
                    ok = False; break
                base[i], base[j] = base[j], base[i]
        if not ok:
            continue
        if any(base[i] == base[i - 1] == base[i - 2] for i in range(2, n)):
            continue
        return base
    raise RuntimeError('排不出符合條件的答案序列（固定題太多？）')


def scoring(cnt):
    """回傳讓總分 = 100 的整數配分（難度越高分數越高），最多 5 組。"""
    levels = [d for d in ('易', '中', '難') if cnt.get(d)]
    res = []
    def rec(k, prev, used, acc):
        if k == len(levels):
            if used == 100: res.append(acc)
            return
        for s in range(prev + 1, 101):
            u = used + s * cnt[levels[k]]
            if u > 100: break
            rec(k + 1, s, u, acc + [(levels[k], s)])
    rec(0, 0, 0, [])
    res.sort(key=lambda r: max(s for _, s in r) - min(s for _, s in r))
    return res[:5]


def main(src, out, seed=None):
    data = json.load(open(src, encoding='utf-8'))
    items = data['items']
    seed = seed if seed is not None else data.get('seed', 1)
    outdir = os.path.dirname(os.path.abspath(out))
    problems = []
    for i, q in enumerate(items, 1):
        opts = q['fixed'] if q.get('fixed') else [q['answer']] + q['wrong']
        if len(opts) != 4 or len(set(opts)) != 4:
            problems.append('第 %d 題選項不是 4 個不重複的選項' % i)
        if q['answer'] not in opts:
            problems.append('第 %d 題正解不在選項內' % i)
        if q['diff'] not in ('易', '中', '難'):
            problems.append('第 %d 題難易度要寫 易／中／難' % i)
        for img in re.findall(r'@@(.+?)@@', q['stem']):
            if not os.path.exists(os.path.join(outdir, img)):
                problems.append('第 %d 題的圖 %s 不在輸出資料夾' % (i, img))
        hit = DEPEND.search(q['stem'])
        if hit:
            problems.append('第 %d 題題幹有依賴編號的措辭「%s」，請改寫成題目本身看得懂' % (i, hit.group(0)))
    if problems:
        print('\n'.join(problems)); sys.exit(1)

    target = plan(items, seed)
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('繁體中文')
    wrap = xlwt.easyxf('alignment: wrap on, vert top')
    ws.write(0, 0, NOTE, wrap)
    ws.write(1, 0, '請根據上方的規則進行填寫。')
    for c, h in enumerate(HEAD):
        ws.write(2, c, h)
    key = []
    for i, q in enumerate(items):
        if q.get('fixed'):
            opts = list(q['fixed'])
        else:
            w = list(q['wrong']); random.Random(100 + i).shuffle(w)
            opts = w[:target[i]] + [q['answer']] + w[target[i]:]
        letter = L[opts.index(q['answer'])]
        assert letter == L[target[i]]
        for c, v in enumerate(['單選題', q['stem'], q['diff'], letter, q.get('expl', '')] + opts):
            ws.write(3 + i, c, v, wrap)
        key.append((i + 1, q.get('src', ''), letter, q['diff']))
    ws.col(1).width = 256 * 60; ws.col(4).width = 256 * 40
    for c in range(5, 9):
        ws.col(c).width = 256 * 28
    wb.save(out)

    n = len(key)
    nh = sum(1 for k in key if k[1].startswith('講義')); nb = sum(1 for k in key if k[1].startswith('課本'))
    cnt = Counter(k[3] for k in key)
    print(out)
    print('答案序列', ''.join(k[2] for k in key), dict(sorted(Counter(k[2] for k in key).items())))
    print('講義 %d（%.0f%%）、課本 %d（%.0f%%），共 %d 題' % (nh, 100 * nh / n, nb, 100 * nb / n, n))
    print('難易度', {d: cnt[d] for d in ('易', '中', '難') if cnt[d]})
    sc = scoring(cnt)
    if 100 % n == 0:
        print('配分：每題 %d 分即 100 分' % (100 // n))
    for r in sc:
        print('配分', '、'.join('%s %d 分' % x for x in r), '＝100')
    if not sc:
        print('配分：找不到難度遞增的整數組合，可考慮小數或調整難易度標記')
    for k in key:
        print(*k)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    seed = None
    if '--seed' in a:
        k = a.index('--seed'); seed = int(a[k + 1]); del a[k:k + 2]
    main(a[0], a[1], seed)
