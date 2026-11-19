"""TronClass Word 匯入測試檔：確認填空題、題組裡的填空子題、單選題、LaTeX 公式都能匯入，以及數字答案怎麼判分。
以官方範本 小考\\期中考\\exam-word-import-zh-tw.docx 為底：保留第一段「@@Word匯入說明@@」（系統不匯入），
刪掉範例題目，換成測試題。
- 第 1～4 題：同一題、標準答案都是 80000，作答時各輸入一種寫法，一次測完判分方式
- 第 5 題：題組（含 2 格填空子題、承上題子題），題幹 LaTeX 用 $…$
- 第 6 題：單選題，題幹與選項 LaTeX 用 \\(…\\)
輸出：小考\\期中考\\Word匯入測試.docx
"""
import os
from docx import Document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '小考', '期中考', 'exam-word-import-zh-tw.docx')
OUT = os.path.join(ROOT, '小考', '期中考', 'Word匯入測試.docx')

VARIANTS = ['80000，標準答案', '80,000，加逗號', '８００００，全形數字', '一個半形空格再接 80000，前面多一個空格']
LINES = []
for k, v in enumerate(VARIANTS, 1):
    LINES += [
        '%d.【填空題】甲以每股 800 元買進 1 口股票期貨，每口代表 2,000 股，到期時期貨價格為 840 元。'
        '甲的損益為 _____ 元（測試用：這題請輸入 %s）（1分）' % (k, v),
        '答案：80000',
        '答案解釋：(840 − 800) × 2,000 = 80,000 元',
        '難易度：中',
    ]
LINES += [
    # 題組用 {{ }} 包起來，LaTeX 裡不能出現連續的 }} 或 {{，否則可能被當成題組結尾 → 用空格隔開
    '{{5.【題組】某股票連續 5 個月的月報酬為 3%、−1%、1%、3%、−1%。'
    '樣本標準差 $s=\\sqrt{ \\dfrac{\\sum_{i=1}^{n}(r_i-\\bar{r})^2}{n-1} }$，其中 $\\bar{r}$ 為平均、n 為資料筆數。',
    '難易度：中',
    '5.1【填空題】這 5 個月報酬的平均為 _____ %、樣本標準差為 _____ %（只填數字）（2分）',
    '答案：1；2',
    '答案解釋：平均 = 5% / 5 = 1%；偏差平方和 16，除以 4 得 4，開根號 = 2%',
    '難易度：中',
    '5.2【填空題】承上題，若月報酬互相獨立、分配相同，持有 4 個月的波動率為 _____ %（只填數字）（2分）',
    '答案：4',
    '答案解釋：變異數變 4 倍，標準差變 √4 = 2 倍：2% × 2 = 4%',
    '難易度：中}}',
    '6.【單選題】名目年利率 8%、每季複利一次，有效年利率 \\(R_{eff}=\\left(1+\\dfrac{R}{m}\\right)^{m}-1\\) 約為？'
    '（\\(1.02^{4}\\approx 1.0824\\)）（2分）',
    'A.7.92%',
    'B.8.00%',
    'C.8.16%',
    'D.\\(8.24\\%\\)',
    '答案：D',
    '答案解釋：(1 + 0.08/4)^4 − 1 = 8.24%',
    '難易度：中',
]


def main():
    doc = Document(SRC)
    body = doc.element.body
    paras = doc.paragraphs
    # 第一個說明區塊：從開頭到第一個以 @@ 結尾的段落
    end = next(i for i, p in enumerate(paras) if p.text.rstrip().endswith('@@'))
    for p in paras[end + 1:]:
        body.remove(p._element)
    for t in body.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl'):
        body.remove(t)
    for line in LINES:
        doc.add_paragraph(line)
    doc.save(OUT)
    # 題組區塊裡只能有結尾那一個 }}
    text = '\n'.join(p.text for p in Document(OUT).paragraphs)
    blk = text[text.index('{{'):text.index('}}') + 2]
    assert blk.count('}}') == 1 and blk.count('{{') == 1 and blk.rstrip().endswith('}}'), blk
    print(OUT)
    print(text[text.index('1.【'):])


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
