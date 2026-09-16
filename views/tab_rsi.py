if not df_target.empty:
                for idx, row in df_target.iterrows():
                    ticker = row.get("Ticker", row.get("Saham"))
                    saham = row.get("Saham", ticker.replace(".JK", ""))
                    score = row.get("Score", 0)
                    pattern_raw = row.get("Pattern", "-")
                    pattern_short = shorten_pattern(pattern_raw)
                    
                    close_price = row.get("Close_Price", 0)
                    change_pct = row.get("Change_Pct", 0.0)

                    tgl_kiri = str(row.get("Tgl Kiri", "-"))
                    tgl_kanan = str(row.get("Tgl Kanan", "-"))

                    is_selected = (st.session_state.get("selected_rsi_ticker") == ticker)

                    change_color = "#00E676" if change_pct >= 0 else "#FF5252"
                    change_icon = "📈" if change_pct >= 0 else "📉"
                    change_str = f"{change_icon} {change_pct:+.2f}%"
                    price_str = f"{close_price:,.0f}".replace(",", ".")

                    # Styling border jika dipilih
                    border_style = "border: 1.5px solid #00E676; background-color: #0D2B1D;" if is_selected else "border: 1px solid #30363D; background-color: #161B22;"

                    # Bikin Container Kartu Utuh
                    with st.container():
                        st.markdown(f"""
                        <div style="{border_style} border-radius: 8px; padding: 10px 12px; margin-bottom: 4px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                                        <span style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                        <span style="background-color: #21262D; border: 1px solid #30363D; color: #E6BDFB; font-size: 10px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">⭐ {score}</span>
                                    </div>
                                    <div style="font-size: 11px; color: #8B949E; margin-bottom: 2px;">📌 {pattern_short}</div>
                                    <div style="font-size: 10px; color: #6E7681;">🗓️ {tgl_kiri} ➔ {tgl_kanan}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 16px; font-weight: 700; color: #FFFFFF; margin-bottom: 2px;">{price_str}</div>
                                    <div style="font-size: 11px; font-weight: 600; color: {change_color};">{change_str}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Tombol Pilih yang Terintegrasi di Bawah Kartu
                        btn_label = f"✓ Selected ({saham})" if is_selected else f"Select {saham}"
                        btn_type = "primary" if is_selected else "secondary"
                        
                        if st.button(btn_label, key=f"select_btn_{ticker}_{idx}", use_container_width=True, type=btn_type):
                            st.session_state["selected_rsi_ticker"] = ticker
                            st.rerun()

                        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
