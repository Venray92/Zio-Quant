"""Potongan HTML bersama untuk kartu hasil screener (RSI dan Stoch), supaya tampilannya seragam."""
import re
from html import escape

from utils.icons import svg_icon

CYAN, PINK, GREEN, AMBER, GRAY = "#00F3FF", "#FF007F", "#00FF66", "#E3B341", "#8B949E"

_PILL_STYLES = {
    "neutral": ("#30363D", "#C9D1D9"),
    "cyan": (CYAN, CYAN),
    "amber": (AMBER, AMBER),
    "red": (PINK, PINK),
    "green": (GREEN, GREEN),
}


def compact_html(html):
    """Buang indentasi dan baris kosong. Di Markdown, baris kosong mengakhiri blok HTML dan
    baris berikutnya yang menjorok 4 spasi berubah jadi blok kode (HTML tampil mentah)."""
    return "\n".join(line.strip() for line in str(html).splitlines() if line.strip())


def fmt_id(n):
    """Angka ribuan gaya Indonesia: 9450 -> 9.450"""
    try:
        return f"{float(n):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"


def pill(text, kind="neutral"):
    border, color = _PILL_STYLES.get(kind, _PILL_STYLES["neutral"])
    return (
        f'<span style="display:inline-block; font-size:10px; padding:1px 7px; border-radius:4px; '
        f'border:1px solid {border}; color:{color}; margin:5px 4px 0 0; white-space:nowrap;">{escape(str(text))}</span>'
    )


def score_badge(score):
    return (
        '<span style="display:inline-flex; align-items:center; gap:3px; background-color:rgba(255,0,127,0.2); '
        f'border:1px solid {PINK}; color:{PINK}; font-size:10px; padding:1px 6px; border-radius:4px; font-weight:700;">'
        f'{svg_icon("star", 11, PINK, 2)}{escape(str(score))}</span>'
    )


def direction_badge(text, kind="red"):
    border, color = _PILL_STYLES.get(kind, _PILL_STYLES["red"])
    return (
        f'<span style="border:1px solid {border}; color:{color}; font-size:10px; padding:1px 6px; '
        f'border-radius:4px; font-weight:700;">{escape(str(text))}</span>'
    )


def change_html(pct):
    up = pct >= 0
    color = GREEN if up else PINK
    icon = svg_icon("trending-up" if up else "trending-down", 13, color, 2)
    return (
        f'<div style="font-size:11px; font-weight:700; color:{color}; white-space:nowrap;">'
        f'{icon} {pct:+.2f}%</div>'
    )


def info_row(html, icon=None, color=GRAY):
    ic = svg_icon(icon, 12, color, 1.8, margin_right=4) if icon else ""
    return f'<div style="font-size:11px; color:{color}; margin-top:2px;">{ic}{html}</div>'


def build_card(is_selected, symbol, badges_html, price, change_pct, rows_html="", pills_html=""):
    border_style = (
        "border: 1.5px solid #00F3FF; background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); box-shadow: 0 0 12px rgba(0, 243, 255, 0.3);"
        if is_selected
        else "border: 1px solid #30363D; background-color: #161B22;"
    )
    return (
        f'<div style="{border_style} border-radius:8px; padding:10px 12px; margin-bottom:4px;">'
        '<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">'
        '<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap; min-width:0;">'
        f'<span style="font-size:15px; font-weight:800; color:#FFFFFF;">{escape(str(symbol))}</span>{badges_html}</div>'
        '<div style="text-align:right; flex-shrink:0;">'
        f'<div style="font-size:15px; font-weight:800; color:#FFFFFF; white-space:nowrap;">Rp {fmt_id(price)}</div>'
        f'{change_html(change_pct)}</div></div>'
        f'{rows_html}<div>{pills_html}</div></div>'
    )


def section_label(icon, text):
    return f'<div class="cyber-section-label">{svg_icon(icon, 13, "#FF007F", 2)}{escape(text)}</div>'


def source_note_html(text):
    if not text:
        return ""
    return (
        f'<div style="font-size:11px; color:{GRAY}; margin:2px 0 8px 0;">'
        f'{svg_icon("database", 12, GRAY, 1.8, margin_right=4)}{escape(text)}</div>'
    )


# ---------- emoji dari engine -> ikon (hanya untuk tampilan HTML) ----------
_DOT = '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:{c}; margin-right:5px;"></span>'
_EMOJI_HTML = {
    "⚠️": svg_icon("alert-triangle", 14, "currentColor", 2, margin_right=3),
    "⚠": svg_icon("alert-triangle", 14, "currentColor", 2, margin_right=3),
    "ℹ️": svg_icon("info-circle", 14, "currentColor", 2, margin_right=3),
    "✅": svg_icon("circle-check", 14, "currentColor", 2, margin_right=3),
    "🚫": svg_icon("circle-x", 14, "currentColor", 2, margin_right=3),
    "🟢": _DOT.format(c="#34d399"),
    "🟡": _DOT.format(c="#fbbf24"),
    "🔴": _DOT.format(c="#ef4444"),
}
_EMOJI_RE = re.compile("|".join(re.escape(k) for k in sorted(_EMOJI_HTML, key=len, reverse=True)))
_ANY_EMOJI = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]\u200d?")


def emoji_to_icons(text):
    """Teks biasa -> HTML aman (di-escape), emoji dari engine diganti ikon/titik warna."""
    return _EMOJI_RE.sub(lambda m: _EMOJI_HTML[m.group(0)], escape(str(text)))


def strip_emoji(text):
    """Untuk teks Copy ke clipboard: buang emoji, rapikan spasi."""
    return re.sub(r"\s{2,}", " ", _ANY_EMOJI.sub("", str(text))).strip()
