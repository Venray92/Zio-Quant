"""Footer tetap di kiri-bawah: IHSG (delayed, dari Yahoo) + jam WIB real-time + status pasar."""
import inspect

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from engines.market_data import calendar_is_covered, is_trading_day, now_wib


def fmt_id_num(value, decimals=2):
    """7842.15 -> '7.842,15' (format Indonesia)."""
    return f"{value:,.{decimals}f}".replace(",", "#").replace(".", ",").replace("#", ".")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ihsg():
    """Harga IHSG (^JKSE). Satu ambilan per menit dipakai semua pengunjung. None kalau gagal.

    Kadang panggilan LANGSUNG ke Yahoo baliknya ketinggalan (bar harian terakhirnya lebih lawas dari
    yang seharusnya -- pernah dilaporkan user: jam 08:24 pagi tanggal 24, masih nunjuk 21 Sep, padahal
    seharusnya paling telat 23 Sep/kemarin). File harian kita sendiri (`ihsg_history.csv`, dari job
    tiap sore) biasanya lebih baru krn itu hasil `yf.download` batch, bukan `Ticker().history()` yang
    dipanggil di sini. Jadi kalau hasil Yahoo langsung ternyata LEBIH LAWAS dari file kita, pakai
    punya file -- bukan sebaliknya (biar tetap dapat harga paling baru kalau memang live-nya OK).
    """
    live = _fetch_ihsg_live()
    from_file = _fetch_ihsg_from_file()
    if live and from_file:
        return from_file if from_file["_date_obj"] > live["_date_obj"] else live
    return live or from_file


def _fetch_ihsg_live():
    try:
        import yfinance as yf

        t = yf.Ticker("^JKSE")
        hist = t.history(period="5d", interval="1d")
        if hist is None or hist.empty:
            return None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
        date_obj = pd.Timestamp(hist.index[-1]).tz_localize(None).normalize()
        try:
            fi = t.fast_info
            lp, pc = float(fi.last_price), float(fi.previous_close)
            if lp > 0 and pc > 0:
                last, prev = lp, pc
        except Exception:
            pass
        return {
            "last": last,
            "chg": ((last - prev) / prev * 100) if prev else 0.0,
            "date": date_obj.strftime("%d %b"),
            "fetched": now_wib().strftime("%H:%M"),
            "_date_obj": date_obj,
        }
    except Exception:
        return None


def _fetch_ihsg_from_file():
    try:
        from utils.market_source import load_ihsg

        d = load_ihsg()
        if d is None or len(d) == 0:
            return None
        d = d.sort_values("Date")
        last = float(d["Close"].iloc[-1])
        prev = float(d["Close"].iloc[-2]) if len(d) > 1 else last
        date_obj = pd.Timestamp(d["Date"].iloc[-1]).normalize()
        return {
            "last": last,
            "chg": ((last - prev) / prev * 100) if prev else 0.0,
            "date": date_obj.strftime("%d %b"),
            "fetched": now_wib().strftime("%H:%M"),
            "_date_obj": date_obj,
        }
    except Exception:
        return None


def _footer_html():
    q = fetch_ihsg()
    today = now_wib().date()
    trading = is_trading_day(today) if calendar_is_covered(today) else today.weekday() < 5
    if q:
        cls = "zq-up" if q["chg"] >= 0 else "zq-down"
        idx = (
            f'<span class="zq-f-idx">{fmt_id_num(q["last"])}</span> '
            f'<span class="{cls}">{"+" if q["chg"] >= 0 else ""}{fmt_id_num(q["chg"])}%</span>'
        )
        note = f'<span class="zq-f-note">Delayed · {q["date"]}</span>'
    else:
        idx = '<span class="zq-muted">tidak tersedia</span>'
        note = ""
    # Sumber data (tersembunyi). Script jam menyalin isinya ke bar footer yang ditempel
    # langsung di <body>, supaya posisinya tidak terpengaruh kontainer Streamlit.
    return (
        f'<div id="zq-footer-src" data-trading="{1 if trading else 0}" style="display:none;">'
        f'<span class="zq-muted">IHSG</span> {idx} {note}'
        "</div>"
    )


# Status pasar: jam sesi BEI (perkiraan). Senin-Kamis 09:00-12:00 & 13:30-16:00,
# Jumat 09:00-11:30 & 14:00-16:00 (pre-closing dihitung Open).
_CLOCK_JS = """
(function () {
  var W = %(win)s, D = %(doc)s;
  function status(mins, dow, trading) {
    if (!trading || dow === 0 || dow === 6) return ["Closed", ""];
    var fri = dow === 5;
    var s1End = fri ? 690 : 720, s2Start = fri ? 840 : 810;
    if (mins >= 540 && mins < s1End) return ["Open", "open"];
    if (mins >= s1End && mins < s2Start) return ["Break", "break"];
    if (mins >= s2Start && mins < 960) return ["Open", "open"];
    return ["Closed", ""];
  }
  W.__zqStatus = status;
  if (W.__zqClock) return;
  W.__zqClock = true;
  function bar() {
    var b = D.getElementById("zq-footer-live");
    if (!b) {
      b = D.createElement("div");
      b.id = "zq-footer-live";
      b.className = "zq-footer";
      [["zq-f-data", ""], ["", "zq-f-sep"], ["zq-mkt", "zq-mkt"], ["zq-clock", ""]].forEach(function (a) {
        var sp = D.createElement("span");
        if (a[0]) sp.id = a[0];
        if (a[1]) sp.className = a[1];
        b.appendChild(sp);
      });
      D.body.appendChild(b);
    }
    return b;
  }
  var fmt = new Intl.DateTimeFormat("en-GB", {timeZone: "Asia/Jakarta", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, weekday: "short"});
  var DOW = {Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6};
  function tick() {
    var parts = {};
    fmt.formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
    var hh = parts.hour === "24" ? "00" : parts.hour;
    var src = D.getElementById("zq-footer-src");
    if (!src) return;
    bar();
    var data = D.getElementById("zq-f-data");
    if (data && data.innerHTML !== src.innerHTML) data.innerHTML = src.innerHTML;
    var el = D.getElementById("zq-clock");
    if (el) el.textContent = hh + ":" + parts.minute + ":" + parts.second + " WIB";
    var mk = D.getElementById("zq-mkt");
    if (mk) {
      var st = status(parseInt(hh, 10) * 60 + parseInt(parts.minute, 10), DOW[parts.weekday], src.getAttribute("data-trading") === "1");
      mk.textContent = st[0];
      mk.className = "zq-mkt" + (st[1] ? " zq-mkt-" + st[1] : "");
    }
  }
  tick();
  W.setInterval(tick, 1000);
})();
"""


def _inject_clock():
    try:
        supports_js = "unsafe_allow_javascript" in inspect.signature(st.html).parameters
    except Exception:
        supports_js = False
    if supports_js:
        st.html(
            '<span id="zq-clock-js" style="display:none"></span><script>'
            + _CLOCK_JS % {"win": "window", "doc": "document"}
            + "</script>",
            unsafe_allow_javascript=True,
        )
    else:  # Streamlit lama: jalankan dari iframe kecil, akses halaman induk
        components.html(
            "<script>" + _CLOCK_JS % {"win": "window.parent", "doc": "window.parent.document"} + "</script>",
            height=0,
        )


def _render_bar():
    st.markdown(_footer_html(), unsafe_allow_html=True)


if hasattr(st, "fragment"):
    _render_bar = st.fragment(run_every=60)(_render_bar)


def render_footer():
    _render_bar()
    _inject_clock()
