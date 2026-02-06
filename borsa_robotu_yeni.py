import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY FAVORİLER VE 100+ LİSTE (Eksiksiz)
favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]

ek_liste = [
    "THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR",
    "EKGYO", "KARDMD", "PETKM", "ARCLK", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO", "ENJSA",
    "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN", "HALKB",
    "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN", "ADESE",
    "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK", "ALFAS",
    "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM", "ASGYO",
    "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA", "BIENY",
    "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS", "CIMSA",
    "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL", "GESAN",
    "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT", "KLRGY",
    "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC", "QUAGR",
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "ALVES", "REEDR"
]

hisseler = [h + ".IS" for h in sorted(list(set(favoriler + ek_liste)))]

def rsi_hesapla(series, period=14):
    """Kütüphane hatası almamak için manuel RSI hesaplama."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []
print(f"🚀 Toplam {len(hisseler)} hisse taranıyor...")

for h in hisseler:
    try:
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
        if data.empty or len(data) < 20: continue
        
        # Yahoo Multi-index düzeltmesi
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # RSI ve Hareketli Ortalama (SMA)
        rsi_serisi = rsi_hesapla(data["Close"])
        son_rsi = rsi_serisi.iloc[-1]
        son_fiyat = data["Close"].iloc[-1]
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        
        puan = 0
        if son_rsi < 50: puan += 1
        if son_fiyat > sma20: puan += 1

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{son_fiyat:.2f}",
            "RSI": f"{son_rsi:.1f}",
            "Skor": f"{puan}/2",
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.12) # Engel yememek için kısa bekleme
    except: continue

# --- WEB PANELİ (HTML) ÜRETİMİ ---
html = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Hasan Bey 100+ Panel</title>
    <style>
        body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px; border: 1px solid #334155; text-align: center; }}
        th {{ background: #334155; color: #3b82f6; }}
        .fav {{ background: #1e3a8a !important; color: white; font-weight: bold; }}
    </style>
</head>
<body>
    <h2 align="center">🎯 Hasan Bey Stratejik Analiz (120+ Hisse)</h2>
    <p align="center">Güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <table>
        <tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor</th></tr>
"""
# Favoriler üstte, sonra skora göre sırala
sirali = sorted(sonuclar, key=lambda x: (not x['Fav'], -int(x['Skor'][0])))
for s in sirali:
    cls = "class='fav'" if s['Fav'] else ""
    html += f"<tr {cls}><td>{s['Kod']}</td><td>{s['Fiyat']} TL</td><td>{s['RSI']}</td><td>{s['Skor']}</td></tr>"

html += "</table></body></html>"
with open("index_yeni.html", "w", encoding="utf-8") as f: f.write(html)

# --- TELEGRAM RAPORU ---
try:
    firsatlar = [h for h in sonuclar if int(h['Skor'][0]) >= 1]
    if firsatlar:
        msg = f"🚀 *HASAN BEY 100+ ANALİZ*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        for f in firsatlar[:15]:
            msg += f"✅ {f['Kod']}: {f['Fiyat']} (RSI: {f['RSI']})\n"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except: pass
