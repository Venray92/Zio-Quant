"""Halaman Watchlist: kartu saham (harga, grafik mini, rencana terbaik), catatan dan target,
panel Live Trade Plan yang sama dengan tab screener. Data disimpan per profil (utils/storage.py)."""
import pandas as pd
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.market_data import candle_is_final, now_wib
from engines.trade_planner import TradePlanner
from utils.compat import STRETCH
from utils import market_source, watchlist_store
from utils.card_html import (
    GREEN,
    PINK,
    build_card,
    compact_html,
    direction_badge,
    fmt_id,
    info_row,
    pill,
    source_note_html,
    strip_emoji,
)
from utils.icons import expander_kwargs, icon_kwargs, svg_icon
from utils.pages import keyed_container
from utils.profile import render_profile_card
from utils.ui_helpers import render_inline_trade_planner

_GRADE_KIND = {"strong": "green", "good": "cyan", "fair": "amber", "weak": "red"}
_FILTERS = ["All", "Gainers", "Losers", "In Buy Zone"]
_SORTS = ["Added (default)", "Gainers", "Losers", "Score", "Price high", "Price low", "A-Z"]


# ---------------------------------------------------------------- data
def _plan_summary(ticker, df):
    """Rencana terbaik (Best Fit) untuk satu saham, atau None kalau data tidak cukup."""
    try:
        planner = TradePlanner(ticker=ticker, period="6mo")
        planner.fetch_and_prepare_data(data=df)
        plans = planner.generate_trade_plan()
        best = str(planner.get_direction().iloc[0]["Direction"])
        rows = plans[plans["Type"] == best]
        row = (rows if not rows.empty else plans).iloc[0]
        return {
            "type": str(row["Type"]),
            "grade": strip_emoji(str(row["Grade"])).replace(" Setup", ""),
            "score": int(row["Score"]),
            "zone": str(row["Posisi Harga"]),
            "buy_min": float(row["Range Buy Min"]),
            "buy_max": float(row["Range Buy Max"]),
            "sl": float(row["Stop Loss"]),
            "tp1": float(row["TP 1"]),
            "rr": float(row["RR_Val"]) if pd.notna(row["RR_Val"]) else 0.0,
        }
    except Exception:
        return None


def _bucket():
    n = now_wib()
    return n.strftime("%Y%m%d%H") + str(n.minute // 5)


@st.cache_data(ttl=300, show_spinner=False)
def _snapshots(tickers, bucket):
    """Harga, % ubah, grafik 30 hari, dan rencana terbaik untuk tiap saham. Satu kali unduh untuk semua."""
    frames, source = market_source.get_histories(list(tickers))
    now = now_wib()
    out = {}
    for t in tickers:
        snap = None
        try:
            df = frames.get(t)
            if df is not None and len(df) >= 2:
                closes = pd.to_numeric(df["Close"], errors="coerce").dropna()
                last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
                date = pd.to_datetime(df["Date"]).iloc[-1]
                snap = {
                    "last": last,
                    "chg": (last - prev) / prev * 100 if prev > 0 else 0.0,
                    "spark": [float(x) for x in closes.tail(30)],
                    "date": date.strftime("%Y-%m-%d"),
                    "final": candle_is_final(date.date(), now),
                    "plan": _plan_summary(t, df),
                }
        except Exception:
            snap = None
        out[t] = snap
    return {"items": out, "source": source}


# ---------------------------------------------------------------- tampilan
def sparkline(values, color, w=160, h=24):
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    pts = " ".join(
        f"{i * w / (len(values) - 1):.1f},{h - 2 - (v - lo) / span * (h - 4):.1f}" for i, v in enumerate(values)
    )
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="width:100%; height:{h}px; margin-top:4px;" '
        f'aria-hidden="true"><polyline fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" points="{pts}"/></svg>'
    )


def _short_date(value):
    try:
        return pd.to_datetime(value).strftime("%d %b")
    except Exception:
        return ""


def _card_html(item, snap, is_selected):
    code = item["Ticker"].replace(".JK", "")
    plan = snap["plan"] if snap else None
    badges = ""
    if plan:
        kind = _GRADE_KIND.get(plan["grade"].split()[0].lower(), "neutral") if plan["grade"] else "neutral"
        badges = direction_badge(f"{plan['grade']} {plan['score']}", kind)

    rows = ""
    if snap:
        rows += sparkline(snap["spark"], GREEN if snap["chg"] >= 0 else PINK)
    if plan:
        rows += info_row(f"{plan['type']} · Best Fit", "target")
        rows += info_row(f"Buy {fmt_id(plan['buy_min'])}-{fmt_id(plan['buy_max'])} · SL {fmt_id(plan['sl'])} · TP1 {fmt_id(plan['tp1'])}")
    elif not snap:
        rows += info_row("Data belum tersedia untuk saham ini", "alert-triangle", "#E3B341")
    target = item.get("Target Price") or 0
    if target and snap and snap["last"] > 0:
        rows += info_row(f"Target Rp {fmt_id(target)} ({(target - snap['last']) / snap['last'] * 100:+.1f}%)", "flag")

    pills = ""
    if plan:
        z = plan["zone"]
        pills += pill(z, "green" if z == "In Buy Zone" else ("cyan" if z == "Near Zone" else "amber"))
        if plan["rr"] > 0:
            pills += pill(f"R:R 1 : {plan['rr']:.1f}")
    if snap and not snap["final"]:
        pills += pill("Candle belum final", "amber")
    if item.get("Notes"):
        pills += pill(item["Notes"])
    if item.get("Added"):
        d = _short_date(item["Added"])
        if d:
            pills += pill(f"Added {d}")

    return build_card(
        is_selected,
        code,
        badges,
        snap["last"] if snap else None,
        snap["chg"] if snap else None,
        rows,
        pills,
    )


def _csv_safe(v):
    s = str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


def _apply_filter_sort(items, snaps, flt, sort):
    def snap(x):
        return snaps.get(x["Ticker"])

    def zone(x):
        s = snap(x)
        return s["plan"]["zone"] if s and s["plan"] else ""

    view = list(items)
    if flt == "Gainers":
        view = [x for x in view if snap(x) and snap(x)["chg"] > 0]
    elif flt == "Losers":
        view = [x for x in view if snap(x) and snap(x)["chg"] < 0]
    elif flt == "In Buy Zone":
        view = [x for x in view if zone(x) == "In Buy Zone"]

    def num(x, field):
        s = snap(x)
        return s[field] if s else None

    def score(x):
        s = snap(x)
        return s["plan"]["score"] if s and s["plan"] else None

    keys = {
        "Gainers": (lambda x: num(x, "chg"), True),
        "Losers": (lambda x: num(x, "chg"), False),
        "Score": (score, True),
        "Price high": (lambda x: num(x, "last"), True),
        "Price low": (lambda x: num(x, "last"), False),
    }
    if sort in keys:
        fn, rev = keys[sort]
        have = [x for x in view if fn(x) is not None]
        missing = [x for x in view if fn(x) is None]
        view = sorted(have, key=fn, reverse=rev) + missing
    elif sort == "A-Z":
        view = sorted(view, key=lambda x: x["Ticker"])
    return view


def _toast_add(res):
    if res["added"]:
        st.toast(f"{res['added']} saham ditambahkan ke Watchlist.")
    if res["exists"] and not res["added"]:
        st.toast("Saham sudah ada di Watchlist.")
    if res["limit"]:
        st.toast(f"Watchlist penuh (maks {watchlist_store.MAX_ITEMS} saham). Hapus satu dulu.")
    if res["invalid"]:
        st.toast("Kode tidak valid: " + ", ".join(res["invalid"]))


def _render_add_form(items):
    have = {x["Ticker"] for x in items}
    options = [t.replace(".JK", "") for t in get_all_ihsg_tickers() if t not in have]
    with st.expander("Add stocks", expanded=not items, **expander_kwargs("add")):
        with st.form("wl_add_form", clear_on_submit=True, border=False):
            if options:
                picks = st.multiselect("Stocks", options, placeholder="Type a ticker, e.g. BBCA", key="wl_add_pick")
            else:
                raw = st.text_input("Tickers (pisahkan dengan koma)", placeholder="BBCA, BBRI", key="wl_add_text")
                picks = [p for p in raw.replace(";", ",").split(",") if p.strip()]
            go = st.form_submit_button("Add to watchlist", **STRETCH, **icon_kwargs("bookmark_add"))
        if go:
            _toast_add(watchlist_store.add_tickers(picks, "Manual"))
            st.rerun()
        st.caption(f"{len(items)} / {watchlist_store.MAX_ITEMS} stocks")


def render_page_watchlist():
    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("bookmarks", 24, "#00F3FF", 2, margin_right=8)}WATCHLIST</h1>
<p>Pantau saham pilihanmu: harga, rencana terbaik, dan target dalam satu tempat.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )
    items = watchlist_store.load_watchlist()  # dimuat dulu supaya status penyimpanan di kartu profil akurat
    render_profile_card()
    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    snaps, source = {}, ""
    if items:
        with st.spinner("Loading prices..."):
            data = _snapshots(tuple(x["Ticker"] for x in items), _bucket())
        snaps, source = data["items"], data["source"]

    # ================= KIRI: daftar =================
    with col_left:
        _render_add_form(items)

        if not items:
            st.markdown(
                compact_html(
                    f"""<div class="zq-card" style="margin-top:8px;">
<div style="color:#FFFFFF; font-weight:800; font-size:14px;">{svg_icon("bookmarks", 16, "#00F3FF", 2, margin_right=6)}Your watchlist is empty</div>
<div class="zq-muted" style="font-size:12px; margin-top:4px;">Tambah saham di atas, atau klik Add to Watchlist di panel Trade Plan pada halaman screener.</div>
</div>"""
                ),
                unsafe_allow_html=True,
            )
        else:
            n_up = sum(1 for s in snaps.values() if s and s["chg"] > 0)
            n_down = sum(1 for s in snaps.values() if s and s["chg"] < 0)
            n_zone = sum(1 for s in snaps.values() if s and s["plan"] and s["plan"]["zone"] == "In Buy Zone")
            st.markdown(
                compact_html(
                    f'<div style="margin:4px 0 6px 0;">{pill(f"{len(items)} stocks")}{pill(f"{n_up} up", "green")}'
                    f'{pill(f"{n_down} down", "red")}{pill(f"{n_zone} in buy zone", "cyan")}</div>'
                ),
                unsafe_allow_html=True,
            )
            with keyed_container("wlrow_filters"):
                f1, f2 = st.columns(2)
                with f1:
                    flt = st.selectbox("Filter", _FILTERS, key="wl_filter", label_visibility="collapsed")
                with f2:
                    sort = st.selectbox("Sort", _SORTS, key="wl_sort", label_visibility="collapsed")

            with keyed_container("wlrow_tools"):
                b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Refresh", key="wl_refresh", **STRETCH, **icon_kwargs("refresh")):
                    _snapshots.clear()
                    st.rerun()
            with b2:
                with st.popover("Manage", **STRETCH, **icon_kwargs("tune", "popover")):
                    st.caption("Remove every stock from this watchlist.")
                    sure = st.checkbox("Yes, remove all", key="wl_confirm_clear")
                    if st.button("Clear watchlist", key="wl_clear_all", disabled=not sure, **STRETCH):
                        watchlist_store.clear_all()
                        st.session_state["selected_watchlist_ticker"] = None
                        st.toast("Watchlist dikosongkan.")
                        st.rerun()
            with b3:
                df = pd.DataFrame(
                    [
                        {
                            "Ticker": x["Ticker"].replace(".JK", ""),
                            "Last": (snaps.get(x["Ticker"]) or {}).get("last", ""),
                            "Change %": round((snaps.get(x["Ticker"]) or {}).get("chg", 0), 2) if snaps.get(x["Ticker"]) else "",
                            "Notes": _csv_safe(x["Notes"]),
                            "Target": x["Target Price"] or "",
                            "Added": x["Added"],
                        }
                        for x in items
                    ]
                )
                st.download_button(
                    "CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="watchlist.csv",
                    mime="text/csv",
                    **STRETCH,
                    help="Export watchlist to CSV",
                    **icon_kwargs("download", "download_button"),
                )

            st.markdown(source_note_html(source), unsafe_allow_html=True)

            view = _apply_filter_sort(items, snaps, flt, sort)
            valid = {x["Ticker"] for x in items}
            if st.session_state.get("selected_watchlist_ticker") not in valid:
                st.session_state["selected_watchlist_ticker"] = view[0]["Ticker"] if view else items[0]["Ticker"]

            if not view:
                st.info(f"Tidak ada saham untuk filter {flt}.")
            with st.container(height=700, border=False):
                for x in view:
                    t = x["Ticker"]
                    code = t.replace(".JK", "")
                    is_sel = st.session_state.get("selected_watchlist_ticker") == t
                    st.markdown(_card_html(x, snaps.get(t), is_sel), unsafe_allow_html=True)
                    with keyed_container(f"wlrow_card_{code}"):
                        c_sel, c_del = st.columns([3, 2])
                    with c_sel:
                        if st.button(
                            f"SELECTED ({code})" if is_sel else f"SELECT {code}",
                            key=f"wl_sel_{code}",
                            **STRETCH,
                            type="primary" if is_sel else "secondary",
                            **(icon_kwargs("check") if is_sel else {}),
                        ):
                            st.session_state["selected_watchlist_ticker"] = t
                            st.rerun()
                    with c_del:
                        if st.button("Remove", key=f"wl_del_{code}", **STRETCH, **icon_kwargs("delete")):
                            watchlist_store.remove_tickers([t])
                            if st.session_state.get("selected_watchlist_ticker") == t:
                                st.session_state["selected_watchlist_ticker"] = None
                            st.toast(f"{code} dihapus dari Watchlist.")
                            st.rerun()
                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # ================= KANAN: panel saham terpilih =================
    with col_right:
        sel = st.session_state.get("selected_watchlist_ticker")
        item = next((x for x in items if x["Ticker"] == sel), None) if items else None
        if not item:
            st.info("Pilih satu saham dari daftar untuk melihat Live Trade Plan-nya.")
            return
        code = sel.replace(".JK", "")
        st.markdown(
            compact_html(
                f"""<div style="background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); border: 1.5px solid #00F3FF; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);">
<span>{svg_icon("target", 18, "#00F3FF", 2, margin_right=6)}SELECTED SYMBOL: <strong style="color: #00F3FF; font-size: 15px; margin-left: 6px;">{sel}</strong></span>
<span style="color: #8B949E; font-size: 11px; font-weight: 500;">Interactive Analysis Workspace</span>
</div>"""
            ),
            unsafe_allow_html=True,
        )

        with st.expander("Notes & target", expanded=False, **expander_kwargs("edit_note")):
            with st.form(f"wl_edit_{code}", border=False):
                notes = st.text_input("Notes", value=item["Notes"], max_chars=80)
                target = st.number_input(
                    "Target price (Rp)", min_value=0.0, value=float(item["Target Price"]), step=1.0, format="%.0f"
                )
                saved = st.form_submit_button("Save", **STRETCH, **icon_kwargs("save"))
            if saved:
                watchlist_store.update_item(sel, notes=notes, target=float(target))
                st.toast(f"Catatan {code} disimpan.")
                st.rerun()

        try:
            render_inline_trade_planner(sel, key_suffix="wl", screener_name="Watchlist", show_watchlist_button=False)
        except Exception as e:
            st.error(f"Failed to load Trade Plan for {sel}: {e}")
