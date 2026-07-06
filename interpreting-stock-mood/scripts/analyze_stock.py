"""
股票溝通師 — 股價特徵 + 新聞 + 社群熱度提取器
==================================================

這個腳本是「股票溝通師」skill 的後台引擎。它的工作很單純：
拿一支股票的客觀資料（價格、技術指標、新聞、社群熱度），
打包成 JSON 輸出，讓 Claude 後續可以據此寫出擬人化的「溝通報告」。

用法：
    python analyze_stock.py <股票代號> [中文搜尋詞]

範例：
    python analyze_stock.py 2330                # 台股 4 位數字會自動補 .TW
    python analyze_stock.py 2330.TW
    python analyze_stock.py 2330 台積電         # 第二個參數會給 Google Trends 用
    python analyze_stock.py AAPL                # 美股直接給代號
    python analyze_stock.py 0050 元大台灣50     # ETF 也支援

第二個參數（中文搜尋詞）的用途：
    yfinance 給的台股 longName 是英文全名（例：Taiwan Semiconductor Manufacturing Company Limited），
    但台灣人在 Google 上實際搜尋時用的是「台積電」。
    如果不提供這個參數，腳本會 fallback 用 yfinance 給的 longName。
    建議呼叫者（Claude）在呼叫腳本前，先把使用者熟悉的中文簡稱猜好傳進來。

設計原則（Graceful Fallback / 容錯）：
    每個資料源都包在自己的 try/except 裡。
    pytrends 被 Google 擋？trends 欄位回 null，主流程不中斷。
    yfinance 抓不到？整支腳本回 error（這是必要的，因為核心資料缺失）。

輸出：一個 JSON 物件，印到 stdout。
"""

from __future__ import annotations

import json
import logging
import os
import sys
import warnings
from datetime import datetime
from typing import Any

# 抑制 pandas/yfinance 的 deprecation warning，避免污染 JSON 輸出
warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


def _silence_stderr():
    """把 stderr 暫時關掉（避免 yfinance 警告污染 JSON 輸出）。
    僅在直接執行時呼叫；被 import 時不會自動關 stderr。
    """
    if not os.environ.get("STOCK_DEBUG"):
        sys.stderr = open(os.devnull, "w")


# ============================================================
# Step A：標準化股票代號
# ============================================================
# 為什麼需要標準化？
#   使用者可能輸入 "2330"、"2330.TW"、"aapl"、" AAPL " 各種格式。
#   yfinance 在抓台股時需要 ".TW" 後綴；美股則不用。
#   所以這裡做一個簡單的判斷：純 4-6 位數字就視為台股，補 .TW。
def normalize_symbol(raw: str) -> str:
    """把使用者輸入的代號正規化成 yfinance 可以接受的格式。

    支援的台股格式：
      - 純數字 4-6 位（一般股票/ETF）：2330 → 2330.TW
      - 數字 + L/R 後綴（槓桿/反向 ETF）：00631L → 00631L.TW、00632R → 00632R.TW
      - 已有 .TW/.HK/.T 後綴：直接用
    """
    import re
    s = raw.strip().upper()

    # 已有後綴（.TW / .HK / .T 等），直接回傳
    if "." in s:
        return s

    # 台股格式判斷：
    #   - 純數字 4-6 位（如 2330、0050、00929）
    #   - 數字結尾接 L 或 R（如 00631L、00632R 槓桿/反向 ETF）
    if re.match(r"^\d{4,6}[LR]?$", s):
        return f"{s}.TW"

    # 其他（美股、英文代號等）原樣回傳
    return s


# ============================================================
# Step B：抓股價歷史 + 公司資訊（yfinance 主力）
# ============================================================
def fetch_price_history(symbol: str) -> tuple[Any, dict, str | None]:
    """
    用 yfinance 抓最近 6 個月的股價歷史 + 公司基本資訊。

    回傳 (DataFrame, info_dict, error_message)
    成功時 error_message 為 None，失敗時 DataFrame/info 為 None、error 有訊息。
    """
    try:
        import yfinance as yf  # type: ignore
        ticker = yf.Ticker(symbol)

        # 抓最近 6 個月的日 K（足夠算 60 日均線、20 日波動率等）
        hist = ticker.history(period="6mo", auto_adjust=True)

        if hist is None or hist.empty:
            return None, {}, f"yfinance 抓不到 {symbol} 的歷史資料（代號可能錯誤或下市）"

        # 公司基本資訊（名稱、產業、市值等）
        # yfinance 的 info 偶爾會慢或失敗，包另一層 try
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        return hist, info, None

    except ImportError:
        return None, {}, "yfinance 未安裝（pip install yfinance）"
    except Exception as e:
        return None, {}, f"yfinance 錯誤：{e}"


# ============================================================
# Step C：計算技術指標
# ============================================================
# 為什麼把每個指標寫成獨立函式？
#   1. 容易測試
#   2. 哪個指標壞掉，其他還是能算
#   3. 教學時可以一個一個講解
def calculate_ma(close, window):
    """簡單移動平均（Simple Moving Average）：window 天的收盤平均。"""
    return close.rolling(window=window).mean()


def calculate_rsi(close, period=14):
    """
    RSI（相對強弱指數）：衡量「最近上漲動能 vs 下跌動能」的比例。
    > 70 通常被視為超買、< 30 超賣。但這只是參考，不是買賣訊號。

    公式：RSI = 100 - 100 / (1 + RS)，其中 RS = 平均上漲幅度 / 平均下跌幅度
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)  # 避免除以零
    return 100 - (100 / (1 + rs))


def calculate_macd(close, fast=12, slow=26, signal=9):
    """
    MACD（指數平滑異同移動平均）：兩條 EMA 的差距 + 訊號線。
    DIF（快慢線差） > DEA（訊號線）→ 多頭氛圍
    DIF < DEA → 空頭氛圍
    DIF 由下穿上 DEA = 黃金交叉、由上穿下 = 死亡交叉
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    histogram = dif - dea
    return dif, dea, histogram


def calculate_kd(high, low, close, period=9, smooth=3):
    """
    KD（隨機指標 / Stochastic Oscillator）：
    K 線：今天的 RSV（收盤在最近 9 日高低點區間的位置）的指數平滑
    D 線：K 的指數平滑
    都在 0-100 之間，> 80 超買、< 20 超賣。
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    rsv = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, 1e-10)
    k = rsv.ewm(alpha=1/smooth, adjust=False).mean()
    d = k.ewm(alpha=1/smooth, adjust=False).mean()
    return k, d


def calculate_bollinger(close, window=20, num_std=2):
    """
    布林通道：以 20 日均線為中軸，上下各 2 倍標準差。
    股價貼上軌可能短期過熱，貼下軌可能短期超賣。
    """
    mid = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def compute_technicals(hist) -> dict:
    """把上面所有指標一次算完，整理成方便輸出的字典。"""
    import numpy as np

    close = hist["Close"]
    high = hist["High"]
    low = hist["Low"]
    volume = hist["Volume"]

    # 均線
    ma5 = calculate_ma(close, 5)
    ma20 = calculate_ma(close, 20)
    ma60 = calculate_ma(close, 60)

    # RSI / MACD / KD
    rsi = calculate_rsi(close, 14)
    macd_dif, macd_dea, macd_hist = calculate_macd(close)
    k, d = calculate_kd(high, low, close)

    # 布林
    bb_upper, bb_mid, bb_lower = calculate_bollinger(close)

    # 取最新值
    latest_close = float(close.iloc[-1])
    latest_volume = int(volume.iloc[-1])
    avg_volume_20 = float(volume.rolling(20).mean().iloc[-1])

    # 近 N 日報酬
    def pct_return(days):
        if len(close) < days + 1:
            return None
        return float((close.iloc[-1] / close.iloc[-1 - days] - 1) * 100)

    # 近 60 日最高最低
    last_60 = close.tail(60)
    high_60 = float(last_60.max())
    low_60 = float(last_60.min())
    pos_in_range = (latest_close - low_60) / (high_60 - low_60) if high_60 > low_60 else 0.5

    # 年化波動率（用近 20 日日報酬的標準差 × √252）
    daily_returns = close.pct_change().dropna()
    vol_20 = float(daily_returns.tail(20).std() * (252 ** 0.5) * 100) if len(daily_returns) >= 20 else None

    # 趨勢判斷：看三條均線的相對位置
    def trend_label():
        """多頭排列：MA5 > MA20 > MA60；空頭排列反之；其他叫盤整/糾結"""
        if any(np.isnan(x) for x in [ma5.iloc[-1], ma20.iloc[-1], ma60.iloc[-1]]):
            return "資料不足"
        if ma5.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1]:
            return "多頭排列"
        if ma5.iloc[-1] < ma20.iloc[-1] < ma60.iloc[-1]:
            return "空頭排列"
        return "盤整/糾結"

    # MACD 狀態
    def macd_label():
        if np.isnan(macd_dif.iloc[-1]) or np.isnan(macd_dea.iloc[-1]):
            return "資料不足"
        # 看最近 3 天有沒有交叉
        recent = macd_dif - macd_dea
        if recent.iloc[-1] > 0 and recent.iloc[-3] <= 0:
            return "剛出現黃金交叉"
        if recent.iloc[-1] < 0 and recent.iloc[-3] >= 0:
            return "剛出現死亡交叉"
        if recent.iloc[-1] > 0:
            return "多頭氛圍（DIF 在 DEA 上方）"
        return "空頭氛圍（DIF 在 DEA 下方）"

    # 布林通道位置
    def bb_label():
        if np.isnan(bb_upper.iloc[-1]):
            return "資料不足"
        if latest_close >= bb_upper.iloc[-1] * 0.98:
            return "貼近上軌（短期可能過熱）"
        if latest_close <= bb_lower.iloc[-1] * 1.02:
            return "貼近下軌（短期可能超賣）"
        return "在中軸附近"

    # 量價關係（看最近 5 天）
    # 注意：如果今天是當日盤中，最新一根 K 線的 volume 還沒累積完，
    # 用最後 5 天的「平均量」就會被拉低。所以判斷時用「上一個完整交易日」做比較。
    def volume_price_label():
        if len(close) < 6:
            return "資料不足"
        # 用倒數第 6 ~ 倒數第 2 天（5 個完整交易日）做比較，避免當日未完成資料污染
        recent_close = close.iloc[-6:-1]
        recent_volume = volume.iloc[-6:-1]
        price_up = recent_close.iloc[-1] > recent_close.iloc[0]
        avg_recent_vol = recent_volume.mean()
        avg_prev_vol = volume.iloc[-26:-6].mean()  # 再前面 20 天
        if avg_prev_vol == 0 or np.isnan(avg_prev_vol):
            return "資料不足"
        vol_up = avg_recent_vol > avg_prev_vol * 1.1
        if price_up and vol_up:
            return "量增價漲（健康上攻）"
        if price_up and not vol_up:
            return "量縮價漲（漲勢動能不足，留意背離）"
        if not price_up and vol_up:
            return "量增價跌（賣壓重）"
        return "量縮價跌（恐慌期可能尾聲，但仍弱勢）"

    return {
        "price": {
            "latest_close": round(latest_close, 2),
            "latest_volume": latest_volume,
            "high_60d": round(high_60, 2),
            "low_60d": round(low_60, 2),
            "position_in_60d_range_pct": round(pos_in_range * 100, 1),
            "return_5d_pct": round(pct_return(5), 2) if pct_return(5) is not None else None,
            "return_20d_pct": round(pct_return(20), 2) if pct_return(20) is not None else None,
            "return_60d_pct": round(pct_return(60), 2) if pct_return(60) is not None else None,
        },
        "trend": {
            "ma5": round(float(ma5.iloc[-1]), 2) if not np.isnan(ma5.iloc[-1]) else None,
            "ma20": round(float(ma20.iloc[-1]), 2) if not np.isnan(ma20.iloc[-1]) else None,
            "ma60": round(float(ma60.iloc[-1]), 2) if not np.isnan(ma60.iloc[-1]) else None,
            "label": trend_label(),
            "above_ma5": bool(latest_close > ma5.iloc[-1]) if not np.isnan(ma5.iloc[-1]) else None,
            "above_ma20": bool(latest_close > ma20.iloc[-1]) if not np.isnan(ma20.iloc[-1]) else None,
            "above_ma60": bool(latest_close > ma60.iloc[-1]) if not np.isnan(ma60.iloc[-1]) else None,
        },
        "momentum": {
            "rsi14": round(float(rsi.iloc[-1]), 1) if not np.isnan(rsi.iloc[-1]) else None,
            "macd_dif": round(float(macd_dif.iloc[-1]), 3) if not np.isnan(macd_dif.iloc[-1]) else None,
            "macd_dea": round(float(macd_dea.iloc[-1]), 3) if not np.isnan(macd_dea.iloc[-1]) else None,
            "macd_label": macd_label(),
            "k": round(float(k.iloc[-1]), 1) if not np.isnan(k.iloc[-1]) else None,
            "d": round(float(d.iloc[-1]), 1) if not np.isnan(d.iloc[-1]) else None,
        },
        "volatility": {
            "annualized_pct": round(vol_20, 1) if vol_20 is not None else None,
            "bollinger_label": bb_label(),
            "bb_upper": round(float(bb_upper.iloc[-1]), 2) if not np.isnan(bb_upper.iloc[-1]) else None,
            "bb_lower": round(float(bb_lower.iloc[-1]), 2) if not np.isnan(bb_lower.iloc[-1]) else None,
        },
        "volume": {
            "latest": latest_volume,
            "avg_20d": int(avg_volume_20) if not np.isnan(avg_volume_20) else None,
            "ratio_to_20d": round(latest_volume / avg_volume_20, 2) if avg_volume_20 and not np.isnan(avg_volume_20) else None,
            "label": volume_price_label(),
            # 旗標：如果最新一筆量遠低於 20 日均量（< 50%），可能是當日盤中尚未完成
            # Claude 在解讀時應該優先用 label（已用前一日量計算），不要被 ratio_to_20d 誤導
            "intraday_partial_warning": (
                avg_volume_20 and not np.isnan(avg_volume_20)
                and latest_volume < avg_volume_20 * 0.5
            ),
        },
    }


# ============================================================
# Step D：抓 yfinance 內建新聞
# ============================================================
def fetch_news_yfinance(symbol: str) -> tuple[list, dict]:
    """
    yfinance 的 .news 屬性會抓 Yahoo Finance 上的相關新聞。
    台股新聞極少（Yahoo Finance 國際版幾乎不收 tw.stock.yahoo.com 的中文新聞），
    美股覆蓋率較好但 Yahoo 也常 401/429 被當成空陣列吞掉。

    回傳 (新聞列表, 診斷字典)。
      - 新聞列表每筆：{title, publisher, date, link, source: "yfinance"}
      - 診斷字典：{status, message, raw_count, parsed_count}
        status:
          - "ok"                 解析到 ≥1 筆
          - "empty"              API 真的回空陣列（可能真的沒新聞，也可能被 silent rate-limit）
          - "structure_unreadable" 回了 N 筆但所有 title 都讀不到（yfinance 又改 schema）
          - "exception"          網路 / 套件 / 內部錯誤
    """
    diag = {"source": "yfinance", "status": "exception",
            "message": "", "raw_count": 0, "parsed_count": 0}
    try:
        import yfinance as yf  # type: ignore
        ticker = yf.Ticker(symbol)

        # 不同版本的 yfinance API 不太一樣，兩種都試
        try:
            news = ticker.news
        except Exception:
            news = ticker.get_news()

        if not news:
            diag["status"] = "empty"
            diag["message"] = "yfinance 回空陣列（可能真無新聞，也可能被 Yahoo silent rate-limit）"
            return [], diag

        diag["raw_count"] = len(news)

        cleaned = []
        for n in news[:10]:
            # yfinance 的新聞欄位在不同版本之間有差異，盡量穩健地讀
            title = n.get("title") or n.get("content", {}).get("title", "")
            publisher = n.get("publisher") or n.get("content", {}).get("provider", {}).get("displayName", "")
            ts = n.get("providerPublishTime") or n.get("content", {}).get("pubDate", "")
            link = n.get("link") or n.get("content", {}).get("canonicalUrl", {}).get("url", "")

            # 時間戳轉可讀格式
            if isinstance(ts, (int, float)):
                ts_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            elif isinstance(ts, str):
                ts_str = ts[:10]
            else:
                ts_str = ""

            if title:
                cleaned.append({
                    "title": title,
                    "publisher": publisher,
                    "date": ts_str,
                    "link": link,
                    "source": "yfinance",
                })

        diag["parsed_count"] = len(cleaned)
        if not cleaned:
            diag["status"] = "structure_unreadable"
            diag["message"] = (f"yfinance 回了 {len(news)} 筆但所有 title 都讀不到 —— "
                                "可能 schema 又改版，請檢查 yfinance 版本")
        else:
            diag["status"] = "ok"
            diag["message"] = f"成功解析 {len(cleaned)}/{len(news)} 筆"
        return cleaned, diag

    except Exception as e:
        diag["status"] = "exception"
        diag["message"] = f"yfinance 例外：{type(e).__name__}: {e}"
        return [], diag


def fetch_news_google_rss(symbol: str, name_zh: str | None) -> tuple[list, dict]:
    """
    Google News RSS 備援。

    優點：
    - 不需 API key
    - RSS 是 W3C 標準，結構比 yfinance 內部 API 穩定得多
    - 對台股中文新聞覆蓋率遠高於 yfinance

    缺點：
    - 結果是依關鍵字搜尋，可能混入不相關的同名新聞（要靠別名清單收斂）
    - 偶爾被 Google 限流（這時當 google_rss empty 處理）

    回傳 (新聞列表, 診斷字典)，shape 與 fetch_news_yfinance 一致。
    每筆 source 欄位 = "google_rss"。
    """
    diag = {"source": "google_rss", "status": "exception",
            "message": "", "raw_count": 0, "parsed_count": 0}
    try:
        import urllib.request
        import urllib.parse
        import xml.etree.ElementTree as ET

        # 組查詢字串：別名清單前 3 個 OR 串起來；若沒有別名只用代號
        query_terms: list[str] = []
        if name_zh:
            for alias in [a.strip() for a in name_zh.split(",") if a.strip()][:3]:
                query_terms.append(alias)
        # 一定加上「不含 .TW 的純代號」
        clean_symbol = symbol.replace(".TW", "").replace(".TWO", "")
        if clean_symbol not in query_terms:
            query_terms.append(clean_symbol)
        query = " OR ".join(query_terms)

        # 台股 / 美股 用不同地區參數
        is_taiwan = symbol.endswith(".TW") or symbol.endswith(".TWO") or (clean_symbol.isdigit() and len(clean_symbol) <= 5)
        if is_taiwan:
            params = {"q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
        else:
            params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}

        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
        diag["query"] = query

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_bytes = resp.read()

        root = ET.fromstring(xml_bytes)
        items = root.findall(".//item")
        diag["raw_count"] = len(items)

        cleaned = []
        for item in items[:10]:
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            source_el = item.find("source")

            title = title_el.text if title_el is not None and title_el.text else ""
            link = link_el.text if link_el is not None and link_el.text else ""

            # 解析 RFC 822 日期 → YYYY-MM-DD
            ts_str = ""
            if pub_el is not None and pub_el.text:
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_el.text)
                    ts_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    ts_str = pub_el.text[:16]

            publisher = (source_el.text if source_el is not None and source_el.text else "Google News")

            if title:
                cleaned.append({
                    "title": title,
                    "publisher": publisher,
                    "date": ts_str,
                    "link": link,
                    "source": "google_rss",
                })

        diag["parsed_count"] = len(cleaned)
        if not cleaned:
            diag["status"] = "empty"
            diag["message"] = f"Google News RSS 對 [{query}] 無命中"
        else:
            diag["status"] = "ok"
            diag["message"] = f"Google News RSS 取得 {len(cleaned)} 筆（query=[{query}]）"
        return cleaned, diag

    except Exception as e:
        diag["status"] = "exception"
        diag["message"] = f"Google News RSS 例外：{type(e).__name__}: {e}"
        return [], diag


def fetch_news(symbol: str, name_zh: str | None) -> tuple[list, list]:
    """
    新聞抓取總入口：先試 yfinance，台股或 yfinance 抓不到時加 Google News RSS 補強。

    回傳 (合併後的新聞列表, 診斷清單)。
    診斷清單是兩個來源的 status dict 列表，呼叫端可塞進 result["news_sources"]
    讓使用者看到哪些來源試了、結果如何。

    合併策略：
    - 美股：yfinance 結果若 ≥3 筆，直接用；否則加 RSS
    - 台股：永遠加 RSS（yfinance 對台股覆蓋極差）
    - 結果以 RSS 在前、yfinance 在後排列，最多 10 筆
    """
    yf_news, yf_diag = fetch_news_yfinance(symbol)
    diags = [yf_diag]

    is_taiwan = symbol.endswith(".TW") or symbol.endswith(".TWO")
    need_rss = is_taiwan or len(yf_news) < 3

    if need_rss:
        rss_news, rss_diag = fetch_news_google_rss(symbol, name_zh)
        diags.append(rss_diag)
        # RSS 在前（台股中文新聞優先），yfinance 在後
        merged = (rss_news + yf_news)[:10]
    else:
        merged = yf_news[:10]

    return merged, diags


# ============================================================
# Step E：抓 Google Trends 熱度（pytrends）
# ============================================================
def fetch_google_trends(symbol: str, name: str, custom_search_term: str | None = None) -> tuple[dict | None, str | None]:
    """
    用 pytrends 抓最近 30 天的 Google 搜尋熱度走勢。

    搜尋詞優先順序：
      1. custom_search_term（呼叫者明確指定）。可傳逗號分隔的別名清單
         （例「台積電,台積,TSMC」），此時只取第一個別名（慣例上是最正式的
         中文名）—— Google Trends 一次只查一個詞，塞整串反而查不到東西
      2. yfinance 給的公司名稱（去掉「股份有限公司」等冗餘後綴）
      3. 後備：股票代號本身

    Google Trends 對股票代號的搜尋資料通常很稀疏，用公司中文名效果好得多。
    所以建議呼叫者（Claude）盡量提供台灣人熟悉的中文簡稱。

    回傳 (trends_dict, error_message)。
    被 Google 擋或失敗時 trends_dict 為 None、error 有訊息。
    """
    try:
        import re
        from pytrends.request import TrendReq  # type: ignore

        # 選搜尋關鍵字：custom > yfinance name > 代號
        # custom_search_term 可能是逗號分隔的別名清單（例「台積電,台積,TSMC」），
        # 只取第一個別名（=最正式的中文名）給 Trends 用
        search_term = ""
        if custom_search_term and custom_search_term.strip():
            search_term = re.split(r"[,，]", custom_search_term)[0].strip()
        if not search_term:
            search_term = (name or "").strip() or symbol.split(".")[0]

        # 簡化中文名稱（很多時候 yfinance 給的台股名稱會包含「股份有限公司」之類冗餘）
        for suffix in ["股份有限公司", "公司", "Limited", "Inc", "Inc.", "Corporation", "Corp", "Corp."]:
            if search_term.endswith(suffix):
                search_term = search_term.replace(suffix, "").strip()

        # 台股 .TW（上市）/.TWO（上櫃）→ 用台灣地區 + 中文介面
        # 美股 → 用美國地區 + 英文介面
        if symbol.endswith((".TW", ".TWO")):
            geo, hl = "TW", "zh-TW"
        else:
            geo, hl = "US", "en-US"

        pytrends = TrendReq(hl=hl, tz=480, timeout=(10, 25))
        pytrends.build_payload(
            kw_list=[search_term],
            timeframe="today 1-m",  # 最近 30 天
            geo=geo,
        )
        df = pytrends.interest_over_time()

        if df is None or df.empty:
            return None, f"Google Trends 沒有 '{search_term}' 的資料"

        # 取出搜尋熱度欄位（去掉 isPartial）
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        values = df[search_term].tolist()
        if not values:
            return None, "Google Trends 回傳空資料"

        # 計算走勢標籤：比較最近 7 天平均 vs 前面 21 天平均
        recent_avg = sum(values[-7:]) / max(len(values[-7:]), 1)
        earlier_avg = sum(values[:-7]) / max(len(values[:-7]), 1) if len(values) > 7 else recent_avg

        if earlier_avg == 0:
            ratio = 1.0
        else:
            ratio = recent_avg / earlier_avg

        if ratio > 1.5:
            trend_label = "飆升（近 7 日明顯熱度上升）"
        elif ratio > 1.15:
            trend_label = "上升"
        elif ratio < 0.6:
            trend_label = "驟降"
        elif ratio < 0.85:
            trend_label = "下滑"
        else:
            trend_label = "平穩"

        return {
            "search_term": search_term,
            "geo": geo,
            "values": values,                 # 原始時序值（0-100）
            "latest": values[-1],
            "max": max(values),
            "min": min(values),
            "recent_7d_avg": round(recent_avg, 1),
            "earlier_avg": round(earlier_avg, 1),
            "trend_label": trend_label,
        }, None

    except ImportError:
        return None, "pytrends 未安裝（pip install pytrends）"
    except Exception as e:
        return None, f"pytrends 錯誤（可能被 Google 暫時擋住）：{e}"


# ============================================================
# Step F：警訊偵測
# ============================================================
def detect_warnings(hist, technicals: dict) -> list[str]:
    """
    根據技術指標偵測幾個經典警訊模式。
    每個警訊都對應 SKILL.md 裡的一條，輸出時 Claude 應該對應顯示 ⚠️。
    """
    warnings_list = []
    import numpy as np

    close = hist["Close"]
    volume = hist["Volume"]

    # 1) 爆量長黑：當日量 > 20MA 量 1.5×，且當日跌幅 > 3%
    if len(close) >= 20:
        avg_vol_20 = volume.rolling(20).mean().iloc[-1]
        today_vol = volume.iloc[-1]
        today_return = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) >= 2 else 0
        if (
            not np.isnan(avg_vol_20)
            and today_vol > avg_vol_20 * 1.5
            and today_return < -3
        ):
            warnings_list.append(
                f"⚠️ 爆量長黑：今日量是 20 日均量的 {today_vol/avg_vol_20:.1f}× ，跌幅 {today_return:.1f}%"
            )

    # 2) 跌破 60 日線：最近 5 日內從上方跌穿
    if technicals["trend"]["ma60"] is not None and len(close) >= 65:
        ma60_series = close.rolling(60).mean()
        was_above = (close.iloc[-7:-1] > ma60_series.iloc[-7:-1]).sum() >= 4
        is_below_now = close.iloc[-1] < ma60_series.iloc[-1]
        if was_above and is_below_now:
            warnings_list.append(
                f"⚠️ 跌破 60 日均線：原本站在 60MA 上方，最近跌破（中期支撐失守）"
            )

    # 3) 量價背離：股價創 20 日新高但量沒跟上
    if len(close) >= 20:
        is_20d_high = close.iloc[-1] >= close.tail(20).max() * 0.999
        avg_vol_20 = volume.rolling(20).mean().iloc[-2]  # 用前一日的均量比
        if (
            is_20d_high
            and not np.isnan(avg_vol_20)
            and volume.iloc[-1] < avg_vol_20 * 0.85
        ):
            warnings_list.append(
                "⚠️ 量價背離：價創 20 日新高但量縮（漲勢動能不足）"
            )

    # 4) 死亡交叉（MACD 角度）
    if technicals["momentum"]["macd_label"] == "剛出現死亡交叉":
        warnings_list.append("⚠️ MACD 死亡交叉：DIF 由上穿下 DEA（短期動能轉弱）")

    # 5) 5MA 跌破 20MA（短中期均線死亡交叉）
    if len(close) >= 21:
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        if (
            not np.isnan(ma5.iloc[-1])
            and not np.isnan(ma20.iloc[-1])
            and ma5.iloc[-1] < ma20.iloc[-1]
            and ma5.iloc[-3] >= ma20.iloc[-3]
        ):
            warnings_list.append("⚠️ 短期均線死亡交叉：5MA 跌穿 20MA")

    # 6) RSI 超買區拉回
    rsi_now = technicals["momentum"]["rsi14"]
    if rsi_now is not None and len(close) >= 20:
        # 重新算近期 RSI 看高點
        from numpy import isnan
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi_series = 100 - (100 / (1 + rs))
        recent_max = rsi_series.tail(5).max()
        if not isnan(recent_max) and recent_max > 80 and rsi_now < recent_max - 5:
            warnings_list.append(
                f"⚠️ RSI 超買區拉回：近 5 日 RSI 最高 {recent_max:.0f}，已回落到 {rsi_now:.0f}"
            )

    return warnings_list


# ============================================================
# Step G：human-readable 觀察文字
# ============================================================
def build_notes(technicals: dict) -> list[str]:
    """把技術指標翻譯成「人話」，給 Claude 在最後輸出時直接引用。"""
    notes = []

    trend = technicals["trend"]
    if trend["label"] == "多頭排列":
        notes.append("均線多頭排列（5MA > 20MA > 60MA），趨勢結構偏強")
    elif trend["label"] == "空頭排列":
        notes.append("均線空頭排列（5MA < 20MA < 60MA），趨勢結構偏弱")
    elif trend["label"] == "盤整/糾結":
        notes.append("均線糾結，方向不明朗（盤整中）")

    # 站幾條均線之上
    above_count = sum(1 for k in ["above_ma5", "above_ma20", "above_ma60"] if trend.get(k))
    if above_count == 3:
        notes.append("股價站上所有均線")
    elif above_count == 0:
        notes.append("股價跌破所有均線")

    # 動能
    momentum = technicals["momentum"]
    if momentum["rsi14"] is not None:
        rsi = momentum["rsi14"]
        if rsi > 70:
            notes.append(f"RSI {rsi:.0f}（超買區）")
        elif rsi < 30:
            notes.append(f"RSI {rsi:.0f}（超賣區）")
    if momentum["macd_label"]:
        notes.append(f"MACD：{momentum['macd_label']}")

    # 波動率
    vol = technicals["volatility"]["annualized_pct"]
    if vol is not None:
        if vol < 20:
            notes.append(f"年化波動率 {vol:.0f}%（溫和）")
        elif vol < 40:
            notes.append(f"年化波動率 {vol:.0f}%（中等）")
        else:
            notes.append(f"年化波動率 {vol:.0f}%（劇烈）")

    # 量價
    notes.append(f"量價關係：{technicals['volume']['label']}")

    # 60 日區間位置
    pos = technicals["price"]["position_in_60d_range_pct"]
    if pos is not None:
        if pos > 80:
            notes.append(f"位於近 60 日區間 {pos:.0f}% 位置（接近高點）")
        elif pos < 20:
            notes.append(f"位於近 60 日區間 {pos:.0f}% 位置（接近低點）")

    return notes


# ============================================================
# Step H：新聞密度（從 yfinance.news 已抓的資料計算）
# ============================================================
# 想法：「最近 3 天新聞數」vs「過去 27 天每 3 天平均」 = 媒體熱度倍率
# 倍率 > 2 → 媒體熱度上升、可能有重要事件
# 這個指標完全用本地資料算，不爬蟲、不被擋、最穩
def compute_news_density(news_list: list) -> dict | None:
    """從新聞列表算媒體熱度密度。回傳 dict 或 None（資料不足時）。

    注意：yfinance.news 通常只回傳最近 5-10 則新聞，不會給 30 天前的，
    所以「過去 27 天平均」這個分母經常是 0。本函式改用比較務實的算法：
    - 若新聞全部都是近 3 天內的（很常見）：標「最近 3 天有 X 則新聞」，不算 ratio
    - 若有跨期新聞：才算 ratio 和趨勢
    """
    if not news_list:
        return None

    from datetime import datetime, timedelta
    today = datetime.now().date()
    cutoff_3d = today - timedelta(days=3)
    cutoff_30d = today - timedelta(days=30)

    recent_3d = 0
    earlier_27d = 0
    total_with_date = 0
    for n in news_list:
        date_str = n.get("date", "")
        if not date_str or len(date_str) < 10:
            continue
        try:
            news_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        total_with_date += 1
        if news_date >= cutoff_3d:
            recent_3d += 1
        elif cutoff_30d <= news_date < cutoff_3d:
            earlier_27d += 1

    if total_with_date == 0:
        return None

    # 沒有跨期資料：只能講「最近 3 天有幾則」
    if earlier_27d == 0:
        if recent_3d >= 5:
            label = f"近 3 日有 {recent_3d} 則新聞（密度高，可能有重要事件）"
        elif recent_3d >= 2:
            label = f"近 3 日有 {recent_3d} 則新聞（一般水準）"
        else:
            label = f"近 3 日只有 {recent_3d} 則新聞"
        return {
            "recent_3d_count": recent_3d,
            "earlier_27d_count": 0,
            "ratio": None,
            "label": label,
            "note": "yfinance 提供的新聞多為最近數日內，無歷史對比",
        }

    # 有跨期資料：算 ratio
    earlier_3d_equivalent = earlier_27d * 3 / 27
    ratio = recent_3d / earlier_3d_equivalent if earlier_3d_equivalent > 0 else 0

    if ratio >= 3:
        label = "媒體熱度飆升（近 3 日新聞密度遠高於平常）"
    elif ratio >= 1.5:
        label = "媒體熱度上升"
    elif ratio >= 0.7:
        label = "媒體熱度平穩"
    else:
        label = "媒體冷清（近 3 日新聞少於平常）"

    return {
        "recent_3d_count": recent_3d,
        "earlier_27d_count": earlier_27d,
        "ratio": round(ratio, 2),
        "label": label,
    }


# ============================================================
# Step I：PTT 股板熱度（爬蟲，免 API key）
# ============================================================
# 想法：抓 PTT Stock 板最近 N 頁的文章標題，數提及該股票代號或中文名的次數。
# 這個比 Google Trends 對台股更準，因為股板使用者就是投資人，不是路人。
def fetch_ptt_stock_heat(symbol: str, name_zh: str | None, n_pages: int = 5) -> tuple[dict | None, str | None]:
    """
    爬 PTT Stock 板最近 n_pages 頁的標題，計算提及次數。

    Args:
        symbol: 股票代號（"2330.TW" 或 "AAPL"）
        name_zh: 中文名或別名清單。支援兩種格式：
                 - 單一名稱：「聯發科」
                 - 逗號分隔多個別名：「聯發科,聯發,MTK,MediaTek」（V2.1 新增）
        n_pages: 要翻幾頁（每頁約 20 篇）

    回傳 (dict 或 None, error_message)
    """
    try:
        import urllib.request
        import re

        # === 提取要搜尋的關鍵字 ===
        # 來源 1：股票代號（去 .TW）—— 台股 4-6 位數字才搜
        # 來源 2：使用者傳的 name_zh，可以是單一名稱或逗號分隔多別名
        keywords = []
        # 取「.」前的裸代號（同時支援 .TW 上市與 .TWO 上櫃；不能用 replace(".TW","")，
        # 否則 "5483.TWO" 會變成 "5483O"）
        bare_symbol = symbol.split(".")[0].strip()
        if bare_symbol.isdigit():
            keywords.append(bare_symbol)

        if name_zh and name_zh.strip():
            # 支援逗號分隔的多別名（例：「聯發科,聯發,MTK,MediaTek」）
            # 全形和半形逗號都支援
            raw_names = re.split(r"[,，]", name_zh)
            for raw in raw_names:
                clean = raw.strip()
                # 去掉「股份有限公司」等冗餘
                for suffix in ["股份有限公司", "公司"]:
                    if clean.endswith(suffix):
                        clean = clean.replace(suffix, "").strip()
                if clean and clean not in keywords:
                    keywords.append(clean)

        if not keywords:
            return None, "PTT 抓取：沒有可搜尋的關鍵字"

        # 從 index.html（最新頁）開始往前翻
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        current_url = "https://www.ptt.cc/bbs/Stock/index.html"
        total_titles = 0
        mentions = 0
        sample_titles = []  # 收集有提到的標題給輸出
        # 各別名命中次數 — 讓使用者知道哪個關鍵字最有效、哪些可能該調整
        keyword_hits: dict[str, int] = {kw: 0 for kw in keywords}

        # === V3.1：retry 機制 ===
        # PTT 偶爾會 timeout 或 Cloudflare challenge，給 3 次嘗試機會
        # 第 1 次失敗 → 等 2 秒 → 第 2 次失敗 → 等 4 秒 → 第 3 次（最後一次）
        import time as _time

        def fetch_with_retry(url: str, max_retries: int = 3) -> str:
            """抓 URL 最多重試 max_retries 次。"""
            last_err = None
            for attempt in range(max_retries):
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        return resp.read().decode("utf-8")
                except Exception as e:
                    last_err = e
                    if attempt < max_retries - 1:
                        _time.sleep(2 * (attempt + 1))  # 漸進式 backoff
            raise last_err

        for _ in range(n_pages):
            html = fetch_with_retry(current_url)

            # 提取標題（PTT 標題在 <div class="title"> 裡）
            titles = re.findall(r'class="title">\s*(?:<a[^>]*>)?([^<]+)', html)
            for t in titles:
                t_clean = t.strip()
                if not t_clean or t_clean.startswith("(已被"):
                    continue
                total_titles += 1
                # 看標題有沒有任何關鍵字、哪些命中
                hit_in_this = [kw for kw in keywords if kw in t_clean]
                if hit_in_this:
                    mentions += 1
                    for kw in hit_in_this:
                        keyword_hits[kw] += 1
                    if len(sample_titles) < 5:
                        sample_titles.append(t_clean[:60])

            # 找上一頁
            prev_match = re.search(r'href="(/bbs/Stock/index\d+\.html)"[^>]*>&lsaquo;', html)
            if not prev_match:
                break
            current_url = "https://www.ptt.cc" + prev_match.group(1)

        # V3.4：頁面抓到了但一篇標題都沒解析出來 → 視為失敗而非「0 提及」。
        # 否則會產生「PTT 冷清」的偽訊號（其實是 HTML 結構改版、regex 失效）。
        if total_titles == 0:
            return None, "PTT 抓到頁面但解析出 0 篇標題（HTML 結構可能改版）"

        rate = mentions / total_titles if total_titles else 0
        if rate >= 0.10:
            label = "PTT 散戶熱議（每 10 篇就有 1 篇提到）"
        elif rate >= 0.05:
            label = "PTT 有熱度"
        elif rate >= 0.01:
            label = "PTT 偶有討論"
        else:
            # V2.1：搜不到時提供具體搜尋資訊，方便使用者判斷是否要再加別名
            label = f"PTT 冷清（搜 {keywords} 在最近 {n_pages} 頁 {total_titles} 篇標題未中；散戶或許在內文討論）"

        return {
            "keywords_searched": keywords,        # 實際搜尋的所有關鍵字
            "keyword_hits": keyword_hits,         # 各別名各命中幾次
            "pages_scanned": n_pages,
            "total_titles": total_titles,
            "mentions": mentions,
            "mention_rate_pct": round(rate * 100, 2),
            "sample_titles": sample_titles,
            "label": label,
        }, None

    except Exception as e:
        return None, f"PTT 抓取失敗：{e}"


# ============================================================
# Step J：Yahoo 股市留言板總數（股票知名度代理）
# ============================================================
# 想法：Yahoo 個股頁面有「檢視留言（X 個）」公開可見，
# 雖然是歷史累計（不是即時熱度），但可以當「股票知名度」「長期討論度」指標。
def fetch_yahoo_community_count(symbol: str) -> tuple[dict | None, str | None]:
    """抓 Yahoo 股市個股頁面的留言總數。回傳 dict 或 None。"""
    try:
        import urllib.request
        import re

        url = f"https://tw.stock.yahoo.com/quote/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        # V3.1：同樣加 retry（Yahoo 偶爾也會 timeout）
        import time as _time
        last_err = None
        html = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                break
            except Exception as e:
                last_err = e
                if attempt < 2:
                    _time.sleep(2 * (attempt + 1))
        if html is None:
            raise last_err

        # 找「檢視留言（X 個）」或類似格式
        # Yahoo 可能用全形或半形括號、可能有逗號千分位
        m = re.search(r"檢視留言[（(]\s*([\d,]+)\s*個?[)）]", html)
        if not m:
            # 備用：找「留言」前後的數字
            m = re.search(r"([\d,]+)\s*則?留言", html)
        if not m:
            return None, "Yahoo 留言數：未找到留言計數欄位"

        count = int(m.group(1).replace(",", ""))
        if count >= 5000:
            label = "高知名度（留言數破萬等級的熱門股）"
        elif count >= 1000:
            label = "知名度高"
        elif count >= 200:
            label = "知名度中等"
        else:
            label = "冷門（討論累積少）"

        return {
            "total_messages": count,
            "label": label,
            "note": "歷史累計留言數，反映長期關注度（非即時熱度）",
        }, None

    except Exception as e:
        return None, f"Yahoo 留言數抓取失敗：{e}"


# ============================================================
# Step K：TWSE 三大法人買賣超（台股專屬）
# ============================================================
# 想法：法人「真金白銀」的買賣方向比散戶聲量更有重量。
# 散戶熱（PTT 熱）+ 法人賣超 → 警訊（散戶在追高，法人在出貨）
# 散戶冷 + 法人買超 → 法人悄悄進場（可能是價值區）
def fetch_institutional_flow(symbol: str) -> tuple[dict | None, str | None]:
    """從 TWSE 公開 API 抓最近一個交易日的三大法人買賣超。僅台股有效。"""
    if not symbol.endswith(".TW"):
        return None, "三大法人：僅台股 (.TW) 有資料"

    try:
        import urllib.request
        import json
        from datetime import datetime, timedelta

        bare_symbol = symbol.replace(".TW", "")

        # TWSE 法人買賣超 T86 表，倒推日期找最近有資料的交易日
        # （週末、假日沒有資料，最多倒推 5 天）
        for days_back in range(1, 6):
            date_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
            url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json"
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                req = urllib.request.Request(url, headers=headers)
                data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            except Exception:
                continue

            if data.get("stat") != "OK":
                continue

            rows = data.get("data", [])
            if not rows:
                continue

            # 找該股票
            target_row = None
            for r in rows:
                if r and r[0].strip() == bare_symbol:
                    target_row = r
                    break
            if not target_row:
                # 那天可能該股票沒有法人異動，繼續往前找
                continue

            # V3.4：欄位索引改用 fields 動態解析，不再硬編（TWSE 曾調整過欄位順序）。
            # 對照歷來的固定索引：4 外陸資買賣超、7 外資自營商買賣超、
            # 10 投信買賣超、11 自營商買賣超合計、18 三大法人買賣超。
            # 注意「自營商買賣超股數」在 fields 裡是合計欄（另有「(自行買賣)」「(避險)」
            # 兩個帶後綴的分項欄，exact match 不會誤中）。
            fields = data.get("fields", [])

            def field_index(col_name):
                try:
                    return fields.index(col_name)
                except ValueError:
                    return None

            idx_foreign = field_index("外陸資買賣超股數(不含外資自營商)")
            idx_foreign_dealer = field_index("外資自營商買賣超股數")
            idx_trust = field_index("投信買賣超股數")
            idx_dealer = field_index("自營商買賣超股數")
            idx_total = field_index("三大法人買賣超股數")

            if None in (idx_foreign, idx_foreign_dealer, idx_trust, idx_dealer, idx_total):
                # 欄名找不到 = 結構又改版了 → 拒絕解析，寧缺勿錯
                return None, "T86 欄位結構改版，拒絕解析"

            def parse_int(s):
                """把 '1,234,567' 轉成 1234567。失敗回 0。"""
                try:
                    return int(s.replace(",", "").strip()) if s else 0
                except (ValueError, AttributeError):
                    return 0

            foreign = parse_int(target_row[idx_foreign]) + parse_int(target_row[idx_foreign_dealer])
            trust = parse_int(target_row[idx_trust])
            dealer = parse_int(target_row[idx_dealer])
            total = parse_int(target_row[idx_total])

            # 判讀標籤
            def direction(n):
                if n > 0:
                    return f"買超 {n:,} 股"
                if n < 0:
                    return f"賣超 {abs(n):,} 股"
                return "中性"

            # 法人總方向
            if total > 0:
                total_label = f"三大法人合計買超 {total:,} 股"
                stance = "法人偏多"
            elif total < 0:
                total_label = f"三大法人合計賣超 {abs(total):,} 股"
                stance = "法人偏空"
            else:
                total_label = "三大法人合計中性"
                stance = "法人中性"

            return {
                "trade_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
                "foreign_net": foreign,
                "foreign_label": direction(foreign),
                "trust_net": trust,
                "trust_label": direction(trust),
                "dealer_net": dealer,
                "dealer_label": direction(dealer),
                "total_net": total,
                "total_label": total_label,
                "stance": stance,
            }, None

        return None, "三大法人：最近 5 天都沒抓到資料（可能連假）"

    except Exception as e:
        return None, f"三大法人抓取失敗：{e}"


# ============================================================
# Step L：多維熱度整合判讀
# ============================================================
# 想法：把 PTT、Yahoo、新聞密度、量比、三大法人、（pytrends 若有）整合在一起。
# 重點是「散戶 vs 法人方向是否一致」這個交叉判讀，因為這正是專業 vs 業餘的差別訊號。
def build_heat_summary(
    ptt: dict | None,
    yahoo: dict | None,
    news_density: dict | None,
    institutional: dict | None,
    volume_info: dict,
    trends: dict | None,
    return_60d_pct: float | None,
) -> dict:
    """整合多源熱度，給出交叉判讀。"""
    summary = {
        "sources_available": [],
        "retail_heat": None,        # 散戶熱度（PTT + Yahoo + Trends 綜合）
        "media_heat": None,         # 媒體熱度（新聞密度）
        "market_heat": None,        # 市場熱度（量比）
        "institutional_stance": None,  # 法人方向
        "cross_check": [],          # 散戶 vs 法人等交叉判讀
    }

    # 散戶熱度
    retail_signals = []
    if ptt:
        summary["sources_available"].append("PTT 股板")
        retail_signals.append(ptt["label"])
    if yahoo:
        summary["sources_available"].append("Yahoo 個股")
        retail_signals.append(yahoo["label"])
    if trends:
        summary["sources_available"].append("Google Trends")
        retail_signals.append(f"Google 搜尋熱度：{trends.get('trend_label', '')}")
    if retail_signals:
        summary["retail_heat"] = retail_signals

    # 媒體熱度
    if news_density:
        summary["sources_available"].append("新聞密度")
        summary["media_heat"] = news_density["label"]

    # 市場熱度
    vol_label = volume_info.get("label", "")
    summary["market_heat"] = vol_label

    # 法人方向
    if institutional:
        summary["sources_available"].append("三大法人")
        summary["institutional_stance"] = institutional["stance"]

    # === 交叉判讀（最有價值的部分）===
    # 注意：#1/#2 都要求 total_titles > 0（雙保險）——
    # 解析出 0 篇標題時 fetch 端已回 None，但這裡再守一次，避免把「沒抓到」當「真的冷清」。
    # 1. 散戶熱（PTT 提及率 >= 3%）+ 法人賣 → 危險訊號
    if ptt and ptt.get("total_titles", 0) > 0 and ptt.get("mention_rate_pct", 0) >= 3 and institutional and institutional["total_net"] < 0:
        summary["cross_check"].append(
            f"⚠️ 散戶熱議 (PTT {ptt['mention_rate_pct']}%) + {institutional['total_label']}：典型的「散戶在追、法人在出」風險組合"
        )

    # 2. 散戶冷 + 法人買 → 法人悄悄進場
    if ptt and ptt.get("total_titles", 0) > 0 and ptt.get("mention_rate_pct", 0) < 1 and institutional and institutional["total_net"] > 0:
        summary["cross_check"].append(
            "💡 散戶冷清 + 法人買超：法人可能在散戶不注意時悄悄佈局"
        )

    # 2b. 短期暴漲（60d > 50%）+ 法人賣超 → 法人獲利了結
    if (
        return_60d_pct is not None
        and return_60d_pct > 50
        and institutional
        and institutional["total_net"] < 0
    ):
        summary["cross_check"].append(
            f"⚠️ 60 日內暴漲 {return_60d_pct:.0f}% + 法人賣超：法人可能在高位獲利了結"
        )

    # 2c. 法人巨量賣超（> 1000 萬股）→ 不論散戶熱度都值得提醒
    if institutional and institutional["total_net"] < -10_000_000:
        summary["cross_check"].append(
            f"🏛⚠️ {institutional['total_label']}（單日量很大，建議留意賣壓來源）"
        )

    # 2d. 法人巨量買超（> 1000 萬股）→ 同上
    if institutional and institutional["total_net"] > 10_000_000:
        summary["cross_check"].append(
            f"🏛💡 {institutional['total_label']}（單日量很大，可能有正面預期）"
        )

    # 3. 新聞密度飆升 + 股價上漲 → 利多帶動
    # （只在有 ratio 可比的情況才觸發；單純看「近 3 日有幾則」不夠強）
    if (
        news_density
        and news_density.get("ratio") is not None
        and news_density["ratio"] >= 3
        and return_60d_pct is not None
        and return_60d_pct > 5
    ):
        summary["cross_check"].append(
            "📰 媒體熱度飆升 + 股價上漲：可能由利多新聞帶動"
        )

    # 4. 新聞密度飆升 + 股價下跌 → 利空主導
    if (
        news_density
        and news_density.get("ratio") is not None
        and news_density["ratio"] >= 3
        and return_60d_pct is not None
        and return_60d_pct < -5
    ):
        summary["cross_check"].append(
            "📰⚠️ 媒體熱度飆升 + 股價下跌：可能有利空新聞，需確認原因"
        )

    # 5. 近 3 日有大量新聞（不需要 ratio）+ 股價變動大
    elif (
        news_density
        and news_density.get("recent_3d_count", 0) >= 5
        and return_60d_pct is not None
        and abs(return_60d_pct) > 10
    ):
        direction = "上漲" if return_60d_pct > 0 else "下跌"
        summary["cross_check"].append(
            f"📰 近 3 日新聞密集 + 股價{direction}超過 10%：可能有事件驅動"
        )

    return summary


# ============================================================
# Main：把所有東西串起來
# ============================================================
def analyze(raw_symbol: str, custom_search_term: str | None = None) -> dict:
    """主流程：抓資料 → 算指標 → 抓新聞 → 抓 trends → 建警訊 → 打包 JSON

    Args:
        raw_symbol: 使用者輸入的股票代號（可能未標準化）
        custom_search_term: 給 Google Trends 用的中文搜尋詞（選用）
    """
    symbol = normalize_symbol(raw_symbol)
    result: dict[str, Any] = {
        "symbol": symbol,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # === 必要：抓股價 ===
    hist, info, err = fetch_price_history(symbol)

    # V3.4：上市 .TW 抓不到 → 自動改試上櫃 .TWO（櫃買中心）再抓一次。
    # 4 位數代號無法從外觀分辨上市/上櫃，normalize 預設補 .TW，
    # 上櫃股票（如 5483 中美晶）會在這裡 fallback 成功。
    if err and symbol.endswith(".TW") and "未安裝" not in err:
        two_symbol = symbol[: -len(".TW")] + ".TWO"
        hist2, info2, err2 = fetch_price_history(two_symbol)
        if not err2:
            symbol = two_symbol
            result["symbol"] = symbol
            hist, info, err = hist2, info2, None
        else:
            err = f"{err}（已試 .TW 與 .TWO 都抓不到；.TWO 錯誤：{err2}）"

    if err:
        result["error"] = err
        return result

    # 公司名稱
    name = info.get("longName") or info.get("shortName") or ""
    result["name"] = name
    result["sector"] = info.get("sector", "") or info.get("category", "")
    result["currency"] = info.get("currency", "")
    result["market"] = "TW" if symbol.endswith((".TW", ".TWO")) else "US"

    # === 必要：算技術指標 ===
    try:
        technicals = compute_technicals(hist)
        result.update(technicals)
    except Exception as e:
        result["technicals_error"] = f"技術指標計算失敗：{e}"
        return result

    # === 警訊偵測 ===
    try:
        result["warnings"] = detect_warnings(hist, technicals)
    except Exception as e:
        result["warnings"] = []
        result["warnings_error"] = f"警訊偵測失敗：{e}"

    # === 人類可讀觀察 ===
    result["notes"] = build_notes(technicals)

    # === 新聞（yfinance + Google News RSS 雙來源容錯） ===
    news, news_diags = fetch_news(symbol, custom_search_term)
    result["news"] = news
    result["news_sources"] = news_diags  # 每個來源的 status / message / count，給 SKILL.md 透明顯示
    # 若全部來源都失敗，也記一個總體錯誤訊息（向後相容）
    if not news:
        all_msgs = [f"{d['source']}={d['status']}" for d in news_diags]
        result["news_error"] = "所有新聞來源都未取得：" + "；".join(all_msgs)

    # === 新聞密度（從上面已抓的 news 計算，不需要再抓）===
    result["news_density"] = compute_news_density(news)

    # === PTT 股板熱度 ===
    ptt, ptt_err = fetch_ptt_stock_heat(symbol, custom_search_term, n_pages=10)
    result["ptt_heat"] = ptt
    if ptt_err:
        result["ptt_error"] = ptt_err

    # === Yahoo 股市留言板（總留言數）===
    yahoo, yahoo_err = fetch_yahoo_community_count(symbol)
    result["yahoo_community"] = yahoo
    if yahoo_err:
        result["yahoo_error"] = yahoo_err

    # === 三大法人買賣超（台股專屬）===
    instit, instit_err = fetch_institutional_flow(symbol)
    result["institutional"] = instit
    if instit_err:
        result["institutional_error"] = instit_err

    # === Google Trends（有就用，沒有就跳）===
    # 注意：失敗時我們不在最終 4 區塊輸出顯示「無資料」，由 SKILL.md 控制顯示邏輯。
    trends, trends_err = fetch_google_trends(symbol, name, custom_search_term)
    if trends:
        result["trends"] = trends
    # trends 失敗就完全不放這個 key（SKILL.md 看不到就不顯示）
    if trends_err and not trends:
        result["trends_error"] = trends_err  # 留錯誤訊息給 debug，但 trends 本身為空

    # === 多維熱度整合判讀 ===
    result["heat_summary"] = build_heat_summary(
        ptt=ptt,
        yahoo=yahoo,
        news_density=result["news_density"],
        institutional=instit,
        volume_info=technicals["volume"],
        trends=trends,
        return_60d_pct=technicals["price"].get("return_60d_pct"),
    )

    return result


def main() -> int:
    _silence_stderr()  # 直接執行時關 stderr 避免污染 JSON 輸出
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法：analyze_stock.py <股票代號> [中文搜尋詞]"}, ensure_ascii=False))
        return 1
    raw_symbol = sys.argv[1]
    # 第二個參數：給 Google Trends 用的中文搜尋詞（選用）
    custom_search_term = sys.argv[2] if len(sys.argv) >= 3 else None
    result = analyze(raw_symbol, custom_search_term)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if "error" not in result else 2


if __name__ == "__main__":
    raise SystemExit(main())
