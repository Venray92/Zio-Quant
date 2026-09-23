"""Halaman Sector Radar: sektor mana yang lagi "menyala" hari ini (dana ramai masuk).

Deskriptif, bukan prediksi -- sama seperti Arah Pasar di Home. Dibandingkan ke kebiasaan sektor
itu sendiri, bukan angka mutlak antar sektor.
"""
from html import escape

import pandas as pd
import streamlit as st

from engines.sector_map import get_company_name, load_sector_map
from engines.sector_radar import compute_sector_radar, heatmap_data, sector_detail
from utils.card_html import compact_html, fmt_id
from utils.icons import svg_icon
from utils.compat import STRETCH
from utils.market_source import load_sector_hist, load_shared_file
from utils.pages import keyed_container

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


def _status_html(row):
    hot, streak = bool(row["Is Hot"]), int(row["Streak Days"])
    if hot:
        return f'<span style="color:{GREEN}; font-weight:800; font-size:12px;">MENYALA{f" · {streak} hari" if streak > 1 else ""}</span>'
    return '<span class="zq-muted" style="font-size:12px;">Netral</span>'


def _concentrated(row):
    return float(row["Concentration (%)"]) > 70


def _warn_html(row):
    if not _concentrated(row):
        return ""
    top = escape(str(row["Top Ticker"] or "").replace(".JK", ""))
    return (
        f'<div style="margin-top:4px; font-size:11px; color:{AMBER};">{svg_icon("alert-triangle", 12, AMBER, 2, margin_right=4)}'
        f'Digerakkan 1 saham dominan ({top}, {row["Concentration (%)"]:.0f}% dari nilai transaksi)</div>'
    )


def _sector_card(row, is_selected):
    """Kartu ringkas untuk daftar kiri: nama, status, dan satu baris angka utama."""
    hot = bool(row["Is Hot"])
    border = (
        f'border: 1.5px solid {CYAN}; background: linear-gradient(135deg, rgba(0,243,255,0.12) 0%, rgba(255,0,127,0.1) 100%); box-shadow: 0 0 12px rgba(0,243,255,0.3);'
        if is_selected
        else (f'border: 1.5px solid {GREEN}; background-color:#161B22;' if hot else 'border: 1px solid #30363D; background-color:#161B22;')
    )
    med = float(row["Median Return (%)"])
    return (
        f'<div class="zq-card" style="{border} padding:10px 12px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<span style="font-weight:800; color:#FFFFFF; font-size:14px;">{escape(row["Sector"])}</span>{_status_html(row)}</div>'
        f'<div class="zq-muted" style="font-size:11px; margin-top:3px;">Naik {row["Pct Up"]:.0f}% · Vol tinggi {row["Pct High Vol"]:.0f}% · '
        f'Median <span class="{"zq-up" if med >= 0 else "zq-down"}">{med:+.1f}%</span> · Persentil {row["Value Percentile"]:.0f}</div>'
        f'{_warn_html(row)}</div>'
    )


def _detail_header(row):
    """Panel kanan: angka lengkap sektor terpilih."""
    up_col = GREEN if row["Pct Up"] >= 55 else (PINK if row["Pct Up"] <= 40 else "#C9D1D9")
    med = float(row["Median Return (%)"])
    return (
        f'<div class="zq-card zq-card-accent">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
        f'<span style="font-weight:800; color:#FFFFFF; font-size:18px;">{escape(row["Sector"])}</span>{_status_html(row)}</div>'
        f'<div class="zq-row"><span>Saham naik hari ini</span><span style="color:{up_col}; font-weight:700;">{row["Pct Up"]:.0f}%</span></div>'
        f'<div class="zq-row"><span>Saham dengan volume di atas 1,5x biasanya</span><span>{row["Pct High Vol"]:.0f}%</span></div>'
        f'<div class="zq-row"><span>Median return hari ini</span><span class="{"zq-up" if med >= 0 else "zq-down"}">{med:+.2f}%</span></div>'
        f'<div class="zq-row"><span>Nilai transaksi vs 60 hari terakhir sektor ini</span><span>Persentil {row["Value Percentile"]:.0f}</span></div>'
        f'<div class="zq-row"><span>Saham likuid yang dianalisis</span><span>{int(row["N Members"])}</span></div>'
        f'{_warn_html(row)}</div>'
    )


_HOW_TO_READ = """
- **Saham naik**: persen saham likuid di sektor itu yang harganya naik hari ini.
- **Volume tinggi**: persen saham yang volumenya di atas 1,5x rata-rata 20 harinya sendiri.
- **Median return**: kenaikan/penurunan "tengah" sektor hari ini. Dipakai median supaya satu saham ekstrem tidak menipu.
- **Persentil nilai transaksi**: dibanding 60 hari terakhir sektor itu sendiri. 100 = hari ini paling ramai dalam 60 hari, 50 = biasa saja.
- **MENYALA**: nilai transaksi masuk 20% teratas kebiasaan sektor itu **dan** mayoritas saham naik **dan** tidak didominasi 1 saham. Angka hari = berapa hari berturut-turut kondisi ini terjadi.
- **Peringatan kuning**: sektor terlihat ramai tapi sebenarnya digerakkan 1 saham. Jangan dianggap sektor kompak.

Hanya saham dengan rata-rata transaksi 20 hari minimal Rp 1 M yang dihitung. Ini gambaran hari ini, bukan prediksi.
"""


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
    st.dataframe(view[["Saham", "Nama", "Close", "Change (%)", "RVOL", "Volatilitas"]], hide_index=True, **STRETCH, height=min(38 + 35 * len(view), 560))
    st.caption("RVOL = volume hari ini dibanding rata-rata 20 hari saham itu sendiri. Diurutkan dari RVOL tertinggi.")
    if det["Volatile Tinggi"].any():
        st.caption("Volatilitas tinggi = saham ini bergerak sangat liar (ATR > 8% dari harga). Angka RVOL/Change tetap dihitung sama, ini cuma catatan kehati-hatian.")


def load_radar():
    """(DataFrame radar, meta) dari file harian, di-cache per versi file. (None, None) kalau file belum ada."""
    _, meta = load_shared_file()
    if not meta:
        return None, None
    stamp = f"{meta.get('last_candle_date', '')}|{meta.get('updated_at_wib', '')}"
    return _cached_radar(stamp)



def _heatmap_html(dates, sectors, matrix):
    if not dates or not sectors:
        return '<div class="zq-muted" style="font-size:12px;">Heatmap tampil setelah histori beberapa hari terkumpul.</div>'
    header = "<div></div>" + "".join(f'<div style="writing-mode:vertical-rl; text-orientation:mixed; font-size:9px; color:#8B949E; text-align:right; padding-bottom:2px;">{escape(pd.to_datetime(d).strftime("%d/%m"))}</div>' for d in dates)
    rows = header
    for sec in sectors:
        cells = ""
        for d in dates:
            v = matrix[sec][d]
            color = "#00FF66" if v is True else ("#21262D" if v is False else "transparent")
            title = f"{escape(sec)} · {pd.to_datetime(d).strftime('%d %b')} · {'Menyala' if v is True else ('Netral' if v is False else 'Tidak ada data')}"
            cells += f'<div title="{title}" style="width:10px; height:10px; border-radius:2px; background:{color}; margin:1px auto;"></div>'
        rows += f'<div style="font-size:10px; color:#C9D1D9; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding-right:6px;">{escape(sec)}</div>{cells}'
    cols = f'auto repeat({len(dates)}, 12px)'
    return (
        f'<div style="display:grid; grid-template-columns:{cols}; align-items:center; gap:1px; overflow-x:auto; padding-bottom:4px;">{rows}</div>'
        f'<div style="display:flex; gap:12px; margin-top:6px; font-size:11px; color:#8B949E;">'
        f'<span><span style="display:inline-block; width:9px; height:9px; background:#00FF66; border-radius:2px; margin-right:4px;"></span>Menyala</span>'
        f'<span><span style="display:inline-block; width:9px; height:9px; background:#21262D; border-radius:2px; margin-right:4px;"></span>Netral</span></div>'
    )


def render_page_sector_radar():
    _html(
        f"""<div class="zq-hero">
<h1>{svg_icon("radar-2", 24, "#00F3FF", 2, margin_right=8)}SECTOR RADAR</h1>
<p>Sektor mana yang lagi ramai dana hari ini -- dibandingkan ke kebiasaan sektor itu sendiri, bukan angka mutlak.</p>
</div>"""
    )

    df, meta = load_radar()
    if df is None:
        st.info("Sector Radar butuh file data harian. Coba muat ulang setelah data harian versi terbaru berjalan.")
        return
    if df.empty:
        st.info("Belum ada sektor dengan saham likuid yang cukup untuk dianalisis pada data saat ini.")
        return

    as_of = (meta or {}).get("last_candle_date", "")
    if as_of:
        st.caption(f"Data penutupan {pd.to_datetime(as_of).strftime('%d %b %Y')} (file harian, diperbarui otomatis setelah bursa tutup). Deskriptif, bukan prediksi dan bukan rekomendasi.")

    sectors = list(df["Sector"])
    if st.session_state.get("sector_radar_selected") not in sectors:
        st.session_state["sector_radar_selected"] = sectors[0]
    sel = st.session_state["sector_radar_selected"]

    with keyed_container("zworkspace_sector"):
        col_left, col_right = st.columns([1.3, 2.7], gap="medium")
    with col_left:
        n_hot = int(df["Is Hot"].sum())
        _html(_label("bolt", f"{n_hot} sektor lagi menyala" if n_hot else "Belum ada sektor yang menyala"))
        with st.container(height=820, border=False):
            for _, row in df.iterrows():
                is_sel = row["Sector"] == sel
                _html(_sector_card(row, is_sel))
                if st.button(
                    f"SELECTED ({row['Sector']})" if is_sel else f"Lihat {row['Sector']}",
                    key=f"sr_pick_{row['Sector']}", **STRETCH,
                    type="primary" if is_sel else "secondary",
                ):
                    st.session_state["sector_radar_selected"] = row["Sector"]
                    st.rerun()
                st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    with col_right:
        row = df[df["Sector"] == sel].iloc[0]
        _html(_detail_header(row))
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        _html(_label("list-numbers", f"Saham di sektor {sel}"))
        data_map, _ = load_shared_file()
        if data_map:
            _detail_table(sel, data_map)
        with st.expander("Cara membaca Sector Radar", expanded=False):
            st.markdown(_HOW_TO_READ)

    _html(_label("calendar", "Heatmap 90 Hari Terakhir"))
    hist = load_sector_hist()
    if hist is None:
        st.info("Heatmap butuh riwayat harian. Tampil setelah data harian berjalan beberapa hari.")
    else:
        dates, sectors, matrix = heatmap_data(hist)
        _html(f'<div class="zq-card">{_heatmap_html(dates, sectors, matrix)}</div>')
        st.caption("Tiap kotak = satu hari bursa. Hijau = sektor itu 'menyala' hari itu. Diperbarui otomatis tiap hari lewat data harian.")


def render_sector_summary(pages, width):
    """Kartu ringkas untuk Home: sektor paling ramai hari ini + tautan ke halaman Sector Radar."""
    df, meta = load_radar()
    _html(_label("radar-2", "Sector Radar"))
    if df is None or df.empty:
        st.info("Ringkasan sektor tampil setelah data harian tersedia.")
        return
    top = df.head(3)
    cols = st.columns(len(top))
    for col, (_, row) in zip(cols, top.iterrows()):
        with col:
            _html(_sector_card(row, False))
    n_hot = int(df["Is Hot"].sum())
    st.caption(
        (f"{n_hot} sektor menyala hari ini. " if n_hot else "Belum ada sektor yang menyala hari ini. ")
        + "Diurutkan dari sektor paling ramai dibanding kebiasaannya sendiri."
    )
    with keyed_container("zopen_sector_radar"):
        st.page_link(pages["sector_radar"], label="Open Sector Radar", icon=":material/radar:", **width)
