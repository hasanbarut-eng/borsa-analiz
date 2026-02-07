import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR (HASAN BEY ÖZEL) ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY FAVORİLER VE 120+ GENİŞ LİSTE
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
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER"
]

hisseler = [h + ".IS" for h in sorted(list(set(favoriler + ek_liste)))]

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []
print(f"🚀 {len(hisseler)} Hisse Taranıyor...")

for h in hisseler:
    try:
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=20)
        if data.empty or len(data) < 20: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # KRİTER 1: RSI
        rsi_serisi = rsi_hesapla(data["Close"])
        son_rsi = rsi_serisi.iloc[-1]
        
        # KRİTER 2: SMA20
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        son_fiyat = data["Close"].iloc[-1]
        
        # KRİTER 3: HACİM
        hacim_ort = data["Volume"].rolling(10).mean().iloc[-1]
        son_hacim = data["Volume"].iloc[-1]
        
        puan = 0
        if 30 < son_rsi < 65: puan += 1
        if son_fiyat > sma20: puan += 1
        if son_hacim > hacim_ort: puan += 1

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{son_fiyat:.2f}",
            "RSI": f"{son_rsi:.1f}",
            "Skor": f"{puan}/3",
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.1)
    except: continue

# --- WEB PANELİ (DİĞER PROGRAMLARI ETKİLEMEZ) ---
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body {{ background: #0f172a; color: white; font-family: sans-serif; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; }}
        th, td {{ border: 1px solid #334155; padding: 10px; text-align: center; }}
        th {{ background: #334155; }}
        .fav {{ background: #1e3a8a !important; font-weight: bold; }}
        .high {{ color: #4ade80; font-weight: bold; }}
    </style>
</head>
<body>
    <h2 align='center'>🎯 Hasan Bey Üçlü Filtre Paneli</h2>
    <p align='center'>Taranan: {len(sonuclar)} Hisse | {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <table>
        <tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor (3 Üzerinden)</th></tr>
"""
# Sıralama: Favoriler en üstte, sonra skora göre
sirali = sorted(sonuclar, key=lambda x: (not x['Fav'], -int(x['Skor'][0])))
for s in sirali:
    cls = "class='fav'" if s['Fav'] else ""
    skor_renk = "class='high'" if int(s['Skor'][0]) >= 2 else ""
    html += f"<tr {cls}><td>{s['Kod']}</td><td>{s['Fiyat']} TL</td><td>{s['RSI']}</td><td {skor_renk}>{s['Skor']}</td></tr>"

html += "</table></body></html>"
# DİKKAT: İsim analiz_yeni.html yapılarak çakışma önlendi
with open("analiz_yeni.html", "w", encoding="utf-8") as f:
    f.write(html)

# --- TELEGRAM (SEÇENEK B) ---
try:
    if sonuclar:
        msg = f"🚀 *HASAN BEY ÜÇLÜ ANALİZ*\n✅ Taranan: {len(sonuclar)} Hisse\n\n"
        for f in sonuclar:
            if int(f['Skor'][0]) >= 2: # Sadece 2 ve 3 puan alanları gönder
                emoji = "💎" if f['Fav'] else "✅"
                line = f"{emoji} *{f['Kod']}*: {f['Fiyat']} (Skor: {f['Skor']})\n"
                if len(msg) + len(line) > 4000:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                    msg = ""
                msg += line
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except: pass
