import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY GENİŞ LİSTE (120+ HİSSE)
favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]
ek_liste = ["THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR", "EKGYO", "KARDMD", "PETKM", "ARCLK", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO", "ENJSA", "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN", "HALKB", "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM", "ASGYO", "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA", "BIENY", "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS", "CIMSA", "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL", "GESAN", "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT", "KLRGY", "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC", "QUAGR", "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER"]

hisseler = ["ESEN.IS"] + [h + ".IS" for h in sorted(list(set(favoriler + ek_liste))) if h != "ESEN"]

def rsi_manuel(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []

print(f"📡 {len(hisseler)} Hisse taranıyor, bu işlem birkaç dakika sürebilir...")

for h in hisseler:
    try:
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
        if data.empty or len(data) < 20: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # HESAPLAMALAR
        rsi_vals = rsi_manuel(data["Close"])
        last_rsi = rsi_vals.iloc[-1]
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        last_price = data["Close"].iloc[-1]
        avg_vol = data["Volume"].rolling(10).mean().iloc[-1]
        last_vol = data["Volume"].iloc[-1]

        # DURUMLAR
        rsi_durum = "UYGUN" if 30 < last_rsi < 65 else "DEĞİL"
        sma_durum = "ÜSTTE" if last_price > sma20 else "ALTTA"
        hacim_durum = "ARTMIŞ" if last_vol > avg_vol else "DÜŞÜK"
        
        puan = 0
        if rsi_durum == "UYGUN": puan += 1
        if sma_durum == "ÜSTTE": puan += 1
        if hacim_durum == "ARTMIŞ": puan += 1

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{last_price:.2f}",
            "RSI": f"{last_rsi:.1f}",
            "RSI_D": rsi_durum,
            "SMA_D": sma_durum,
            "Hacim_D": hacim_durum,
            "Puan": puan,
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.1)
    except: continue

# --- WEB PANELİ (BAŞLIKLI VE TÜM LİSTE) ---
html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
    body {{ background: #050505; color: #eee; font-family: sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ padding: 12px; border: 1px solid #222; text-align: center; }}
    th {{ background: #111; color: #3b82f6; }}
    .skor-3 {{ background: #064e3b; color: #6ee7b7; font-weight: bold; }}
    .skor-2 {{ background: #14532d; color: #86efac; }}
    .skor-0 {{ background: #450a0a; color: #f87171; }}
    .normal {{ background: #1a1a1a; color: #888; }}
</style>
</head>
<body>
    <h2 align="center">🎯 Hasan Bey 120+ Teknik Analiz Tablosu</h2>
    <p align="center">Toplam {len(sonuclar)} hisse taranmıştır. | {datetime.now().strftime('%H:%M')}</p>
    <table>
        <tr>
            <th>Hisse</th>
            <th>Fiyat</th>
            <th>RSI Durumu</th>
            <th>SMA20 (Yön)</th>
            <th>Hacim (Güç)</th>
            <th>Skor</th>
        </tr>
"""

# Web'de TÜMÜNÜ göster (Sıralama: Önce En İyiler)
for s in sorted(sonuclar, key=lambda x: (-x['Puan'], not x['Fav'])):
    renk = f"skor-{s['Puan']}" if s['Puan'] in [3, 2, 0] else "normal"
    star = "⭐" if s['Fav'] else ""
    html += f"""<tr class='{renk}'>
        <td>{s['Kod']} {star}</td>
        <td>{s['Fiyat']}</td>
        <td>{s['RSI']} ({s['RSI_D']})</td>
        <td>{s['SMA_D']}</td>
        <td>{s['Hacim_D']}</td>
        <td>{s['Puan']}/3</td>
    </tr>"""
html += "</table></body></html>"

with open("analiz_yeni.html", "w", encoding="utf-8") as f: f.write(html)

# --- TELEGRAM (FİLTRELİ ÖZET) ---
try:
    iyiler = [h for h in sonuclar if h['Puan'] >= 2]
    kotuler = [h for h in sonuclar if h['Puan'] == 0]
    msg = f"🚀 *HASAN BEY 120+ ANALİZ ÖZETİ*\n✅ Taranan: {len(sonuclar)} Hisse\n\n"
    if iyiler:
        msg += "🟢 *EN İYİLER (PUAN 2-3)*\n"
        for i in sorted(iyiler, key=lambda x: -x['Puan']):
            msg += f"✳️ {i['Kod']}: {i['Fiyat']} (Skor: {i['Puan']}/3)\n"
    if kotuler:
        msg += "\n🔴 *EN KÖTÜLER (PUAN 0)*\n"
        for k in kotuler:
            msg += f"❌ {k['Kod']}: {k['Fiyat']}\n"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except: pass
