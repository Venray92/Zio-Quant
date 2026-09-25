"""Ranking Leaderboard: gantiin "Leaderboard Screener" + "Rekap Screener" (24 Sep -> sekarang, 1
halaman gabungan). Rank 1 = Top saham dgn kenaikan % terbesar (dedup, dari sinyal Bullish semua
screener), Rank 2 = screener mana yg paling nyumbang ke Top itu + riwayat akurasi & streak aktif.

Sumber data SAMA dgn Leaderboard/Rekap lama (screener_history.json via scripts/update_market_data.py),
jadi "data ga keupdate" itu soal PIPELINE (lihat .github/workflows/update_market_data.yml), bukan
halaman ini -- halaman ini cuma nampilin apa yg ADA di file itu, sejujur-jujurnya.
"""
from html import escape

import streamlit as st

from engines import ranking as RK
from utils.card_html import compact_html
from utils.compat import STRETCH
from utils.icons import svg_icon
from utils.pages import keyed_container
from utils.ui_helpers import render_inline_trade_planner

GREEN, PINK, AMBER = "#00FF66", "#FF007F", "#E3B341"
_DIM = "__dim"  # class marker, dipetakan ke CSS opacity di utils/theme.py (konvensi sama spt "__active" di top_nav.py)
_WINDOW_LABELS = ["Harian", "Mingguan", "Bulanan", "Tahunan"]
_WINDOW_KEY = {"Harian": "harian", "Mingguan": "mingguan", "Bulanan": "bulanan", "Tahunan": "tahunan"}


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def _reset_filters():
    for k in ("rk_window_input", "rk_date_input", "_rk_prev_window", "_rk_prev_range"):
        st.session_state.pop(k, None)
    st.session_state["rk_mode"] = "window"
    st.session_state["rk_window_sel"] = "Mingguan"
    st.session_state["rk_date_range"] = None


def _render_filters(min_d, max_d):
    """Kartu 'Kapan data diambil': rentang tanggal (klik 2x) ATAU jendela waktu shortcut --
    saling eksklusif (pilih satu, yang lain otomatis nonaktif/abu-abu)."""
    st.session_state.setdefault("rk_mode", "window")
    st.session_state.setdefault("rk_window_sel", "Mingguan")
    st.session_state.setdefault("rk_date_range", None)

    _html(
        f"""<div class="zq-card" style="margin-bottom:6px;">
<div style="font-family:'Share Tech Mono', monospace; font-size:11px; font-weight:800; letter-spacing:1px; color:#00F3FF;">
{svg_icon("calendar-event", 14, "#00F3FF", 2, margin_right=6)}KAPAN DATA DIAMBIL</div>
</div>"""
    )

    mode = st.session_state["rk_mode"]
    # CATATAN: SENGAJA tidak dipakai disabled=True Streamlit di sini -- kalau widget yg TIDAK aktif
    # betul-betul dikunci (disabled), user tidak akan bisa lagi memilihnya sama sekali (klik pun tidak
    # bereaksi), jadi begitu salah satu mode kepilih dulu, mode lain jadi terkunci PERMANEN kecuali klik
    # Clear. Supaya user selalu bisa pindah mode kapan saja (sesuai maksud "klik salah satu, yg lain
    # otomatis ganti"), dua kontrol ini SELALU bisa diklik -- yg "tidak aktif" cuma didim visual lewat
    # CSS opacity (keyed_container + class "__dim", CSS-nya di utils/theme.py), bukan dikunci sungguhan.
    with keyed_container(f"zrk_daterange{_DIM if mode == 'window' else ''}"):
        date_val = st.date_input(
            "Rentang tanggal data (klik tanggal awal, lalu tanggal akhir)",
            value=st.session_state["rk_date_range"] or (),
            min_value=min_d, max_value=max_d,
            key="rk_date_input",
        )
    with keyed_container(f"zrk_windowsel{_DIM if mode == 'range' else ''}"):
        win_val = st.segmented_control(
            "Atau pilih jendela waktu (shortcut)",
            options=_WINDOW_LABELS,
            default=st.session_state["rk_window_sel"] if mode == "window" else None,
            key="rk_window_input",
        )

    cur_range = tuple(date_val) if date_val and len(date_val) == 2 else None

    # Bandingkan ke state OTORITATIF (rk_window_sel/rk_date_range), bukan shadow "prev_*" terpisah --
    # itu bisa telat sinkron dan bikin kondisi selalu "beda" -> st.rerun() tanpa henti. Dengan cara ini,
    # begitu state otoritatif diperbarui, kondisinya jadi False di run berikutnya dan loop berhenti sendiri.
    if win_val is not None and (mode != "window" or win_val != st.session_state["rk_window_sel"]):
        st.session_state["rk_mode"] = "window"
        st.session_state["rk_window_sel"] = win_val
        st.session_state["rk_date_range"] = None
        st.session_state.pop("rk_date_input", None)
        st.rerun()
    elif cur_range is not None and cur_range != st.session_state["rk_date_range"]:
        st.session_state["rk_mode"] = "range"
        st.session_state["rk_date_range"] = cur_range
        st.session_state.pop("rk_window_input", None)
        st.rerun()

    c_clear, c_gap = st.columns([1, 3])
    with c_clear:
        if st.button("Clear", key="rk_clear_btn", **STRETCH):
            _reset_filters()
            st.rerun()

    if st.session_state["rk_mode"] == "range" and st.session_state["rk_date_range"]:
        d0, d1 = st.session_state["rk_date_range"]
        return {"date_start": str(d0), "date_end": str(d1), "window_key": None}
    return {"date_start": None, "date_end": None, "window_key": _WINDOW_KEY[st.session_state["rk_window_sel"]]}


def _row_html(row):
    badge = ' <span class="zq-chip" style="background:rgba(0,243,255,.15); color:#00F3FF;">Baru</span>' if row["is_new"] else ""
    return (
        f'<div class="zq-card zq-lb-row" style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">'
        f'<div style="font-size:20px; font-weight:800; color:#8B949E; min-width:36px;">#{row["rank"]}</div>'
        f'<div style="flex:2; min-width:150px;">'
        f'<div style="color:#FFFFFF; font-weight:800; font-size:15px;">{escape(row["ticker"].replace(".JK",""))}{badge}</div>'
        f'<div class="zq-muted" style="font-size:11px;">{escape(row["screener_name"])} &bull; sinyal {row["signal_date"]}</div>'
        f'</div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:90px;">'
        f'<div style="font-size:14px; font-weight:700; color:#C9D1D9;">Rp {row["signal_price"]:,.0f}</div>'
        f'<div class="zq-muted" style="font-size:11px;">harga sinyal</div></div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:90px;">'
        f'<div style="font-size:14px; font-weight:700; color:#FFFFFF;">Rp {row["last_price"]:,.0f}</div>'
        f'<div class="zq-muted" style="font-size:11px;">harga sekarang</div></div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:80px;">'
        f'<div style="font-size:18px; font-weight:800; color:{GREEN};">+{row["gain_pct"]:.1f}%</div>'
        f'<div class="zq-muted" style="font-size:11px;">kenaikan</div></div>'
        f'</div>'
    ).replace(",", ".")


def _screener_row_html(rank, s, max_n):
    pct = int(100 * s["n_in_top"] / max_n) if max_n else 0
    wr, edge = s["win_rate"], s["avg_edge"]
    wr_col = GREEN if (wr or 0) >= 55 else (PINK if wr is not None and wr <= 45 else AMBER)
    wr_txt = f"{wr:.0f}%" if wr is not None else "-"
    streak_txt = f"streak {s['streak_days']}h" if s["streak_days"] > 0 else "sinyal terakhir kosong"
    return (
        f'<div class="zq-card" style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">'
        f'<div style="font-size:16px; font-weight:800; color:#8B949E; min-width:30px;">#{rank}</div>'
        f'<div style="flex:2; min-width:160px;">'
        f'<div style="color:#FFFFFF; font-weight:800; font-size:14px;">{escape(s["name"])}</div>'
        f'<div class="zq-muted" style="font-size:11px;">{s["n_in_top"]} dari {s["n_total"]} saham tembus filter</div>'
        f'<div style="background:#161B22; border-radius:4px; height:6px; margin-top:5px; overflow:hidden;">'
        f'<div style="background:#00F3FF; height:6px; width:{pct}%;"></div></div>'
        f'</div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:70px;">'
        f'<div style="font-size:16px; font-weight:800; color:{wr_col};">{wr_txt}</div>'
        f'<div class="zq-muted" style="font-size:11px;">win rate</div></div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:90px;">'
        f'<div style="font-size:13px; font-weight:700; color:#E3B341;">🔥 {streak_txt}</div>'
        f'<div class="zq-muted" style="font-size:11px;">aktif beruntun</div></div>'
        f'</div>'
    )


def render_page_ranking():
    _html(
        f"""<div class="zq-hero">
<h1>{svg_icon("trophy", 24, "#00F3FF", 2, margin_right=8)}RANKING LEADERBOARD</h1>
<p>Top saham dengan kenaikan terbesar dari semua screener (dedup per saham) + screener mana yang paling akurat &amp; aktif belakangan ini.</p>
</div>"""
    )

    from utils import market_source, watchlist_store

    history = market_source.load_recap()
    if not (history or {}).get("days"):
        st.info("Ranking tampil setelah rekap harian versi terbaru berjalan beberapa hari. Coba lagi nanti.")
        return

    days_all = sorted(history["days"])
    min_d, max_d = days_all[0], days_all[-1]

    filt = _render_filters(min_d, max_d)

    c1, c2 = st.columns([1, 1])
    with c1:
        min_gain = st.number_input("Min. kenaikan (%)", min_value=0.0, max_value=500.0, value=st.session_state.get("rk_min_gain", 10.0), step=1.0, key="rk_min_gain")
    with c2:
        wl_only = st.toggle("Hanya saham di watchlist saya", value=st.session_state.get("rk_wl_only", False), key="rk_wl_only")

    watchlist = None
    if wl_only:
        try:
            watchlist = watchlist_store.tickers()
        except Exception:
            watchlist = []
        if not watchlist:
            st.info("Watchlist kamu masih kosong -- tidak ada saham yang bisa disaring.")
            return

    data_map, _ = market_source.load_shared_file()
    if not data_map:
        st.warning("Data harga terbaru belum tersedia (file data harian belum ada/basi). Ranking butuh harga SEKARANG utk menghitung kenaikan.")
        return

    # ambil harga terakhir cuma utk saham yg relevan di jendela ini (hemat, bukan semua ribuan saham)
    keys_preview, _ = RK.resolve_days(history, filt["window_key"], filt["date_start"], filt["date_end"])
    want = {h["t"] for d in keys_preview for e in (history["days"].get(d) or {}).values() if isinstance(e, dict) for h in e.get("hits", []) if h.get("d") == "Bullish"}
    last_close = {}
    for t in want:
        df = data_map.get(t)
        try:
            if df is not None and len(df):
                last_close[t] = float(df["Close"].iloc[-1])
        except Exception:
            pass

    out = RK.build_ranking(
        history, last_close, window_key=filt["window_key"], date_start=filt["date_start"], date_end=filt["date_end"],
        min_gain_pct=float(min_gain), watchlist=watchlist, top_n=30,
    )

    if not out["dates"]:
        st.info("Tidak ada hari bursa di rentang/jendela waktu itu.")
        return

    st.caption(
        f"Jendela: {out['range_label']} ({len(out['dates'])} hari bursa, {out['dates'][0]} s/d {out['dates'][-1]}) &bull; "
        f"{out['n_candidates']} saham unik kena sinyal Bullish, {len(out['rows'])} lolos filter min. kenaikan {out['min_gain_pct']:.0f}%. "
        f"Hasil masa lalu bukan jaminan hasil ke depan."
    )

    st.markdown(
        '<div style="font-family:\'Share Tech Mono\', monospace; font-size:12px; font-weight:800; letter-spacing:1px; color:#00F3FF; margin:14px 0 6px;">RANK 1 &middot; TOP SAHAM (KENAIKAN TERBESAR)</div>',
        unsafe_allow_html=True,
    )
    if not out["rows"]:
        st.info("Tidak ada saham yang lolos filter min. kenaikan di jendela ini. Coba turunkan angkanya atau perlebar jendela waktu.")
    else:
        for row in out["rows"]:
            _html(_row_html(row))
            code = row["ticker"].replace(".JK", "")
            with keyed_container(f"zrk_open_{row['ticker']}"):
                if st.button(f"Buka {code}", key=f"zrk_btn_{row['ticker']}", **STRETCH):
                    st.session_state["selected_ranking_ticker"] = row["ticker"]
            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

        sel = st.session_state.get("selected_ranking_ticker")
        if sel and sel in {r["ticker"] for r in out["rows"]}:
            try:
                render_inline_trade_planner(sel, key_suffix="ranking", screener_name="Ranking Leaderboard")
            except Exception as e:
                st.error(f"Gagal memuat Trade Plan {sel}: {e}")

    st.markdown(
        '<div style="font-family:\'Share Tech Mono\', monospace; font-size:12px; font-weight:800; letter-spacing:1px; color:#00F3FF; margin:18px 0 6px;">RANK 2 &middot; SCREENER PALING NYUMBANG</div>',
        unsafe_allow_html=True,
    )
    if not out["screener_stats"]:
        st.caption("Belum ada screener yang menyumbang saham di jendela ini.")
    else:
        max_n = max((s["n_in_top"] for s in out["screener_stats"]), default=0) or 1
        for i, s in enumerate(out["screener_stats"], start=1):
            _html(_screener_row_html(i, s, max_n))
        st.caption("Win rate Rank 2 sudah sinkron sama filter kenaikan% di atas -- kalau filter dinaikkan, win rate & jumlah saham tiap screener ikut menyusut sesuai yg benar2 lolos (di 0%, hampir semua saham yg kepantau ikut terhitung). Streak tetap independen (soal aktif/kosong, bukan menang). Detail metode di engines/ranking.py.")
