export const PINE_SCRIPT_CODE = `//@version=5
indicator(" || STOCH + PSAR || HIJAU HOLD MERAH BUANG", shorttitle="STOCH + PSAR", overlay=false)

// ==========================================
// 1. INPUT PARAMETER
// ==========================================
// Parameter Stochastic (10, 5, 5)
stochLength = input.int(10, title="Stoch Period (%K Length)", group="Stochastic Settings")
smoothK     = input.int(5, title="Stoch Smooth %K", group="Stochastic Settings")
smoothD     = input.int(5, title="Stoch Smooth %D", group="Stochastic Settings")

// Parameter Parabolic SAR (Standard)
sarStart = input.float(0.02, title="PSAR Start", group="PSAR Settings")
sarInc   = input.float(0.02, title="PSAR Increment", group="PSAR Settings")
sarMax   = input.float(0.20, title="PSAR Maximum", group="PSAR Settings")

// ==========================================
// 2. KALKULASI STOCHASTIC & PSAR
// ==========================================
k = ta.sma(ta.stoch(close, high, low, stochLength), smoothK)
d = ta.sma(k, smoothD)
psar = ta.sar(sarStart, sarInc, sarMax)

// ==========================================
// 3. PLOTTING STOCHASTIC (PANE BAWAH)
// ==========================================
// Plot Garis Stochastic (%K dan %D)
pk = plot(k, title="%K", color=color.rgb(255, 82, 82), linewidth=2) // Merah
pd = plot(d, title="%D", color=color.rgb(41, 98, 255), linewidth=2) // Biru

// Plot Garis Batas Atas (70) dan Bawah (30)
hLineTop = plot(70, title="Level 70", color=color.red, linewidth=1)
hLineBot = plot(30, title="Level 30", color=color.blue, linewidth=1)

// Area "Kolam" Overbought (> 70) dan Oversold (< 30)
fill(pk, hLineTop, k > 70 ? color.new(color.red, 30) : na, title="Kolam Overbought (>70)")
fill(pk, hLineBot, k < 30 ? color.new(color.blue, 30) : na, title="Kolam Oversold (<30)")

// ==========================================
// 4. SINYAL CROSS & POSISI PANAH
// ==========================================
bullishCross = ta.crossover(k, d)
bearishCross = ta.crossunder(k, d)

// Offset agar panah berada di luar/di atas/bawah garis Stochastic
offsetVal = 4

// Panah Biru: Menunjuk ke Atas (Golden Cross) di bawah garis
plotshape(bullishCross ? math.min(k, d) - offsetVal : na, title="Golden Cross", style=shape.arrowup, location=location.absolute, color=color.blue, size=size.tiny)

// Panah Merah: Menunjuk ke Bawah (Death Cross) di atas garis
plotshape(bearishCross ? math.max(k, d) + offsetVal : na, title="Death Cross", style=shape.arrowdown, location=location.absolute, color=color.red, size=size.tiny)

// ==========================================
// 5. PLOTTING PSAR (CHART UTAMA)
// ==========================================
psarColor = psar < close ? color.green : color.red
plot(psar, title="Parabolic SAR", style=plot.style_circles, linewidth=2, color=psarColor, force_overlay=true)
`;
