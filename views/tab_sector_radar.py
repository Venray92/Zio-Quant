"""Halaman Sector Radar: sektor mana yang lagi "menyala" hari ini (dana ramai masuk).

Deskriptif, bukan prediksi -- sama seperti Arah Pasar di Home. Dibandingkan ke kebiasaan sektor
itu sendiri, bukan angka mutlak antar sektor.
"""
from html import escape

import pandas as pd
import streamlit as st

from engines.sector_map import get_company_name, load_sector_map
from engines.sector_radar import compute_sector_radar, sector_detail
from utils.card_html import compact_html, fmt_id
from utils.icons import svg_icon
from utils.market_source import load_shared_file

GREEN, PINK, CYAN, AMBER = "#00FF66", "#FF007F", "#00F3FF", "#E3B341"


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def _label(icon, text):
    return f'<div class="zq-label">{svg_icon(icon, 13, "#FF007F", 2)}{escape(text)}</div>'


@st.cache_data(ttl=600, show_spinner=False)
def _cached_radar(stamp):
    data_map, meta = load_shared_file()
    if not data_map:
        return None, None
    return compute_sector_radar(data_map, load_sector_map()), meta


def _sector_card(row, is_selected):
    hot = bool(row["Is Hot"])
    streak = int(row["Streak Days"])
    accent = GREEN if hot else None
    border = (
        f'border: 1.5px solid {CYAN}; background: linear-gradient(135deg, rgba(0,243,255,0.12) 0%, rgba(255,0,127,0.1) 100%); box-shadow: 0 0 12px rgba(0,243,255,0.3);'
        if is_selected
        else (f'border: 1.5px solid {accent}; background-color:#161B22;' if accent else 'border: 1px solid #30363D; background-color:#161B22;')
    )
    status = f'<span style="color:{GREEN}; font-weight:800;">MENYALA{f" · {streak} hari" if streak > 1 else ""}</span>' if hot else '<span class="zq-muted">Netral</span>'
    up_col = GREEN if row["Pct Up"] >= 55 else (PINK if row["Pct Up"] <= 40 else "#C9D1D9")
    warn = f'<div style="margin-top:4px; font-size:11px; color:{AMBER};">{svg_icon("alert-triangle", 12, AMBER, 2, margin_right=4)}Digerakkan 1 saham dominan ({escape(str(row["Top Ticker"] or "").replace(".JK", ""))}, {row["Concentration (%)"]:.0f}% dari nilai transaksi)</div>' if row["Concentration (%)"] > 70 else ""
    return (
        f'<div class="zq-card" style="{border} margin-bottom:8px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<span style="font-weight:800; color:#FFFFFF; font-size:15px;">{escape(row["Sector"])}</span>{status}</div>'
        f'<div class="zq-row"><span>Saham naik</span><span style="color:{up_col}; font-weight:700;">{row["Pct Up"]:.0f}%</span></div>'
        f'<div class="zq-row"><span>Volume relatif tinggi</span><span>{row["Pct High Vol"]:.0f}% saham</span></div>'
        f'<div class="zq-row"><span>Median return hari ini</span><span class="{"zq-up" if row["Median Return (%)"] >= 0 else "zq-down"}">{row["Median Return (%)"]:+.1f}%</span></div>'
        f'<div class="zq-row"><span>Nilai transaksi vs kebiasaan 60 hari</span><span>Persentil {row["Value Percentile"]:.0f}</span></div>'
        f'<div class="zq-row"><span>Jumlah saham likuid dianalisis</span><span>{int(row["N Members"])}</span></div>'
        f'{warn}</div>'
    )


def _detail_table(sector, data_map):
    det = sector_detail(sector, data_map, load_sector_map())
    if det.empty:
        st.info("Belum ada saham likuid yang bisa dianalisis di sektor ini.")
        return
    view = det.copy()
    view["Nama"] = view["Ticker"].apply(lambda t: get_company_name(t) or "")
    view["Close"] = view["Close"].apply(fmt_id)
    view["Change (%)"] = view["Change (%)"].apply(lambda v: f"{v:+.1f}%")
    view["RVOL"] = view["RVOL"].apply(lambda v: f"{v:.1f}x" if pd.notna(v) else "-")
    view["Volatilitas"] = det.apply(lambda r: f"Tinggi (ATR {r['ATR % Now']:.0f}%)" if r.get("Volatile Tinggi") else "-", axis=1)
    st.dataframe(view[["Saham", "Nama", "Close", "Change (%)", "RVOL", "Volatilitas"]], hide_index=True, use_container_width=True)
    if det["Volatile Tinggi"].any():
        st.caption("Volatilitas tinggi = saham ini bergerak sangat liar (ATR > 8% dari harga). Angka RVOL/Change tetap dihitung sama, ini cuma catatan kehati-hatian.")


def render_page_sector_radar():
    _html(
        f"""<div class="zq-hero">
<h1>{svg_icon("radar-2", 24, "#00F3FF", 2, margin_right=8)}SECTOR RADAR</h1>
<p>Sektor mana yang lagi ramai dana hari ini -- dibandingkan ke kebiasaan sektor itu sendiri, bukan angka mutlak.</p>
</div>"""
    )

    _, meta = load_shared_file()
    stamp = f"{(meta or {}).get('last_candle_date', '')}|{(meta or {}).get('updated_at_wib', '')}"
    df, meta2 = _cached_radar(stamp) if meta else (None, None)

    if df is None:
        st.info("Sector Radar butuh file data harian. Coba muat ulang setelah data harian versi terbaru berjalan.")
        return
    if df.empty:
        st.info("Belum ada sektor dengan saham likuid yang cukup untuk dianalisis pada data saat ini.")
        return

    dates = [meta2.get("last_candle_date", "")] if meta2 else []
    if dates and dates[0]:
        st.caption(f"Data per {pd.to_datetime(dates[0]).strftime('%d %b %Y')}. Deskriptif, bukan prediksi dan bukan rekomendasi.")

    n_hot = int(df["Is Hot"].sum())
    _html(_label("bolt", f"{n_hot} sektor lagi menyala" if n_hot else "Belum ada sektor yang menyala hari ini"))

    st.session_state.setdefault("sector_radar_selected", df.iloc[0]["Sector"])
    for _, row in df.iterrows():
        is_sel = st.session_state["sector_radar_selected"] == row["Sector"]
        _html(_sector_card(row, is_sel))
        if st.button(f"Lihat saham {row['Sector']}", key=f"sr_pick_{row['Sector']}", use_container_width=True):
            st.session_state["sector_radar_selected"] = row["Sector"]
            st.rerun()
        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    sel = st.session_state["sector_radar_selected"]
    _html(_label("list-numbers", f"Saham di sektor {sel}"))
    data_map, _ = load_shared_file()
    if data_map:
        _detail_table(sel, data_map)
