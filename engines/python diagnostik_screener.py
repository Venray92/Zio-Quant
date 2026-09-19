"""
DIAGNOSTIK SCREENER RSI DIVERGENCE
----------------------------------
Menghitung berapa saham yang GUGUR di tiap tahap, buat bullish dan
bearish, supaya kelihatan filter mana yang paling banyak ngebuang.
File ini terpisah: TIDAK mengubah screener_rsi_divergence.py.

Cara pakai (satu file berisi satu ticker per baris, .JK otomatis):
    python diagnostik_screener.py daftar_ticker.txt

Atau dari Python:
    from diagnostik_screener import run_diagnostic
    run_diagnostic(['BFIN.JK', 'MEDC.JK', 'INDY.JK'])
"""
import sys

import pandas as pd
import yfinance as yf

import screener_rsi_divergence as scr

STAGES = [
    'Data cukup (>= 30 candle)',              # 0
    'Harga > 70',                             # 1
    'Value > Rp1 miliar',                     # 2
    'Ada >= 2 swing',                         # 3
    'Umur T2 <= H+3',                         # 4
    'Close belum jebol T2',                   # 5
    'Ada T1 dgn jarak 5-25 candle',           # 6
    'Lantai/plafon T1-T2 tidak putus',        # 7
    'Garis miring harga tidak putus',         # 8
    'Tidak ada kawah di tengah',              # 9
    'Arah pola cocok (harga vs RSI)',         # 10
    'RSI di zona pola',                       # 11
    'Selisih harga & RSI cukup',              # 12
    'Garis miring RSI tidak putus',           # 13
    'Ada GC/DC di H+0..H+3 (= LOLOS)',        # 14
]


def _prepare(raw):
    """Persiapan data, sama dengan detect_rsi_patterns_and_score.
    Return (df, tahap_lolos). df = None kalau gugur di filter awal."""
    df = raw.copy()
    if df is None or df.empty or len(df) < 30:
        return None, -1
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    latest_close = float(df['Close'].iloc[-1])
    if latest_close <= 70:
        return None, 0
    if df['Volume'].iloc[-1] * latest_close <= 1_000_000_000:
        return None, 1
    df['RSI_10'] = scr.calculate_rsi(df['Close'], period=10)
    df['RSI_EMA10'] = scr.calculate_ema(df['RSI_10'], period=10)
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df = df.dropna(subset=['RSI_10', 'RSI_EMA10', 'Vol_MA20'])
    return df, 2


def _rsi_extreme(df, idx_pos, use_min, window=2):
    start = max(0, idx_pos - window)
    end = min(len(df) - 1, idx_pos + window)
    seg = df['RSI_10'].iloc[start:end + 1]
    return seg.min() if use_min else seg.max()


def _rsi_pos(df, idx_pos, use_min, window=2):
    start = max(0, idx_pos - window)
    end = min(len(df) - 1, idx_pos + window)
    seg = df['RSI_10'].iloc[start:end + 1].values
    return start + int(seg.argmin() if use_min else seg.argmax())


def _analyze_side(df, side):
    """Return tahap tertinggi yang berhasil dilewati (3..14)."""
    bull = side == 'bull'
    swings = scr.extract_swings(
        df['Low' if bull else 'High'],
        left=2, right=2, swing_type='LOW' if bull else 'HIGH',
    )
    best = 2
    if swings.empty or len(swings) < 2:
        return best
    best = 3
    swings = swings.sort_values('Index_Pos', ascending=False)
    latest_idx = len(df) - 1
    latest_close = float(df['Close'].iloc[-1])

    for i in range(len(swings) - 1):
        rp = swings.iloc[i]
        r_idx = int(rp['Index_Pos'])
        if latest_idx - r_idx > 3:
            continue
        best = max(best, 4)
        if (bull and latest_close < rp['Nilai']) or (
            not bull and latest_close > rp['Nilai']
        ):
            continue
        best = max(best, 5)

        for j in range(i + 1, len(swings)):
            lp = swings.iloc[j]
            l_idx = int(lp['Index_Pos'])
            if not (5 <= r_idx - l_idx <= 25):
                continue
            best = max(best, 6)

            between = df.iloc[l_idx:r_idx + 1]
            if bull:
                if between['Low'].min() < min(lp['Nilai'], rp['Nilai']) * 0.998:
                    continue
            else:
                if between['High'].max() > max(lp['Nilai'], rp['Nilai']) * 1.002:
                    continue
            best = max(best, 7)

            broken = (
                scr.is_price_line_broken(df, l_idx, r_idx)
                if bull
                else scr.is_price_line_broken_high(df, l_idx, r_idx)
            )
            if broken:
                continue
            best = max(best, 8)

            if scr.has_crater_between(swings, l_idx, r_idx, rp['Nilai']):
                continue
            best = max(best, 9)

            rr = _rsi_extreme(df, r_idx, bull)
            rl = _rsi_extreme(df, l_idx, bull)
            if bull:
                pdiff = (lp['Nilai'] - rp['Nilai']) / lp['Nilai'] * 100
                rdiff = rr - rl
                reg = [rp['Nilai'] < lp['Nilai'] and rr > rl,
                       0 <= rr <= 30,
                       pdiff >= scr.MIN_PRICE_DIFF_PCT
                       and rdiff >= scr.MIN_RSI_DIFF]
                hid = [rp['Nilai'] >= lp['Nilai'] and rr < rl,
                       50 < rr <= 75,
                       rdiff <= -scr.MIN_RSI_DIFF]
            else:
                pdiff = (rp['Nilai'] - lp['Nilai']) / lp['Nilai'] * 100
                rdiff = rr - rl
                reg = [rp['Nilai'] > lp['Nilai'] and rr < rl,
                       70 <= rr <= 100,
                       pdiff >= scr.MIN_PRICE_DIFF_PCT
                       and rdiff <= -scr.MIN_RSI_DIFF]
                hid = [rp['Nilai'] <= lp['Nilai'] and rr > rl,
                       30 <= rr <= 50,
                       rdiff >= scr.MIN_RSI_DIFF]

            def progress(conds):
                p = 0
                for c in conds:
                    if not c:
                        break
                    p += 1
                return p

            prog = max(progress(reg), progress(hid))
            best = max(best, 9 + prog)
            if prog < 3:
                continue

            lpos = _rsi_pos(df, l_idx, bull)
            rpos = _rsi_pos(df, r_idx, bull)
            broken = (
                scr.is_rsi_line_broken(df, lpos, rpos)
                if bull
                else scr.is_rsi_line_broken_high(df, lpos, rpos)
            )
            if broken:
                continue
            best = max(best, 13)

            cross = False
            for idx in range(r_idx, min(latest_idx + 1, r_idx + 4)):
                c, e = df['RSI_10'].iloc[idx], df['RSI_EMA10'].iloc[idx]
                pc, pe = df['RSI_10'].iloc[idx - 1], df['RSI_EMA10'].iloc[idx - 1]
                if bull and c > e and pc <= pe:
                    cross = True
                if not bull and c < e and pc >= pe:
                    cross = True
            if cross:
                best = 14
    return best


def analyze_df(raw):
    """Return {'bull': tahap, 'bear': tahap}. -1 = data kurang."""
    df, stage = _prepare(raw)
    if df is None:
        return {'bull': stage, 'bear': stage}
    return {
        'bull': _analyze_side(df, 'bull'),
        'bear': _analyze_side(df, 'bear'),
    }


def _download(ticker):
    df = yf.download(ticker, period='6mo', interval='1d',
                     progress=False, auto_adjust=False)
    return df


def _print_funnel(title, stages_by_ticker):
    total = len(stages_by_ticker)
    print(f'\n=== {title} ({total} saham dianalisa) ===')
    print(f'{"Tahap":<38}{"Lolos":>7}{"Gugur":>8}{"% lolos":>9}')
    prev = total
    worst = (None, -1)
    for k, name in enumerate(STAGES):
        n = sum(1 for s in stages_by_ticker.values() if s >= k)
        drop = prev - n
        pct = (n / prev * 100) if prev else 0
        print(f'{k:>2}. {name:<34}{n:>7}{drop:>8}{pct:>8.0f}%')
        if drop > worst[1]:
            worst = (name, drop)
        prev = n
    print(f'-> Tahap yang paling banyak ngebuang: {worst[0]} ({worst[1]} saham)')
    # tahap 4 (umur) dan 10-11 (arah pola & zona RSI) memang penyaring alami;
    # yang perlu dicurigai kalau hasil 0 adalah filter tambahan di bawah ini
    extra = {5, 7, 8, 9, 12, 13, 14}
    w2, d2, prev = None, -1, total
    for k in range(len(STAGES)):
        n = sum(1 for s in stages_by_ticker.values() if s >= k)
        if k in extra and prev - n > d2:
            w2, d2 = STAGES[k], prev - n
        prev = n
    print(f'-> Filter tambahan yang paling banyak ngebuang: {w2} ({d2} saham)')


def run_diagnostic(tickers, save_csv='diagnostik_hasil.csv',
                   near_miss=12):
    rows = {}
    bull, bear = {}, {}
    for n, tk in enumerate(tickers, 1):
        tk = tk.strip()
        if not tk:
            continue
        if '.' not in tk:
            tk += '.JK'
        try:
            res = analyze_df(_download(tk))
        except Exception:
            res = {'bull': -1, 'bear': -1}
        bull[tk], bear[tk] = res['bull'], res['bear']
        rows[tk] = res
        if n % 25 == 0:
            print(f'  ...{n}/{len(tickers)} ticker')

    _print_funnel('BULLISH', bull)
    _print_funnel('BEARISH', bear)

    for title, d in (('BULLISH', bull), ('BEARISH', bear)):
        close = sorted(
            [(s, tk) for tk, s in d.items() if 11 <= s < 14],
            reverse=True,
        )[:near_miss]
        if close:
            print(f'\nNyaris lolos {title} (gugur setelah tahap ini):')
            for s, tk in close:
                print(f'  {tk:<10} lolos sampai tahap {s} '
                      f'({STAGES[s]}), gugur di: {STAGES[s + 1].replace(" (= LOLOS)", "")}')

    if save_csv:
        pd.DataFrame(
            [{'Ticker': tk, 'Bull_tahap': r['bull'], 'Bear_tahap': r['bear']}
             for tk, r in rows.items()]
        ).to_csv(save_csv, index=False)
        print(f'\nDetail per saham disimpan ke {save_csv}')
    return rows


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    with open(sys.argv[1], encoding='utf-8') as f:
        run_diagnostic([ln for ln in f.read().splitlines() if ln.strip()])
