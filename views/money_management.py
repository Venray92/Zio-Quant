"""Halaman Money Management: portofolio, ukuran posisi, jurnal, dan pengaturan risiko.
Perhitungan ada di engines/money.py, penyimpanan dan aksi di utils/money_store.py."""
import csv
import inspect
import io
import re
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines import money as M
from engines.sector_map import display_name, get_company_name
from engines.market_data import now_wib
from engines.trade_planner import TradePlanner
from utils import market_source, money_store as ms, watchlist_store
from utils.card_html import GREEN, PINK, build_card, compact_html, fmt_id, info_row, pill, source_note_html
from utils.icons import expander_kwargs, icon_kwargs, svg_icon
from utils.pages import keyed_container
from utils.profile import render_profile_card

SECTIONS = ["Portfolio", "Position sizer", "Journal", "Settings"]
AMBER, CYAN = "#E3B341", "#00F3FF"


def _stretch(fn):
    """Lebar penuh: pakai width="stretch" bila tersedia, kalau tidak use_container_width (versi Streamlit lama)."""
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


_W = {n: _stretch(getattr(st, n)) for n in ("button", "form_submit_button", "popover", "download_button", "dataframe", "plotly_chart")}


# ---------------------------------------------------------------- format
def _dec(x, d=1):
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _pct(v, d=1, sign=False):
    return (f"{v:+,.{d}f}" if sign else f"{v:,.{d}f}").replace(",", "#").replace(".", ",").replace("#", ".") + "%"


def _rr(v, unit="R"):
    """Kelipatan risiko dengan tanda dan koma desimal, mis. +2,5R."""
    return ("-" if v < 0 else "+") + _dec(abs(v), 1) + unit


def _rp(v):
    return ("-" if v < 0 else "") + "Rp " + fmt_id(abs(v))


def _rp_short(v, sign=False):
    a = abs(v)
    s = "-" if v < 0 else ("+" if sign and v > 0 else "")
    if a >= 1e12:
        return f"{s}Rp {_dec(a / 1e12, 2)} T"
    if a >= 1e9:
        return f"{s}Rp {_dec(a / 1e9, 2)} M"
    if a >= 1e6:
        return f"{s}Rp {_dec(a / 1e6, 1)} jt"
    if a >= 1e3:
        return f"{s}Rp {_dec(a / 1e3, 0)} rb"
    return f"{s}Rp {fmt_id(a)}"


def _bucket():
    n = now_wib()
    return n.strftime("%Y%m%d%H") + str(n.minute // 5)


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def _gap(px=8):
    st.markdown(f"<div style='height:{px}px;'></div>", unsafe_allow_html=True)


def _label(icon, text):
    return f'<div class="zq-label">{svg_icon(icon, 13, "#FF007F", 2)}{escape(text)}</div>'


def _stat(label, value, sub="", cls="", extra=""):
    return (
        f'<div class="zq-card"><div class="zq-stat-label">{escape(label)}</div>'
        f'<div class="zq-stat-value {cls}">{value}</div><div class="zq-stat-sub">{sub}</div>{extra}</div>'
    )


def _grid(cards, cols=6):
    return f'<div class="zq-grid zq-grid{cols}">{"".join(cards)}</div>'


def _bar(pct_fill, color):
    return (
        '<div style="height:5px; background:#30363D; border-radius:3px; margin-top:6px; overflow:hidden;">'
        f'<div style="width:{max(0, min(100, pct_fill)):.1f}%; height:5px; background:{color};"></div></div>'
    )


_LEVEL_ICON = {
    "ok": ("circle-check", GREEN),
    "warn": ("alert-triangle", AMBER),
    "fail": ("circle-x", PINK),
    "info": ("info-circle", CYAN),
}


def _line(level, text):
    name, color = _LEVEL_ICON.get(level, _LEVEL_ICON["info"])
    return (
        f'<div style="display:flex; gap:6px; align-items:flex-start; margin:3px 0; font-size:13px; color:#C9D1D9;">'
        f'{svg_icon(name, 15, color, 2)}<span>{escape(text)}</span></div>'
    )


def _panel(icon, title, body):
    return f'<div class="zq-card" style="margin-bottom:8px;"><div style="color:#00F3FF; font-weight:800; margin-bottom:6px;">{svg_icon(icon, 15, "#00F3FF", 2, margin_right=6)}{escape(title)}</div>{body}</div>'


def _check_text(c):
    k, a = c["key"], c["args"]
    if k == "total_risk":
        return f"Total risiko {_pct(a['pct'])} dari batas {_pct(a['cap'], 0)}"
    if k == "cash":
        return f"Cash {_pct(a['pct'], 0)}, minimum {_pct(a['min'], 0)}"
    if k == "slots":
        return f"Posisi {a['n']} dari maksimal {a['max']}"
    if k == "concentration":
        return f"Bobot terbesar {a['ticker'].replace('.JK', '')} {_pct(a['pct'], 0)} (maks {_pct(a['max'], 0)})"
    if k == "sl_hit":
        return f"{a['ticker']} sudah menembus stop loss. Cek segera."
    if k == "near_sl":
        return f"{a['ticker']} tinggal {_pct(a['pct'])} dari stop loss"
    if k == "no_sl":
        return f"{a['ticker']} belum punya stop loss (risiko dihitung penuh)"
    if k == "no_price":
        return f"Harga {a['ticker']} belum tersedia, dihitung di harga rata-rata"
    if k == "tp_hit":
        return f"{a['ticker']} sudah mencapai {a['tp']}: pertimbangkan jual sebagian"
    return k


def _impact_text(c):
    k, a = c["key"], c["args"]
    if k == "total_risk":
        return f"Risiko terbuka {_pct(a['before'])} jadi {_pct(a['pct'])} (batas {_pct(a['cap'], 0)})"
    if k == "cash":
        return f"Cash {_pct(a['before'], 0)} jadi {_pct(a['pct'], 0)} (minimum {_pct(a['min'], 0)})"
    if k == "slots":
        return f"Posisi jadi {a['n']} dari maksimal {a['max']}"
    return k


_MSG = {
    "added": "{ticker}: {lots} lot ditambahkan ke portofolio.",
    "merged": "{ticker}: digabung dengan posisi yang ada (harga rata-rata diperbarui).",
    "cash_short": "Cash tidak cukup{short}. Tambah setoran atau kurangi lot.",
    "bad_ticker": "Kode saham tidak valid.",
    "bad_lots": "Jumlah lot minimal 1.",
    "bad_price": "Harga tidak valid.",
    "sl_above_price": "Stop loss harus di bawah harga beli.",
    "tp1_below_price": "TP1 harus di atas harga beli.",
    "tp2_below_tp1": "TP2 tidak boleh di bawah TP1.",
    "tp2_below_price": "TP2 harus di atas harga beli.",
    "too_many": "Jumlah posisi sudah di batas maksimum ({max}).",
    "lots_out_of_range": "Jumlah lot jual harus antara 1 dan jumlah lot yang dimiliki.",
    "not_found": "Data tidak ditemukan (mungkin sudah berubah). Muat ulang halaman.",
    "edited": "Perubahan disimpan.",
    "deleted": "Dihapus.",
    "deposit": "Setoran tercatat.",
    "withdraw": "Penarikan tercatat.",
    "removed": "Setoran dihapus.",
    "would_go_negative": "Cash akan menjadi negatif jika setoran ini dihapus.",
    "bad_amount": "Nominal tidak valid.",
    "reset": "Data portofolio dikosongkan.",
}


def _msg(code, info):
    if code == "sold":
        t = info["trade"]
        return f"{t['ticker'].replace('.JK', '')}: terjual {t['lots']} lot, hasil {_rp_short(t['pnl'], sign=True)} ({_pct(t['pnl_pct'], 1, True)})."
    text = _MSG.get(code, code)
    fmt = {**info}
    if "short" in info:
        fmt["short"] = f" (kurang {_rp_short(info['short'])})"
    else:
        fmt["short"] = ""
    try:
        return text.format(**fmt)
    except (KeyError, IndexError):
        return text


def _done(result, keep_open=False):
    """Tampilkan hasil aksi: sukses = toast lalu muat ulang, gagal = pesan error di tempat."""
    ok, code, info = result
    text = _msg(code, info)
    if ok:
        if info.get("saved") is False:
            text += " (Belum tersimpan di cloud, cek Storage status.)"
        st.toast(text)
        st.rerun()
    else:
        st.error(text)


# ---------------------------------------------------------------- data harga
@st.cache_data(ttl=300, show_spinner=False)
def _prices(tickers, bucket):
    frames, source = market_source.get_histories(list(tickers))
    out = {}
    for t in tickers:
        try:
            df = frames.get(t)
            closes = pd.to_numeric(df["Close"], errors="coerce").dropna()
            if len(closes):
                out[t] = {"last": float(closes.iloc[-1]), "date": pd.to_datetime(df["Date"]).iloc[-1].strftime("%Y-%m-%d")}
        except Exception:
            pass
    return {"prices": out, "source": source}


# ---------------------------------------------------------------- CSV
_HEADERS = {
    "ticker": ("ticker", "kode", "saham", "code", "symbol"),
    "lots": ("lots", "lot"),
    "avg": ("avg", "avg price", "avg_price", "harga", "price", "harga rata-rata", "average"),
    "sl": ("sl", "stop loss", "stoploss", "stop_loss"),
    "tp1": ("tp1", "tp 1", "target 1", "target1"),
    "tp2": ("tp2", "tp 2", "target 2", "target2"),
    "opened": ("opened", "date", "tanggal", "tgl"),
    "note": ("note", "notes", "catatan"),
}


def parse_number(v):
    """'9.450' / '9,450' / 'Rp 9.450,5' / 9450 -> float. None bila bukan angka."""
    s = re.sub(r"[^0-9.,-]", "", str(v if v is not None else ""))
    if not s or s in "-.,":
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and re.fullmatch(r"-?\d{1,3}\.\d{3}", s)):
        s = s.replace(".", "")
    elif s.count(",") > 1 or (s.count(",") == 1 and re.fullmatch(r"-?\d{1,3},\d{3}", s)):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_positions_csv(text, max_rows=200):
    """Return (rows, error). rows: list dict siap untuk money_store.import_positions."""
    text = str(text or "").replace("\ufeff", "")
    if not text.strip():
        return [], "empty"
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return [], "empty"
    header = [h.strip().lower() for h in rows[0]]
    col = {}
    for field, names in _HEADERS.items():
        for i, h in enumerate(header):
            if h in names and field not in col:
                col[field] = i
    if not {"ticker", "lots", "avg"} <= set(col):
        return [], "header"
    out = []
    for r in rows[1: max_rows + 1]:
        get = lambda f: r[col[f]].strip() if f in col and col[f] < len(r) else ""
        lots, avg = parse_number(get("lots")), parse_number(get("avg"))
        out.append({
            "ticker": get("ticker"), "lots": int(lots) if lots else 0, "avg": avg or 0,
            "sl": parse_number(get("sl")) or 0, "tp1": parse_number(get("tp1")) or 0, "tp2": parse_number(get("tp2")) or 0,
            "opened": get("opened"), "note": get("note"),
        })
    return out, None


def _csv_safe(v):
    s = str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


# ---------------------------------------------------------------- PORTFOLIO
def _render_onboarding():
    _html(
        f"""<div class="zq-card" style="margin-bottom:8px;">
<div style="color:#FFFFFF; font-weight:800; font-size:15px;">{svg_icon("wallet", 18, "#00F3FF", 2, margin_right=6)}Set your starting capital</div>
<div class="zq-muted" style="font-size:12px; margin-top:4px;">Masukkan modal yang kamu siapkan untuk trading. Cash, equity, dan batas risiko dihitung dari sini. Sudah punya saham? Setelah ini tambahkan lewat Add position dan centang Already owned.</div>
</div>"""
    )
    with st.form("mm_capital_form", border=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            amt = st.number_input("Starting capital (Rp)", min_value=0, value=100_000_000, step=1_000_000, format="%d")
        with c2:
            when = st.date_input("Date", value=now_wib().date())
        go = st.form_submit_button("Save capital", **_W["form_submit_button"], **icon_kwargs("savings"))
    if go:
        _done(ms.add_cashflow(amt, "Starting capital", when.isoformat()))


def _position_card(r, s):
    code = r["ticker"].replace(".JK", "")
    f = r["flags"]
    accent = PINK if "sl_hit" in f else (AMBER if ("near_sl" in f or "no_sl" in f) else None)
    col = GREEN if r["pnl"] >= 0 else PINK
    rows = info_row(f"avg {fmt_id(r['avg'])} · {fmt_id(r['lots'] * M.LOT)} lembar", "tag")
    rows += info_row(
        f'<span style="color:{col}; font-weight:700;">{_rp_short(r["pnl"], True)} ({_pct(r["pnl_pct"], 1, True)})</span> '
        f'<span style="color:#8B949E;">· nilai {_rp_short(r["value"])}</span>',
        "trending-up" if r["pnl"] >= 0 else "trending-down",
        color=col,
    )
    over = "overweight" in f
    rows += (
        f'<div style="font-size:11px; color:#8B949E; margin-top:6px;">Bobot {_pct(r["weight_pct"], 0)} dari equity (maks {_pct(s["max_alloc_pct"], 0)})</div>'
        + _bar(r["weight_pct"] / s["max_alloc_pct"] * 100, AMBER if over else CYAN)
    )
    pills = ""
    if r["sl"] > 0:
        kind = "red" if "sl_hit" in f else ("amber" if "near_sl" in f else "neutral")
        pills += pill(f"SL {fmt_id(r['sl'])} ({_pct(r['dist_sl_pct'])})", kind)
    else:
        pills += pill("No stop loss", "amber")
    if r["risk_free"]:
        pills += pill("Risk-free", "green")
    if r["r_now"] is not None:
        pills += pill(_rr(r["r_now"]), "green" if r["r_now"] >= 0 else "red")
    if r["tp1"] > 0:
        prog = f" · {int(max(0, min(999, (r['tp1_progress'] or 0) * 100)))}%" if r["tp1_progress"] is not None else ""
        pills += pill(f"TP1 {fmt_id(r['tp1'])}{prog}", "cyan" if "tp1_hit" in f or "tp2_hit" in f else "neutral")
    if "tp2_hit" in f:
        pills += pill("TP2 reached", "cyan")
    if over:
        pills += pill("Overweight", "amber")
    if "no_price" in f:
        pills += pill("No price data", "amber")
    if r.get("strategy"):
        pills += pill(r["strategy"])
    if r.get("opened"):
        pills += pill(f"Opened {pd.to_datetime(r['opened']).strftime('%d %b')}")
    if r.get("note"):
        pills += pill(r["note"])
    return build_card(False, code, f'<span style="font-size:10px; padding:1px 6px; border:1px solid {CYAN}; color:{CYAN}; border-radius:4px; font-weight:700;">{r["lots"]} lot</span>',
                      r["last"] if r["has_price"] else None, None, rows, pills, accent=accent)


def _position_actions(r):
    pid = r["id"]
    with keyed_container(f"mmrow_pos_{pid}"):
        c1, c2, c3 = st.columns(3)
    with c1:
        with st.popover("Sell", **_W["popover"], **icon_kwargs("sell", "popover")):
            with st.form(f"mm_sell_{pid}", border=False):
                lots = st.number_input("Lots to sell", min_value=1, max_value=r["lots"], value=r["lots"], step=1)
                price = st.number_input("Sell price (Rp)", min_value=1, value=max(1, int(round(r["last"]))), step=1, format="%d")
                a, b = st.columns(2)
                with a:
                    reason = st.selectbox("Reason", list(ms.REASONS))
                with b:
                    when = st.date_input("Date", value=now_wib().date())
                note = st.text_input("Note", max_chars=120)
                go = st.form_submit_button("Confirm sell", **_W["form_submit_button"], **icon_kwargs("check"))
            if go:
                _done(ms.sell(pid, lots, price, reason, note, when.isoformat()))
    with c2:
        with st.popover("Edit", **_W["popover"], **icon_kwargs("edit", "popover")):
            with st.form(f"mm_edit_{pid}", border=False):
                sl = st.number_input("Stop loss (0 = none)", min_value=0, value=int(r["sl"]), step=1, format="%d")
                tp1 = st.number_input("Target 1 (0 = none)", min_value=0, value=int(r["tp1"]), step=1, format="%d")
                tp2 = st.number_input("Target 2 (0 = none)", min_value=0, value=int(r["tp2"]), step=1, format="%d")
                note = st.text_input("Note", value=r.get("note", ""), max_chars=120)
                go = st.form_submit_button("Save", **_W["form_submit_button"], **icon_kwargs("save"))
            if go:
                _done(ms.edit_position(pid, sl, tp1, tp2, note))
    with c3:
        with st.popover("Delete", **_W["popover"], **icon_kwargs("delete", "popover")):
            st.caption("Batalkan pembelian ini: posisi dihapus dan cash kembali. Tidak masuk jurnal. Untuk menjual, pakai Sell.")
            sure = st.checkbox("Yes, delete this position", key=f"mm_del_ok_{pid}")
            if st.button("Delete position", key=f"mm_del_{pid}", disabled=not sure, **_W["button"]):
                _done(ms.delete_position(pid))


def _render_add_position(doc):
    wl = [t.replace(".JK", "") for t in watchlist_store.tickers()]
    have = set(wl)
    options = wl + [c for c in (t.replace(".JK", "") for t in get_all_ihsg_tickers()) if c not in have]
    with st.expander("Add position", expanded=not doc["positions"], **expander_kwargs("add")):
        with st.form("mm_add_form", clear_on_submit=False, border=False):
            if options:
                ticker = st.selectbox("Ticker", options, index=None, placeholder="Type a ticker or company name, e.g. BBCA",
                                      format_func=lambda c: display_name(c))
            else:
                ticker = st.text_input("Ticker", placeholder="BBCA")
            c1, c2 = st.columns(2)
            with c1:
                lots = st.number_input("Lots", min_value=1, value=1, step=1)
            with c2:
                price = st.number_input("Buy price (Rp)", min_value=0, value=None, step=1, format="%d", placeholder="mis. 6100")
            c3, c4, c5 = st.columns(3)
            with c3:
                sl = st.number_input("Stop loss", min_value=0, value=0, step=1, format="%d")
            with c4:
                tp1 = st.number_input("Target 1", min_value=0, value=0, step=1, format="%d")
            with c5:
                tp2 = st.number_input("Target 2", min_value=0, value=0, step=1, format="%d")
            c6, c7 = st.columns(2)
            with c6:
                when = st.date_input("Buy date", value=now_wib().date())
            with c7:
                strategy = st.selectbox("Strategy", ["", "BOW", "BOB"], format_func=lambda v: v or "-")
            note = st.text_input("Note", max_chars=120)
            owned = st.checkbox("Already owned (count as deposit, don't deduct cash)")
            go = st.form_submit_button("Add position", **_W["form_submit_button"], **icon_kwargs("add_circle"))
        if go:
            if not ticker:
                st.error(_MSG["bad_ticker"])
            elif not price:
                st.error("Isi harga beli.")
            else:
                _done(ms.add_position(ticker, lots, price, sl, tp1, tp2, when.isoformat(), note, strategy, owned))


def _render_import_export(doc, summary):
    with st.expander("Import / export", expanded=False, **expander_kwargs("swap_vert")):
        st.caption("Kolom CSV: Ticker, Lots, Avg (wajib) plus SL, TP1, TP2, Opened, Note. Pemisah koma, titik koma, atau tab.")
        up = st.file_uploader("CSV file", type=["csv"], key="mm_csv")
        if up is not None:
            text = up.getvalue()[:200_000].decode("utf-8-sig", errors="replace")
            rows, err = parse_positions_csv(text)
            if err == "header":
                st.error("Header tidak dikenali. Butuh kolom Ticker, Lots, dan Avg.")
            elif err or not rows:
                st.error("File kosong.")
            else:
                st.dataframe(pd.DataFrame(rows), hide_index=True, **_W["dataframe"])
                owned = st.checkbox("Already owned (count as deposit, don't deduct cash)", key="mm_csv_owned")
                if st.button("Import positions", key="mm_csv_go", **_W["button"], **icon_kwargs("upload")):
                    ok, code, res = ms.import_positions(rows, owned)
                    text = f"Impor selesai: {res['added']} baru, {res['merged']} digabung, {len(res['errors'])} ditolak."
                    if res["errors"]:
                        st.warning(text + " Baris ditolak: " + ", ".join(f"#{i} ({_MSG.get(c, c).split('.')[0]})" for i, c in res["errors"][:8]))
                    else:
                        st.toast(text)
                        st.rerun()
        d1, d2 = st.columns(2)
        with d1:
            df = pd.DataFrame(
                [{"Ticker": p["ticker"].replace(".JK", ""), "Lots": p["lots"], "Avg": round(p["avg"], 2), "SL": p["sl"], "TP1": p["tp1"], "TP2": p["tp2"], "Opened": p["opened"], "Note": _csv_safe(p["note"])} for p in doc["positions"]],
                columns=["Ticker", "Lots", "Avg", "SL", "TP1", "TP2", "Opened", "Note"],
            )
            st.download_button("Export CSV", df.to_csv(index=False).encode("utf-8"), file_name="positions.csv", mime="text/csv", **_W["download_button"], key="mm_dl_pos", **icon_kwargs("download", "download_button"))
        with d2:
            tpl = "Ticker,Lots,Avg,SL,TP1,TP2,Opened,Note\nBBCA,40,6100,5850,6800,7300,2026-09-01,contoh\n"
            st.download_button("Template", tpl.encode("utf-8"), file_name="positions_template.csv", mime="text/csv", **_W["download_button"], key="mm_dl_tpl", **icon_kwargs("description", "download_button"))


def _render_portfolio(doc, settings, summary, snap):
    if not doc["cashflows"]:
        _render_onboarding()
        return
    s, eq = settings, summary["equity"]
    checks = M.risk_checks(summary, s)
    scen = M.scenarios(summary, s)
    lvl = {c["key"]: c["level"] for c in checks if c["key"] in ("total_risk", "cash", "slots")}
    col_of = {"ok": "", "warn": "color:#E3B341;", "fail": "color:#FF007F;"}
    ret = (eq - summary["deposits"]) / summary["deposits"] * 100 if summary["deposits"] > 0 else 0.0
    n_trades = len(doc["journal"])
    cards = [
        _stat("Equity", _rp_short(eq), f'<span class="zq-muted">modal {_rp_short(summary["deposits"])} · {_pct(ret, 1, True)}</span>'),
        _stat("Cash", f'<span style="{col_of[lvl["cash"]]}">{_rp_short(summary["cash"])}</span>', f'<span class="zq-muted">{_pct(summary["cash_pct"], 0)} (min {_pct(s["min_cash_pct"], 0)})</span>'),
        _stat("Open risk", f'<span style="{col_of[lvl["total_risk"]]}">{_pct(summary["open_risk_pct"])}</span>', f'<span class="zq-muted">{_rp_short(summary["open_risk"])} · batas {_pct(s["max_total_risk_pct"], 0)}</span>',
              extra=_bar(summary["open_risk_pct"] / s["max_total_risk_pct"] * 100, {"ok": GREEN, "warn": AMBER, "fail": PINK}[lvl["total_risk"]])),
        _stat("Unrealized P/L", f'<span class="{"zq-up" if summary["unrealized"] >= 0 else "zq-down"}">{_rp_short(summary["unrealized"], True)}</span>',
              f'<span class="zq-muted">{_pct(summary["unrealized"] / summary["invested_cost"] * 100 if summary["invested_cost"] else 0, 1, True)} dari biaya</span>'),
        _stat("Realized P/L", f'<span class="{"zq-up" if summary["realized"] >= 0 else "zq-down"}">{_rp_short(summary["realized"], True)}</span>', f'<span class="zq-muted">{n_trades} trade tutup</span>'),
        _stat("Position slots", f'<span style="{col_of[lvl["slots"]]}">{summary["n_positions"]} / {s["max_positions"]}</span>', f'<span class="zq-muted">sisa {max(0, s["max_positions"] - summary["n_positions"])}</span>'),
    ]
    _html(_grid(cards, 6))
    dates = [v["date"] for v in snap["prices"].values()]
    if summary["positions"]:
        note = f"Harga penutupan terakhir per {pd.to_datetime(max(dates)).strftime('%d %b %Y')}, bukan real-time." if dates else "Harga belum tersedia, posisi dihitung di harga rata-rata."
        _html(source_note_html(note))
    if eq <= 0:
        st.error("Equity nol atau negatif. Cek setoran dan posisi di Settings.")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        _html(_panel("shield-check", "Risk check", "".join(_line(c["level"], _check_text(c)) for c in checks)))
    with c2:
        rows = (
            f'<div class="zq-row"><span>Semua SL kena</span><span class="zq-down">{_rp_short(scen["sl"], True)} ({_pct(scen["sl_pct"], 1, True)})</span></div>'
            f'<div class="zq-row"><span>Semua TP1 kena</span><span class="zq-up">{_rp_short(scen["tp1"], True)} ({_pct(scen["tp1_pct"], 1, True)})</span></div>'
            f'<div class="zq-row"><span>Semua TP2 kena</span><span class="zq-up">{_rp_short(scen["tp2"], True)} ({_pct(scen["tp2_pct"], 1, True)})</span></div>'
            f'<div class="zq-row"><span>Kapasitas trade baru</span><span>{scen["capacity"]} @ {_pct(s["risk_pct"])} risiko</span></div>'
            f'<div class="zq-row"><span>Sisa ruang risiko / cash bebas</span><span>{_rp_short(scen["risk_room"])} / {_rp_short(scen["cash_free"])}</span></div>'
        )
        _html(_panel("chart-arrows-vertical", "Skenario", rows))

    _html(_label("briefcase", "Positions"))
    if not summary["positions"]:
        _html('<div class="zq-card"><div class="zq-muted" style="font-size:13px;">Belum ada posisi. Tambahkan lewat Add position, atau hitung ukuran trade di tab Position sizer.</div></div>')
    for r in summary["positions"]:
        st.markdown(compact_html(_position_card(r, s)), unsafe_allow_html=True)
        _position_actions(r)
        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    _render_add_position(doc)
    _render_import_export(doc, summary)


# ---------------------------------------------------------------- POSITION SIZER
_ERR = {
    "equity_zero": "Isi modal awal dulu di tab Portfolio.",
    "need_entry_sl": "Isi harga entry dan stop loss.",
    "sl_above_entry": "Stop loss harus di bawah entry.",
    "tp1_below_entry": "TP1 harus di atas entry.",
    "tp2_below_tp1": "TP2 tidak boleh di bawah TP1.",
    "tp2_below_entry": "TP2 harus di atas entry.",
}
_BIND = {"risk": "risiko per trade", "alloc": "maks alokasi per saham", "cash": "cash minimum", "heat": "batas total risiko", "slots": "slot posisi sudah penuh"}


def _on_source():
    src = st.session_state.get("mm_src")
    if src and src != "Manual":
        st.session_state["mm_ticker"] = src


def _sync_plan():
    """Isi entry, SL, dan TP dari Trade Plan (Best Fit atau BOW/BOB pilihan)."""
    ticker = watchlist_store.normalize_ticker(st.session_state.get("mm_ticker"))
    if not ticker:
        st.session_state["mm_msg"] = ("error", "Isi kode saham dulu, mis. BBCA.")
        return
    try:
        planner = TradePlanner(ticker=ticker, period="6mo")
        planner.fetch_and_prepare_data(data=market_source.get_shared_history(ticker))
        plans = planner.generate_trade_plan()
        best = str(planner.get_direction().iloc[0]["Direction"])
        want = st.session_state.get("mm_strategy", "Best Fit")
        typ = best if want == "Best Fit" else want
        rows = plans[plans["Type"] == typ]
        row = (rows if not rows.empty else plans).iloc[0]
        st.session_state["mm_entry"] = M.round_to_tick(float(row["Entry Basis"]), "nearest")
        st.session_state["mm_sl"] = M.round_to_tick(float(row["Stop Loss"]), "down")
        st.session_state["mm_tp1"] = M.round_to_tick(float(row["TP 1"]), "down")
        st.session_state["mm_tp2"] = M.round_to_tick(float(row["TP 2"]), "down")
        st.session_state["mm_plan_type"] = str(row["Type"])
        st.session_state["mm_msg"] = ("success", f"Trade Plan {row['Type']} untuk {ticker.replace('.JK', '')} dimuat ({'Best Fit' if row['Type'] == best else 'pilihan sendiri'}).")
    except Exception as e:
        st.session_state["mm_msg"] = ("error", f"Trade Plan belum bisa dimuat: {e}")


def _render_sizer(doc, settings, summary):
    s = settings
    for k, v in (("mm_entry", 0), ("mm_sl", 0), ("mm_tp1", 0), ("mm_tp2", 0), ("mm_risk", s["risk_pct"]), ("mm_partial", s["partial_pct"]), ("mm_strategy", "Best Fit"), ("mm_ticker", "")):
        st.session_state.setdefault(k, v)
    wl = [t.replace(".JK", "") for t in watchlist_store.tickers()]
    col_in, col_out = st.columns([1.2, 1.8], gap="medium")

    with col_in:
        _html(_label("calculator", "New trade"))
        st.selectbox("Load from", ["Manual"] + wl, key="mm_src", on_change=_on_source,
                     format_func=lambda c: c if c == "Manual" else display_name(c))
        st.text_input("Ticker", key="mm_ticker", placeholder="BBCA", max_chars=8)
        _nm = get_company_name(st.session_state.get("mm_ticker") or "")
        if _nm:
            st.caption(_nm)
        st.radio("Plan", ["Best Fit", "BOW", "BOB"], key="mm_strategy", horizontal=True)
        st.button("Sync Trade Plan", key="mm_sync", on_click=_sync_plan, **_W["button"], **icon_kwargs("sync"))
        flash = st.session_state.pop("mm_msg", None)
        if flash:
            (st.success if flash[0] == "success" else st.error)(flash[1])
        a, b = st.columns(2)
        with a:
            st.number_input("Entry price", min_value=0, step=1, format="%d", key="mm_entry")
        with b:
            st.number_input("Stop loss", min_value=0, step=1, format="%d", key="mm_sl")
        c, d = st.columns(2)
        with c:
            st.number_input("Target 1", min_value=0, step=1, format="%d", key="mm_tp1")
        with d:
            st.number_input("Target 2", min_value=0, step=1, format="%d", key="mm_tp2")
        st.number_input("Risk per trade (% of equity)", min_value=0.1, max_value=5.0, step=0.25, format="%.2f", key="mm_risk")
        st.slider("Sell at TP1 (%)", min_value=10, max_value=90, step=5, key="mm_partial", help="Sisanya dijual di TP2. Kalau hanya satu target diisi, seluruh posisi dijual di target itu.")

    with col_out:
        if summary["equity"] <= 0:
            st.info("Isi modal awal dulu di tab Portfolio supaya ukuran posisi bisa dihitung.")
            return
        res = M.size_position(
            summary["equity"], summary["cash"], summary["open_risk"], summary["n_positions"],
            st.session_state["mm_entry"], st.session_state["mm_sl"], st.session_state["mm_tp1"], st.session_state["mm_tp2"],
            s, risk_pct=st.session_state["mm_risk"], partial_pct=st.session_state["mm_partial"],
        )
        if not res["valid"]:
            if st.session_state["mm_entry"] or st.session_state["mm_sl"]:
                _html(_panel("alert-triangle", "Periksa input", "".join(_line("warn", _ERR.get(e, e)) for e in res["errors"])))
            else:
                _html('<div class="zq-card"><div class="zq-muted" style="font-size:13px;">Isi entry dan stop loss (atau klik Sync Trade Plan) untuk melihat ukuran posisi.</div></div>')
            return
        if res["lots"] > 0:
            head = f'<div style="font-size:30px; font-weight:800; color:#FFFFFF;">{res["lots"]} lot</div><div class="zq-muted" style="font-size:12px;">{fmt_id(res["shares"])} lembar · {_rp_short(res["buy_value"])} ({_pct(res["alloc_pct"])} dari equity)</div>'
        else:
            head = '<div style="font-size:30px; font-weight:800; color:#FF007F;">0 lot</div><div class="zq-muted" style="font-size:12px;">Tidak ada ukuran yang lolos aturan risiko kamu.</div>'
        pills = "".join(pill(f"Dibatasi: {_BIND[k]}", "cyan" if k == "risk" else "amber") for k in res["binding"])
        if "risk" not in res["binding"] and res["lots"] >= 0:
            pills += pill(f"Berdasarkan risiko saja: {res['lots_by']['risk']} lot")
        rows = ""
        if res["lots"] > 0:
            rows += f'<div class="zq-row"><span>Rugi jika SL kena</span><span class="zq-down">-{_rp_short(res["risk_amount"])} ({_pct(res["risk_pct_equity"], 2)} · 1R)</span></div>'
            for name, label in (("tp1", "TP1"), ("tp2", "TP2")):
                if name in res["plan"]:
                    p = res["plan"][name]
                    rows += f'<div class="zq-row"><span>{label} · jual {p["lots"]} lot @ {fmt_id(p["price"])}</span><span class="zq-up">{_rp_short(p["profit"], True)} ({_rr(p["r"])})</span></div>'
            if len(res["plan"]) == 2:
                rows += f'<div class="zq-row"><span>Total jika kedua target tercapai</span><span class="zq-up">{_rp_short(res["total_profit"], True)} ({_rr(res["total_r"])})</span></div>'
            rows += f'<div class="zq-row"><span>Break-even (termasuk fee)</span><span>{fmt_id(res["breakeven"])}</span></div>'
            rows += f'<div class="zq-row"><span>Biaya beli (termasuk fee)</span><span>{_rp(res["cost"])}</span></div>'
        _html(f'<div class="zq-card zq-card-accent"><div class="zq-stat-label">Ukuran yang disarankan</div>{head}<div>{pills}</div><div style="margin-top:8px;">{rows}</div></div>')
        if res["rounded"]:
            names = {"entry": "entry", "sl": "SL", "tp1": "TP1", "tp2": "TP2"}
            st.caption("Harga dibulatkan ke fraksi BEI: " + ", ".join(f"{names[n]} {fmt_id(a)} ke {fmt_id(b)}" for n, a, b in res["rounded"]) + ".")
        _gap(4)
        _html(_panel("chart-arrows-vertical", "Dampak ke portofolio", "".join(_line(c["level"], _impact_text(c)) for c in res["impact"]["checks"])))

        ticker = watchlist_store.normalize_ticker(st.session_state["mm_ticker"])
        owned = st.checkbox("Already owned (count as deposit, don't deduct cash)", key="mm_sizer_owned")
        if st.button("Add to portfolio", key="mm_add_from_sizer", **_W["button"], disabled=(res["lots"] < 1 or not ticker), **icon_kwargs("add_circle")):
            plan = st.session_state.get("mm_plan_type") if st.session_state["mm_strategy"] == "Best Fit" else st.session_state["mm_strategy"]
            _done(ms.add_position(ticker, res["lots"], res["entry"], res["sl"], res["tp1"], res["tp2"], now_wib().date().isoformat(), "Dari position sizer", plan if plan in ("BOW", "BOB") else "", owned))
        if not ticker:
            st.caption("Isi kode saham untuk mengaktifkan tombol Add to portfolio.")
    with st.expander("How the size is calculated", expanded=False, **expander_kwargs("help")):
        st.markdown(
            "- **Risiko per trade**: kerugian jika SL kena (termasuk fee) tidak melebihi persentase yang kamu pilih dari equity.\n"
            "- **Alokasi**: nilai posisi tidak melebihi batas persen per saham.\n"
            "- **Cash**: cash setelah beli tetap di atas minimum.\n"
            "- **Risiko total**: jumlah risiko semua posisi tidak melebihi batas portofolio.\n"
            "- **Slot**: jumlah posisi tidak melebihi maksimum.\n\n"
            "Lot akhir adalah yang **terkecil** dari kelima batas itu (1 lot = 100 lembar). Harga entry dibulatkan ke fraksi BEI terdekat, SL dan target dibulatkan ke bawah."
        )


# ---------------------------------------------------------------- JOURNAL
def _style_fig(fig, height=260):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#161B22",
        font=dict(color="#C0C5D0", size=11), showlegend=False,
        xaxis=dict(gridcolor="#21262D", zeroline=False), yaxis=dict(gridcolor="#21262D", zeroline=False, tickformat=",d"),
    )
    return fig


def _render_journal(doc, settings, summary):
    stats = M.journal_stats(doc["journal"], doc["cashflows"])
    if stats["n"] == 0:
        _html('<div class="zq-card"><div style="color:#FFFFFF; font-weight:800;">Jurnal masih kosong</div><div class="zq-muted" style="font-size:12px; margin-top:4px;">Setiap kali kamu menjual posisi (tombol Sell di tab Portfolio), hasilnya tercatat di sini lengkap dengan statistik dan kurva equity.</div></div>')
        return
    pf = "∞" if stats["no_losses"] else (_dec(stats["profit_factor"], 2) if stats["profit_factor"] is not None else "-")
    exp_r = f"{_dec(stats['expectancy_r'], 2)}R per trade" if stats["expectancy_r"] is not None else "R belum tersedia"
    best, worst = stats["best"], stats["worst"]
    up = lambda v: "zq-up" if v >= 0 else "zq-down"
    cards = [
        _stat("Trades", str(stats["n"]), f'<span class="zq-muted">{stats["wins"]} menang · {stats["losses"]} kalah · {stats["even"]} impas</span>'),
        _stat("Win rate", _pct(stats["win_rate"], 0), f'<span class="zq-muted">payoff {_dec(stats["payoff"], 2) if stats["payoff"] else "-"}</span>'),
        _stat("Profit factor", pf, '<span class="zq-muted">total untung / total rugi</span>'),
        _stat("Expectancy", f'<span class="{up(stats["expectancy"])}">{_rp_short(stats["expectancy"], True)}</span>', f'<span class="zq-muted">{exp_r}</span>'),
        _stat("Total realized", f'<span class="{up(stats["total_pnl"])}">{_rp_short(stats["total_pnl"], True)}</span>', f'<span class="zq-muted">terbaik {best["ticker"].replace(".JK", "")} {_rp_short(best["pnl"], True)}</span>'),
        _stat("Avg win", f'<span class="zq-up">{_rp_short(stats["avg_win"] or 0)}</span>', f'<span class="zq-muted">rata-rata rugi <span class="zq-down">{_rp_short(stats["avg_loss"] or 0)}</span> · terburuk {worst["ticker"].replace(".JK", "")}</span>'),
        _stat("Max drawdown", f'<span class="zq-down">{_rp_short(stats["max_drawdown"])}</span>', f'<span class="zq-muted">{_pct(stats["max_drawdown_pct"])} dari setoran</span>'),
        _stat("Losing streak", str(stats["max_losing_streak"]), f'<span class="zq-muted">rata-rata tahan {_dec(stats["avg_hold_days"], 0) if stats["avg_hold_days"] is not None else "-"} hari</span>'),
    ]
    _html(_grid(cards, 4))

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    cA, cB = st.columns(2)
    with cA:
        _html(_label("chart-line", "Equity curve (realized)"))
        xs = [c["date"] for c in stats["curve"]]
        ys = [c["equity"] for c in stats["curve"]]
        fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=CYAN, width=2, shape="hv"), marker=dict(size=5, color=CYAN),
                                   fill="tozeroy", fillcolor="rgba(0,243,255,0.07)", hovertemplate="%{x}<br>Rp %{y:,.0f}<extra></extra>"))
        if len(ys) > 1:
            lo, hi = min(ys), max(ys)
            pad = (hi - lo) * 0.15 or hi * 0.02
            fig.update_yaxes(range=[lo - pad, hi + pad])
        st.plotly_chart(_style_fig(fig), **_W["plotly_chart"], config={"displayModeBar": False})
    with cB:
        _html(_label("chart-bar", "Monthly P/L"))
        months = list(stats["monthly"].keys())
        vals = [stats["monthly"][m] for m in months]
        fig2 = go.Figure(go.Bar(x=months, y=vals, marker_color=[GREEN if v >= 0 else PINK for v in vals], hovertemplate="%{x}<br>Rp %{y:,.0f}<extra></extra>"))
        fig2.update_xaxes(type="category")
        st.plotly_chart(_style_fig(fig2), **_W["plotly_chart"], config={"displayModeBar": False})

    _html(_label("list-numbers", "Closed trades"))
    trades = sorted(doc["journal"], key=lambda t: (t["closed"], t["id"]), reverse=True)
    f1, f2 = st.columns(2)
    with f1:
        tick_opts = ["All"] + sorted({t["ticker"].replace(".JK", "") for t in trades})
        ft = st.selectbox("Ticker", tick_opts, key="mm_j_ticker")
    with f2:
        fr = st.selectbox("Reason", ["All"] + list(ms.REASONS), key="mm_j_reason")
    view = [t for t in trades if (ft == "All" or t["ticker"].replace(".JK", "") == ft) and (fr == "All" or t["reason"] == fr)]
    df = pd.DataFrame([{
        "Closed": t["closed"], "Ticker": t["ticker"].replace(".JK", ""), "Lots": t["lots"], "Entry": fmt_id(t["entry"]), "Exit": fmt_id(t["exit"]),
        "P/L": _rp_short(t["pnl"], True), "P/L %": _pct(t["pnl_pct"], 1, True), "R": _rr(t["r"], "") if t["r"] is not None else "-", "Reason": t["reason"], "Note": t["note"],
    } for t in view])
    st.dataframe(df, hide_index=True, **_W["dataframe"])
    csv_df = pd.DataFrame([{**{k: (_csv_safe(v) if k == "note" else v) for k, v in t.items()}} for t in trades])
    st.download_button("Export journal CSV", csv_df.to_csv(index=False).encode("utf-8"), file_name="journal.csv", mime="text/csv", key="mm_dl_journal", **icon_kwargs("download", "download_button"))
    with st.expander("Manage journal", expanded=False, **expander_kwargs("tune")):
        st.caption("Menghapus catatan hanya menghapus baris jurnal (laba/rugi terealisasi ikut berubah). Posisi yang sudah terjual tidak dikembalikan.")
        labels = {t["id"]: f"{t['closed']} · {t['ticker'].replace('.JK', '')} · {t['lots']} lot · {_rp_short(t['pnl'], True)}" for t in trades}
        pick = st.selectbox("Entry", list(labels), format_func=lambda i: labels[i], key="mm_j_pick")
        sure = st.checkbox("Yes, delete this entry", key="mm_j_ok")
        if st.button("Delete entry", key="mm_j_del", disabled=not sure, **_W["button"]):
            _done(ms.delete_trade(pick))


# ---------------------------------------------------------------- SETTINGS
_FIELDS = [
    ("risk_pct", "Risk per trade (%)", 0.1, 5.0, 0.25, "%.2f", float),
    ("max_total_risk_pct", "Max total open risk (%)", 0.5, 30.0, 0.5, "%.1f", float),
    ("max_positions", "Max positions", 1, 30, 1, "%d", int),
    ("max_alloc_pct", "Max allocation per stock (%)", 1.0, 100.0, 1.0, "%.0f", float),
    ("min_cash_pct", "Minimum cash (%)", 0.0, 90.0, 1.0, "%.0f", float),
    ("fee_buy_pct", "Buy fee (%)", 0.0, 2.0, 0.01, "%.2f", float),
    ("fee_sell_pct", "Sell fee (%)", 0.0, 2.0, 0.01, "%.2f", float),
    ("partial_pct", "Sell at TP1 (%)", 10, 90, 5, "%d", int),
    ("near_sl_pct", "Near-SL warning (%)", 0.5, 10.0, 0.5, "%.1f", float),
]
_NOTE = {
    "risk_gt_cap": "Risiko per trade lebih besar dari batas total risiko, jadi tidak ada trade yang bisa dibuka.",
    "heat_before_slots": "Batas total risiko ({cap:.0f}%) tercapai sebelum semua slot terisi ({n} x {r:g}% = {x:g}%).",
    "cash_limits_slots": "Cash minimum ({cash:.0f}%) akan membatasi: {n} slot x {a:.0f}% tidak bisa terisi penuh sekaligus.",
}


def _apply_preset():
    name = st.session_state.get("mm_set_preset")
    if name in M.PRESETS:
        for k, v in M.PRESETS[name].items():
            st.session_state[f"mm_set_{k}"] = v


def _do_reset():
    """Callback tombol reset: dijalankan sebelum halaman dirender ulang, jadi kotak konfirmasi boleh dikosongkan."""
    st.session_state["mm_reset_word"] = ""
    ok, code, info = ms.reset_portfolio()
    st.toast(_msg(code, info) + (" (Belum tersimpan di cloud, cek Storage status.)" if info.get("saved") is False else ""))


def _render_settings(doc, settings, summary):
    sig = tuple(sorted((k, str(v)) for k, v in settings.items()))
    if st.session_state.get("_mm_set_sig") != sig:
        for k, *_ in _FIELDS:
            st.session_state[f"mm_set_{k}"] = settings[k]
        st.session_state["mm_set_preset"] = settings["preset"]
        st.session_state["_mm_set_sig"] = sig

    _html(_label("adjustments-horizontal", "Risk rules"))
    st.selectbox("Preset", list(M.PRESETS) + ["Custom"], key="mm_set_preset", on_change=_apply_preset)
    cur = st.session_state["mm_set_preset"]
    if cur in M.PRESET_DESC:
        st.caption(M.PRESET_DESC[cur])
    with st.form("mm_settings_form", border=False):
        cols = st.columns(3)
        for i, (k, label, lo, hi, step, fmt, cast) in enumerate(_FIELDS):
            with cols[i % 3]:
                st.number_input(label, min_value=cast(lo), max_value=cast(hi), step=cast(step), format=fmt, key=f"mm_set_{k}")
        go = st.form_submit_button("Save settings", **_W["form_submit_button"], **icon_kwargs("save"))
    if go:
        vals = {k: st.session_state[f"mm_set_{k}"] for k, *_ in _FIELDS}
        vals["preset"] = st.session_state["mm_set_preset"]
        ms.save_settings(vals)
        st.toast("Pengaturan disimpan.")
        st.rerun()
    lines = "".join(_line("info" if lvl == "info" else "warn", _NOTE[key].format(**args)) for lvl, key, args in M.settings_notes(settings))
    if lines:
        _html(_panel("info-circle", "Catatan", lines))
    with st.expander("What do these numbers mean?", expanded=False, **expander_kwargs("help")):
        st.markdown(
            "- **Risk per trade**: berapa persen equity yang siap hilang jika stop loss kena. Umumnya 0,5% sampai 2%.\n"
            "- **Max total open risk**: jumlah risiko semua posisi yang boleh terbuka bersamaan. Membatasi kerugian di hari buruk.\n"
            "- **Max positions**: jumlah saham yang boleh dipegang sekaligus.\n"
            "- **Max allocation per stock**: nilai satu saham tidak boleh melebihi persen ini dari equity.\n"
            "- **Minimum cash**: sisa cash yang selalu dijaga.\n"
            "- **Fee**: biaya broker beli dan jual (sudah termasuk pajak). Sesuaikan dengan brokermu.\n"
            "- **Sell at TP1**: porsi posisi yang dijual di target 1 pada rencana ambil untung.\n\n"
            "Angka preset hanya titik awal yang umum dipakai, bukan saran investasi. Pilih yang sesuai toleransi risikomu."
        )

    _html(_label("wallet", "Deposits & withdrawals"))
    with st.form("mm_cash_form", border=False):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            amt = st.number_input("Amount (Rp)", min_value=0, value=None, step=1_000_000, format="%d", placeholder="mis. 20000000")
        with c2:
            kind = st.radio("Type", ["Deposit", "Withdraw"], horizontal=True)
        with c3:
            when = st.date_input("Date", value=now_wib().date())
        note = st.text_input("Note", max_chars=80)
        go = st.form_submit_button("Save", **_W["form_submit_button"], **icon_kwargs("savings"))
    if go:
        if not amt:
            st.error(_MSG["bad_amount"])
        else:
            _done(ms.add_cashflow(amt if kind == "Deposit" else -amt, note, when.isoformat()))
    if doc["cashflows"]:
        rows = sorted(doc["cashflows"], key=lambda c: (c["date"], c["id"]), reverse=True)
        st.dataframe(pd.DataFrame([{"Date": c["date"], "Amount": _rp(c["amount"]), "Note": c["note"]} for c in rows]), hide_index=True, **_W["dataframe"])
        with st.expander("Remove an entry", expanded=False, **expander_kwargs("delete")):
            lab = {c["id"]: f"{c['date']} · {_rp_short(c['amount'], True)} · {c['note'] or '-'}" for c in rows}
            pick = st.selectbox("Entry", list(lab), format_func=lambda i: lab[i], key="mm_cf_pick")
            if st.button("Remove entry", key="mm_cf_del", **_W["button"]):
                _done(ms.remove_cashflow(pick))
    with st.expander("Danger zone", expanded=False, **expander_kwargs("warning")):
        st.caption("Menghapus semua posisi, jurnal, dan setoran. Pengaturan risiko tidak ikut terhapus. Tidak bisa dibatalkan.")
        word = st.text_input("Type RESET to confirm", key="mm_reset_word")
        st.button("Reset portfolio data", key="mm_reset", disabled=(word.strip() != "RESET"), on_click=_do_reset, **_W["button"])


# ---------------------------------------------------------------- HALAMAN
def _section_picker():
    if hasattr(st, "segmented_control"):
        kw = {} if "mm_section" in st.session_state else {"default": "Portfolio"}
        return st.segmented_control("Section", SECTIONS, key="mm_section", label_visibility="collapsed", **kw) or "Portfolio"
    return st.radio("Section", SECTIONS, horizontal=True, key="mm_section", label_visibility="collapsed")


def render_page_money_management():
    _html(
        f"""<div class="zq-hero">
<h1>{svg_icon("wallet", 24, "#00F3FF", 2, margin_right=8)}MONEY MANAGEMENT</h1>
<p>Atur ukuran posisi dan risiko seluruh portofolio, catat hasil trade, dan pantau statistiknya.</p>
</div>"""
    )
    render_profile_card()
    settings, doc = ms.load_settings(), ms.load_portfolio()
    snap = {"prices": {}, "source": ""}
    if doc["positions"]:
        with st.spinner("Loading prices..."):
            snap = _prices(tuple(p["ticker"] for p in doc["positions"]), _bucket())
    prices = {t: v["last"] for t, v in snap["prices"].items()}
    summary = M.portfolio_summary(doc["positions"], prices, settings, doc["cashflows"], doc["journal"])

    with keyed_container("mmpage_root"):
        section = _section_picker()
        if section == "Position sizer":
            _render_sizer(doc, settings, summary)
        elif section == "Journal":
            _render_journal(doc, settings, summary)
        elif section == "Settings":
            _render_settings(doc, settings, summary)
        else:
            _render_portfolio(doc, settings, summary, snap)
