"""Tema global Z-QUANT: satu tempat untuk gaya tombol, menu, popover, Home, dan footer.

Warna mengikuti tab screener (RSI/Stoch/Trade Planner) supaya semua halaman seragam.
"""
import streamlit as st

CYAN, PINK, GREEN, AMBER, GRAY = "#00F3FF", "#FF007F", "#00FF66", "#E3B341", "#8B949E"

_CSS = """
<style>
/* ---------- 1. Tombol (semua halaman) ---------- */
.stButton button,
div[data-testid="stHorizontalBlock"] .stButton button,
[data-testid="stPopover"] > button,
[data-testid="stPopover"] button {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%) !important;
    border: 1.5px solid #00F3FF !important;
    color: #00F3FF !important;
    border-radius: 8px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-weight: 700 !important;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover,
div[data-testid="stHorizontalBlock"] .stButton button:hover,
[data-testid="stPopover"] > button:hover,
[data-testid="stPopover"] button:hover {
    background: rgba(0, 243, 255, 0.2) !important;
    color: #ffffff !important;
    border-color: #FF007F !important;
    box-shadow: 0 0 18px rgba(255, 0, 127, 0.6) !important;
    transform: translateY(-1px) !important;
}

/* ---------- 1b. Tombol form dan unduh (hanya halaman Money Management + popover) ---------- */
[class*="st-key-mmpage_"] [data-testid="stFormSubmitButton"] button,
[class*="st-key-mmpage_"] [data-testid="stDownloadButton"] button,
[data-testid="stPopoverBody"] [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%) !important;
    border: 1.5px solid #00F3FF !important;
    color: #00F3FF !important;
    border-radius: 8px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-weight: 700 !important;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}
[class*="st-key-mmpage_"] [data-testid="stFormSubmitButton"] button:hover,
[class*="st-key-mmpage_"] [data-testid="stDownloadButton"] button:hover,
[data-testid="stPopoverBody"] [data-testid="stFormSubmitButton"] button:hover {
    background: rgba(0, 243, 255, 0.2) !important;
    color: #ffffff !important;
    border-color: #FF007F !important;
    box-shadow: 0 0 18px rgba(255, 0, 127, 0.6) !important;
}

/* ---------- 2. Popover ---------- */
[data-testid="stPopoverBody"] {
    background-color: #0d1b2a !important;
    border: 1px solid #00F3FF !important;
    border-radius: 8px !important;
}
[data-testid="stPopoverBody"] .stButton button {
    background: #161B22 !important;
    border: 1px solid #00F3FF !important;
    color: #00F3FF !important;
}
[data-testid="stPopoverBody"] .stButton button:hover {
    border-color: #FF007F !important;
    color: #FFFFFF !important;
    background: rgba(0, 243, 255, 0.15) !important;
}

/* ---------- 3. Menu atas (link halaman) ---------- */
[class*="st-key-znav_"] [data-testid="stPageLink"] a,
[class*="st-key-zcta_"] [data-testid="stPageLink"] a,
[class*="st-key-zopen_"] [data-testid="stPageLink"] a {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    height: 42px;
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%) !important;
    border: 1.5px solid #00F3FF !important;
    border-radius: 8px !important;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.25) !important;
    transition: all 0.3s ease !important;
    text-decoration: none !important;
}
/* warna untuk teks + ikon; font HANYA untuk teks (ikon Material butuh font ikonnya sendiri) */
[class*="st-key-znav_"] [data-testid="stPageLink"] a *,
[class*="st-key-zcta_"] [data-testid="stPageLink"] a *,
[class*="st-key-zopen_"] [data-testid="stPageLink"] a * {
    color: #00F3FF !important;
}
[class*="st-key-znav_"] [data-testid="stPageLink"] a p,
[class*="st-key-zcta_"] [data-testid="stPageLink"] a p,
[class*="st-key-zopen_"] [data-testid="stPageLink"] a p {
    font-family: 'Share Tech Mono', monospace !important;
    font-weight: 700 !important;
}
[class*="st-key-znav_"] [data-testid="stPageLink"] a:hover,
[class*="st-key-zcta_"] [data-testid="stPageLink"] a:hover,
[class*="st-key-zopen_"] [data-testid="stPageLink"] a:hover {
    background: rgba(0, 243, 255, 0.2) !important;
    border-color: #FF007F !important;
    box-shadow: 0 0 18px rgba(255, 0, 127, 0.6) !important;
    transform: translateY(-1px);
}
[class*="st-key-znav_"] [data-testid="stPageLink"] a:hover * { color: #FFFFFF !important; }
/* halaman aktif */
[class*="st-key-znav_"][class*="__active"] [data-testid="stPageLink"] a,
[class*="st-key-znav_"][class*="__active"] [data-testid="stPopover"] button {
    background: linear-gradient(135deg, rgba(0, 243, 255, 0.22) 0%, rgba(255, 0, 127, 0.14) 100%) !important;
    box-shadow: 0 0 16px rgba(0, 243, 255, 0.55) !important;
}
[class*="st-key-znav_"][class*="__active"] [data-testid="stPageLink"] a *,
[class*="st-key-znav_"][class*="__active"] [data-testid="stPopover"] button * { color: #FFFFFF !important; }
/* tombol ajakan sekunder (Home) */
[class*="st-key-zcta_secondary"] [data-testid="stPageLink"] a {
    border-color: #30363D !important;
    box-shadow: none !important;
}
[class*="st-key-zcta_secondary"] [data-testid="stPageLink"] a * { color: #C9D1D9 !important; }

/* ---------- 4. Kartu screener di dropdown ---------- */
[class*="st-key-zscr_"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 6px 10px 2px 10px;
    margin-bottom: 4px;
}
[class*="st-key-zscr_"][class*="__active"] {
    border-color: #00F3FF;
    background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.08) 100%);
}
[class*="st-key-zscr_"] [data-testid="stPageLink"] a { padding-left: 0 !important; }
[class*="st-key-zscr_"] [data-testid="stPageLink"] a * { color: #FFFFFF !important; }
[class*="st-key-zscr_"] [data-testid="stPageLink"] a [data-testid="stIconMaterial"] { color: #00F3FF !important; }
[class*="st-key-zscr_"] [data-testid="stPageLink"] a p {
    font-weight: 700 !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[class*="st-key-zscr_"] [data-testid="stPageLink"] a:hover * { color: #00F3FF !important; }
[class*="st-key-zscr_"] [data-testid="stCaptionContainer"] { margin-top: -10px; }
[class*="st-key-zscr_"] [data-testid="stCaptionContainer"],
[class*="st-key-zscr_"] [data-testid="stCaptionContainer"] * { color: #8B949E !important; opacity: 1 !important; }

/* ---------- 5. Komponen Home / How To ---------- */
.zq-label {
    display: flex; align-items: center; gap: 6px;
    color: #FF007F; font-size: 11px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase; margin: 18px 0 8px 0; font-family: 'Share Tech Mono', monospace;
}
.zq-hero {
    background: linear-gradient(135deg, rgba(0, 243, 255, 0.10) 0%, rgba(255, 0, 127, 0.08) 100%);
    border: 1.5px solid #00F3FF; border-radius: 10px; padding: 22px 24px 18px 24px;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.15); margin-bottom: 10px;
}
.zq-hero h1 {
    color: #00F3FF !important; font-size: 26px !important; font-weight: 900 !important;
    letter-spacing: 2px; margin: 0 0 6px 0 !important; padding: 0 !important;
    text-shadow: 0 0 10px rgba(0, 243, 255, 0.5); font-family: 'Share Tech Mono', monospace !important;
}
.zq-hero p { color: #C0C5D0; font-size: 14px; margin: 0; }
.zq-card {
    background: #161B22; border: 1px solid #30363D; border-radius: 8px;
    padding: 12px 14px; height: 100%;
}
.zq-card-accent { border-color: #00F3FF; }
.zq-stat-label { color: #8B949E; font-size: 11px; letter-spacing: 0.5px; }
.zq-stat-value { color: #FFFFFF; font-size: 20px; font-weight: 800; margin-top: 2px; white-space: nowrap; }
.zq-stat-sub { font-size: 12px; margin-top: 2px; }
.zq-chip {
    display: inline-block; font-size: 10px; padding: 1px 7px; border-radius: 4px;
    border: 1px solid #00F3FF; color: #00F3FF; margin-bottom: 6px;
}
.zq-row { display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; border-bottom: 1px dashed #21262D; }
.zq-row:last-child { border-bottom: none; }
.zq-muted { color: #8B949E; }
.zq-grid { display: grid; gap: 8px; }
.zq-grid6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.zq-grid4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.zq-grid .zq-stat-value { overflow: hidden; text-overflow: ellipsis; }
@media (max-width: 1000px) { .zq-grid6 { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { .zq-grid4 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .zq-grid6 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.zq-up { color: #00FF66; }
.zq-down { color: #FF007F; }
.zq-step-no {
    display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px;
    border-radius: 50%; border: 1px solid #00F3FF; color: #00F3FF; font-size: 12px; font-weight: 800; margin-right: 6px;
}
.zq-disclaimer { color: #6C7A9C; font-size: 11px; line-height: 1.5; margin-top: 18px; }
.zq-doc h4 { color: #00F3FF !important; font-size: 15px !important; margin: 14px 0 6px 0 !important; }
.zq-doc p, .zq-doc li { color: #C0C5D0; font-size: 14px; line-height: 1.6; }
.zq-doc code { color: #00F3FF; background: rgba(0, 243, 255, 0.08); }

/* ---------- 5b. Layar HP: menu 3 per baris, Run/Stop tetap bersebelahan ---------- */
@media (max-width: 640px) {
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-znav_"]) {
        flex-wrap: wrap !important; gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-znav_"]) > div {
        flex: 1 1 calc(33.333% - 6px) !important; min-width: calc(33.333% - 6px) !important; width: auto !important;
    }
    [class*="st-key-znav_"] [data-testid="stPageLink"] a,
    [class*="st-key-znav_"] [data-testid="stPopover"] button { height: 38px; padding: 0 6px !important; }
    [class*="st-key-znav_"] [data-testid="stPageLink"] a p,
    [class*="st-key-znav_"] [data-testid="stPopover"] button p { font-size: 12px !important; }
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_run_"]) { flex-wrap: nowrap !important; gap: 8px !important; }
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-btn_run_"]) > div { min-width: 0 !important; flex: 1 1 0 !important; }
    /* Watchlist: filter/sort, Refresh/Manage/CSV, dan Select/Remove tetap satu baris */
    [class*="st-key-wlrow_"] div[data-testid="stHorizontalBlock"],
    [class*="st-key-mmrow_"] div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 6px !important; }
    [class*="st-key-wlrow_"] div[data-testid="stHorizontalBlock"] > div,
    [class*="st-key-mmrow_"] div[data-testid="stHorizontalBlock"] > div { min-width: 0 !important; flex: 1 1 0 !important; }
    [class*="st-key-wlrow_"] button, [class*="st-key-mmrow_"] button { padding-left: 4px !important; padding-right: 4px !important; }
    [class*="st-key-wlrow_"] button p, [class*="st-key-mmrow_"] button p {
        font-size: 12px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
}

/* ---------- 5c. Kotak input (semua halaman): border dibuat kontras ----------
   Bawaan Streamlit: border kotak input berwarna SAMA dengan latarnya, jadi kotak tidak terlihat. */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-testid="stNumberInputContainer"],
[data-testid="stTextInputRootElement"],
[data-testid="stDateInputField"],
[data-testid="stTimeInputField"],
[data-testid="stTextAreaRootElement"] {
    border: 1px solid #3D4B5E !important;
    border-radius: 6px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stSelectbox"] > div > div:hover,
[data-testid="stMultiSelect"] > div > div:hover,
[data-testid="stNumberInputContainer"]:hover,
[data-testid="stTextInputRootElement"]:hover,
[data-testid="stDateInputField"]:hover,
[data-testid="stTimeInputField"]:hover,
[data-testid="stTextAreaRootElement"]:hover {
    border-color: #5A6B80 !important;
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stMultiSelect"] > div > div:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stDateInputField"]:focus-within,
[data-testid="stTimeInputField"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within {
    border-color: #00F3FF !important;
    box-shadow: 0 0 8px rgba(0, 243, 255, 0.25) !important;
}
/* Form & expander: garis tepi sedikit lebih terang supaya bloknya terbaca */
[data-testid="stForm"] { border-color: #30363D !important; }
[data-testid="stExpander"] details { border-color: #30363D !important; }

/* Pilihan mode Trend Scanner: gaya sama dengan pilihan mode RSI/Stoch (cyan) */
[class*="st-key-ztrend_mode"] [data-testid="stSelectbox"] > div > div {
    background-color: #0D1117 !important;
    border: 1.5px solid #00F3FF !important;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
}
[class*="st-key-ztrend_mode"] [data-testid="stSelectbox"] > div > div:hover {
    border-color: #FF007F !important;
    box-shadow: 0 0 15px rgba(255, 0, 127, 0.4) !important;
}
[class*="st-key-ztrend_mode"] [data-testid="stSelectbox"] * { color: #00F3FF !important; font-weight: 700 !important; }

/* ---------- 5d. Workspace 2 kolom (RSI/Stoch/Trend/Sector Radar): susun ke bawah di layar sempit.
   Streamlit TIDAK menyusun kolom otomatis di layar sempit (cuma soal lebar kontainer, bukan viewport),
   jadi tanpa ini kolom kiri-kanan tetap sebaris dan jadi sempit banget di HP. */
@media (max-width: 900px) {
    [class*="st-key-zworkspace_"] div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    [class*="st-key-zworkspace_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important;
    }
}

/* ---------- 5e. Rekap screener di Home (4 kartu): 2 per baris di tablet, 1 per baris di HP.
   Beda dari zworkspace_ (yang selalu full stack) krn ini kartu SEJAJAR yang wajar dibaca 2x2. */
@media (max-width: 1100px) {
    [class*="st-key-zrecap_"] div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    [class*="st-key-zrecap_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        flex: 1 1 46% !important; min-width: 220px !important;
    }
}
@media (max-width: 640px) {
    [class*="st-key-zrecap_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        flex: 1 1 100% !important; min-width: 100% !important;
    }
}

/* ---------- 5f. Lonceng notifikasi icon-only (header, sebelah chip profil): tombol bulat kecil,
   tanpa teks/label, badge kecil nempel di pojok kalau ada yang belum dibaca. Rata kanan di
   kolomnya sendiri biar nempel ke chip profil di sebelahnya, bukan nongkrong di tengah. ---------- */
[class*="st-key-zheader_bell"] {
    display: flex; justify-content: flex-end;
}
[class*="st-key-zbell"] {
    position: relative;
    display: inline-block;
    width: 38px;
}
[class*="st-key-zbell"] div[data-testid="stPopover"] button {
    border-radius: 50% !important;
    width: 38px !important; height: 38px !important;
    padding: 0 !important;
    display: flex; align-items: center; justify-content: center;
}
[class*="st-key-zbell"] div[data-testid="stPopover"] button p {
    display: none;  /* label kosong tetap bisa render <p> kosong di sebagian versi -- pastikan tidak makan ruang */
}
[class*="st-key-zbell"] .zq-bell-badge {
    position: absolute; top: -2px; right: -2px; z-index: 5;
    background: #FF007F; color: #0D1117; font-size: 10px; font-weight: 800;
    min-width: 16px; height: 16px; line-height: 16px; text-align: center;
    border-radius: 8px; padding: 0 3px; pointer-events: none;
}

/* ---------- 6. Footer IHSG + jam ---------- */
.block-container { padding-bottom: 4.5rem !important; }
.zq-footer {
    position: fixed; left: 14px; bottom: 12px; z-index: 999990;
    display: flex; align-items: center; gap: 14px;
    background: rgba(13, 27, 42, 0.96); border: 1px solid #00F3FF; border-radius: 8px;
    padding: 6px 12px; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);
    font-family: 'Share Tech Mono', monospace; font-size: 12px; color: #C0C5D0;
    white-space: nowrap;
}
.zq-footer #zq-f-data { display: inline-flex; align-items: center; gap: 8px; }
.zq-footer .zq-f-idx { color: #FFFFFF; font-weight: 800; }
.zq-footer .zq-f-sep { width: 1px; height: 14px; background: #30363D; }
.zq-footer .zq-f-note { color: #8B949E; font-size: 11px; }
.zq-footer #zq-clock { color: #00F3FF; font-weight: 800; min-width: 92px; }
.zq-mkt { font-size: 10px; padding: 1px 6px; border-radius: 4px; border: 1px solid #8B949E; color: #8B949E; }
.zq-mkt-open { border-color: #00FF66; color: #00FF66; }
.zq-mkt-break { border-color: #E3B341; color: #E3B341; }
@media (max-width: 640px) {
    .zq-footer { left: 6px; right: 6px; bottom: 6px; justify-content: space-between; gap: 8px; font-size: 11px; }
    .zq-footer .zq-f-note { display: none; }
}
</style>
"""


def inject_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def hide_sidebar_nav():
    """Dipakai kalau versi Streamlit belum mendukung st.navigation(position="hidden")."""
    st.markdown(
        "<style>[data-testid='stSidebarNav'], [data-testid='stSidebar'] {display: none !important;}</style>",
        unsafe_allow_html=True,
    )
