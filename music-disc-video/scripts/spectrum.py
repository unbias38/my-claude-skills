"""
spectrum.py —— 把一首 mp3 事先「聽」過一遍，算出每個時間點的頻譜柱高度。

為什麼要事先算好，而不是讓瀏覽器邊播邊算？
  1. 邊播邊算的做法（Web Audio API）在「雙擊開啟的本機檔案」上有機率失效，
     會變成一排完全不動的柱子，而且很難除錯。
  2. 更重要的是，我們的最高原則是「所有動畫都必須能由時間 t 直接算出來」。
     事先算好 = 給定任何 t 都能查表得到柱高，拖進度條、暫停、跳轉都不會亂。
  3. Phase 2 要輸出 MP4 影片時，可以用「完全同一份資料」，
     這樣網頁版和影片版的頻譜會長得一模一樣。

打個比方：這就像先把整首歌的「心電圖」印成一本厚厚的表格，
之後不管翻到第幾頁（第幾秒），看到的都是同一個結果。
"""

import subprocess
import numpy as np

# ffmpeg 是處理影音的瑞士刀，這裡只用它來把 mp3「解碼」成原始波形。
# 路徑不寫死，交給 env.py 自己去找（Windows / Mac / Linux 都能跑）。
from env import find_ffmpeg
FFMPEG = find_ffmpeg()

# ---- 可調參數（改這裡就能改頻譜的樣子）----
SAMPLE_RATE = 22050   # 解碼取樣率。22050Hz 表示每秒記錄 22050 個聲音數值，足夠分析到 11kHz。
N_BARS      = 56      # 畫面上要有幾根柱子
DATA_FPS    = 20      # 每秒存幾筆頻譜資料。20 筆已經很滑順，播放時再用內插補成 60fps。
FFT_SIZE    = 2048    # 每次分析取多長的一小段聲音（2048 個樣本 ≈ 93 毫秒）
FREQ_LO     = 40      # 最低頻率（Hz），再低人耳幾乎聽不到
FREQ_HI     = 9000    # 最高頻率（Hz）
DB_FLOOR    = -68     # 音量對映範圍：這個分貝以下算作 0（柱子貼地）
DB_CEIL     = -14     # 這個分貝以上算作滿格（柱子頂天）
RELEASE     = 0.80    # 柱子「掉下來」的速度：0.8 表示每一格衰減到 80%，看起來會有殘影感


def decode_mp3_to_mono(mp3_path, sample_rate=SAMPLE_RATE):
    """把 mp3 解碼成一長串「聲音數值」（單聲道）。

    聲音在電腦裡就是一串上下震盪的數字。這一步等於把壓縮過的 mp3
    還原成最原始的波形，才有辦法做後續的頻率分析。
    """
    raw = subprocess.run(
        [FFMPEG, "-v", "error", "-i", mp3_path,
         "-f", "s16le",          # 輸出格式：16 位元、有正負號、小端序的原始數字
         "-ac", "1",             # 混成 1 個聲道（單聲道就夠分析了）
         "-ar", str(sample_rate),
         "-"],                   # "-" 表示不要存檔，直接吐到輸出管線給 Python 接
        capture_output=True,
    )
    if not raw.stdout:
        raise RuntimeError("ffmpeg 解碼失敗：\n" + raw.stderr.decode("utf-8", "ignore"))
    # 16 位元整數的範圍是 -32768 ~ 32767，除以 32768 換算成 -1.0 ~ 1.0 的小數
    return np.frombuffer(raw.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def compute_spectrum(mp3_path, n_bars=N_BARS, data_fps=DATA_FPS):
    """回傳一個 (幀數, 柱子數) 的 uint8 表格，值 0~255 代表柱子高度百分比。"""

    pcm = decode_mp3_to_mono(mp3_path)
    duration = len(pcm) / SAMPLE_RATE
    n_frames = int(np.ceil(duration * data_fps))

    # 兩端補 0，這樣第一幀和最後一幀取窗時不會超出範圍
    pad = FFT_SIZE // 2
    padded = np.pad(pcm, (pad, pad + FFT_SIZE))

    # 漢寧窗：取一小段聲音做分析時，硬生生切斷會產生假的高頻雜訊。
    # 乘上一個「兩端漸弱、中間最強」的窗形可以避免這個問題。（像照片的柔邊）
    window = np.hanning(FFT_SIZE).astype(np.float32)

    # 每一幀對應到原始音訊的哪個位置
    starts = np.round(np.arange(n_frames) * SAMPLE_RATE / data_fps).astype(np.int64)

    # rfftfreq 告訴我們 FFT 出來的每一格分別代表幾 Hz
    freqs = np.fft.rfftfreq(FFT_SIZE, 1.0 / SAMPLE_RATE)

    # 把 40Hz~9000Hz 用「等比」方式切成 n_bars 段。
    # 為什麼用等比而不是等分？因為人耳對頻率的感受是等比的
    # ——100→200Hz 和 1000→2000Hz 聽起來都是「高了一個八度」。
    edges = np.geomspace(FREQ_LO, FREQ_HI, n_bars + 1)
    band_slices = []
    for b in range(n_bars):
        lo, hi = edges[b], edges[b + 1]
        idx = np.where((freqs >= lo) & (freqs < hi))[0]
        if len(idx) == 0:                                   # 低頻段可能一格都沒涵蓋到
            idx = np.array([int(np.argmin(np.abs(freqs - (lo + hi) / 2)))])
        band_slices.append(idx)

    # 高頻天生比低頻小聲，若不補償，右半邊的柱子會一直趴著不動。
    # 這裡加一條隨頻率上升的增益（俗稱 tilt），讓整排柱子看起來平衡。
    centers = np.sqrt(edges[:-1] * edges[1:])
    tilt_db = 9.0 * np.log10(centers / FREQ_LO)             # 每十倍頻率 +9dB

    out = np.zeros((n_frames, n_bars), dtype=np.float32)

    # 分批處理，避免一次做 4800 筆 × 2048 點的矩陣把記憶體吃爆
    CHUNK = 512
    for c0 in range(0, n_frames, CHUNK):
        c1 = min(c0 + CHUNK, n_frames)
        idx = starts[c0:c1, None] + np.arange(FFT_SIZE)[None, :]
        seg = padded[idx] * window                          # 取窗
        mag = np.abs(np.fft.rfft(seg, axis=1)) / (FFT_SIZE / 2)   # 轉成各頻率的強度
        for b, bins in enumerate(band_slices):
            out[c0:c1, b] = mag[:, bins].mean(axis=1)

    # 轉成分貝（人耳感受是對數的），再對映到 0~1
    db = 20.0 * np.log10(out + 1e-7) + tilt_db[None, :]
    norm = np.clip((db - DB_FLOOR) / (DB_CEIL - DB_FLOOR), 0.0, 1.0)

    # 「快速上升、緩慢下降」：真實的頻譜顯示器都這樣做，
    # 鼓點打下去柱子瞬間跳起來，然後慢慢滑下來，看起來才有生命力。
    for f in range(1, n_frames):
        decayed = norm[f - 1] * RELEASE
        norm[f] = np.maximum(norm[f], decayed)

    return (norm * 255.0).astype(np.uint8), duration


if __name__ == "__main__":
    import sys, time
    path = sys.argv[1]
    t0 = time.time()
    data, dur = compute_spectrum(path)
    print(f"歌曲長度 {dur:.2f} 秒，產生 {data.shape[0]} 幀 × {data.shape[1]} 根柱子")
    print(f"耗時 {time.time()-t0:.1f} 秒；平均高度 {data.mean()/255:.2f}，最大 {data.max()/255:.2f}")
