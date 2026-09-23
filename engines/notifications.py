"""Susun daftar notifikasi lonceng dari data yang sudah dimuat (watchlist, portofolio, sinyal,
sektor, alert harga). Murni (tanpa Streamlit), memakai keluaran views.home_today.build_today()
supaya tidak menghitung ulang logic yang sama."""


def sectors_newly_hot(sector_today, sector_prev):
    """{sektor: True/False} hari ini vs hari sebelumnya -> daftar sektor yang BARU menyala
    (kemarin belum/tidak diketahui, sekarang iya)."""
    sector_today = sector_today or {}
    sector_prev = sector_prev or {}
    return sorted(s for s, v in sector_today.items() if v and not sector_prev.get(s))


def build_notifications(today, text_fn=None, sector_today=None, sector_prev=None, fired_alerts=None):
    """today: keluaran home_today.build_today(). text_fn: fungsi format teks utk item risk_checks
    (mis. views.money_management._check_text), sama yang dipakai blok 'Untuk kamu hari ini'.
    Return list item {"icon","text","level","page_key"}."""
    text_fn = text_fn or (lambda c: c["key"])
    items = []
    for row in (today or {}).get("zone_in", []):
        items.append({"icon": "bookmarks", "level": "good", "page_key": "watchlist",
                      "text": f"{row['t']} masuk zona beli ({row['buy_min']:,.0f} - {row['buy_max']:,.0f})".replace(",", ".")})
    for c in (today or {}).get("alerts", []):
        if c["key"] in ("sl_hit", "tp_hit", "no_sl"):
            items.append({"icon": "wallet", "level": "fail" if c["key"] == "sl_hit" else ("good" if c["key"] == "tp_hit" else "warn"),
                          "page_key": "money_management", "text": text_fn(c)})
    for s in (today or {}).get("signals", []):
        items.append({"icon": "radar-2", "level": "good" if s["d"] == "Bullish" else "warn", "page_key": None,
                      "text": f"{s['t']} sinyal {s['d']} di {s['screener']}"})
    for sec in sectors_newly_hot(sector_today, sector_prev):
        items.append({"icon": "radar-2", "level": "good", "page_key": "sector_radar", "text": f"Sektor {sec} baru menyala"})
    for a in fired_alerts or []:
        arrow = "naik ke / lewat" if a["Direction"] == "above" else "turun ke / lewat"
        items.append({"icon": "notifications", "level": "info", "page_key": None,
                      "text": f"{a['Ticker'].replace('.JK', '')} {arrow} Rp {a['Price']:,.0f}".replace(",", ".")})
    return items
