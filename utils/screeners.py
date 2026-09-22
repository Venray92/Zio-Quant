"""Daftar screener Z-QUANT (satu sumber untuk menu, Home, dan How To).

Tambah screener baru = tambah satu entri di SCREENERS. Menu dropdown, kartu di Home,
dan halaman URL-nya ikut otomatis. 'key' dipakai di session_state, jangan diganti.
"""
import importlib

SCREENERS = [
    {
        "key": "rsi",
        "name": "RSI Reversal",
        "category": "Reversal",
        "desc": "Divergence RSI + konfirmasi cross",
        "icon": "arrows-exchange",
        "material": "swap_vert",
        "url": "rsi-reversal",
        "module": "views.tab_rsi",
        "func": "render_tab_rsi",
    },
    {
        "key": "stoch_psar",
        "name": "Stoch Momentum",
        "category": "Momentum",
        "desc": "Golden/Dead Cross Stochastic + PSAR",
        "icon": "activity",
        "material": "speed",
        "url": "stoch-momentum",
        "module": "views.tab_stoch_psar",
        "func": "render_tab_stoch_psar",
    },
    {
        "key": "trend_scanner",
        "name": "Trend Scanner",
        "category": "Struktur",
        "desc": "Breakout Surge, Trend Reset & Quiet Accumulation",
        "icon": "bolt",
        "material": "bolt",
        "url": "trend-scanner",
        "module": "views.tab_trend",
        "func": "render_tab_trend",
    },
    {
        "key": "sector_radar",
        "name": "Sector Radar",
        "category": "Radar",
        "desc": "Sektor mana yang lagi ramai dana hari ini",
        "icon": "radar-2",
        "material": "radar",
        "url": "sector-radar",
        "module": "views.tab_sector_radar",
        "func": "render_page_sector_radar",
    },
    {
        "key": "trade_plan",
        "name": "Trade Planner",
        "category": "Planner",
        "desc": "Area buy, SL, TP dan grade per saham",
        "icon": "target",
        "material": "track_changes",
        "url": "trade-planner",
        "module": "views.tab_trade_planner",
        "func": "render_tab_trade_planner",
    },
]


def get_screener(key):
    return next((s for s in SCREENERS if s["key"] == key), None)


def render_screener(key):
    s = get_screener(key)
    module = importlib.import_module(s["module"])
    getattr(module, s["func"])()
