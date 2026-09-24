"""MFI Reversal -- mesin SAMA PERSIS dengan RSI Reversal (divergence: swing, garis harga/oscillator
tidak boleh dilewati, base konsolidasi), cuma oscillator-nya diganti MFI (Money Flow Index) yang
ikut menghitung volume selain harga -- "RSI yang lebih jujur soal partisipasi pasar".

File ini murni wrapper tipis di atas engines.screener_rsi_divergence (oscillator='mfi'), supaya
mesin divergence yang sudah teruji lama tidak perlu diduplikasi/ditulis ulang.
"""
from engines.screener_rsi_divergence import calculate_mfi  # noqa: F401  (re-export utk kemudahan impor)
from engines.screener_rsi_divergence import detect_rsi_patterns_and_score


def detect_mfi_patterns_and_score(ticker, df=None, now=None):
    return detect_rsi_patterns_and_score(ticker, df=df, now=now, oscillator='mfi')


def run_mfi_screener(tickers, progress_callback=None, data=None, should_stop=None, batch_size=50, phase_callback=None):
    from engines.screener_rsi_divergence import run_rsi_screener

    return run_rsi_screener(
        tickers, progress_callback=progress_callback, data=data, should_stop=should_stop,
        batch_size=batch_size, phase_callback=phase_callback, oscillator='mfi',
    )
