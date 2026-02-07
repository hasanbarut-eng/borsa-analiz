import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- HASAN BEY ÖZEL AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# 140+ EKSİKSİZ HİSSE LİSTESİ
hisse_listesi = [
    "ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA",
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
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER",
    "BRSAN", "SDTTR", "KOPOL", "SAYAS", "GLYHO", "TSKB", "BOBET", "ENERY", "TATEN", "IZENR"
]

hisseler = [h + ".IS" for h in sorted(list(set(hisse_listesi)))]

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []

for h in hisseler:
    try:
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
        if data.empty or len(data) < 30: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # HESAPLAMALAR
        rsi = rsi_hesapla(data["Close"]).iloc[-1]
        fiyat = data["Close"].iloc[-1]
        sma = data["Close"].rolling(20).mean().iloc[-1]
        hacim_ort = data["Volume"].rolling(10).mean().iloc[-1]
        hacim_son = data["Volume"].iloc[-1]

        # DURUMLAR
        c1 = "UYGUN" if 30 < rsi < 65 else "ZAYIF"
        c2 = "YUKARI" if fiyat > sma else "ASAGI"
        c3 = "GUCLU" if hacim_son > hacim_ort else "DUSUK"
        
        puan = 0
        if c1 == "UYGUN": puan += 1
        if c2 == "YUKARI": puan += 1
        if c3 == "GUCLU": puan += 1

        # SADECE EN İYİLER (2-3) VE EN KÖTÜLER (0)
        if puan in [0, 2, 3]:
            sonuclar.append({
                "Kod": h.replace(".IS", ""), "Fiyat": f"{fiyat:.2f}",
                "RSI": f"{rsi:.1f} ({c1})", "SMA": c2, "Hacim": c3, "Skor": puan
            })
        time.sleep(0.1)
    except: continue

# --- WEB GÖRÜNTÜSÜ ---
html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
    body {{ background: #000; color: #fff; font-family: sans-serif; text-align: center; }}
    table {{ width: 95%; margin: auto; border-collapse: collapse; }}
    th {{ background: #222; color: #00d2ff; padding: 15px; border: 1px solid #444; }}
    td {{ padding: 12px; border: 1px solid #444; font-weight: bold; }}
    .yesil {{ background: #004d00; color: #90ee90; }}
    .kirmizi {{ background: #660000; color: #ffcccc; }}
</style>
</head>
<body>
    <h2>🎯 HASAN BEY STRATEJİK ANALİZ (140+ HİSSE)</h2>
    <table>
        <tr>
            <th>HİSSE</th><th>FİYAT</th><th>RSI (30-65)</th><th>SMA20 (TREND)</th><th>HACİM (GÜÇ)</th><th>SKOR</th>
        </tr>
"""
for s in sorted(sonuclar, key=lambda x: -x['Skor']):
    renk = "yesil" if s['Skor'] >= 2 else "kirmizi"
    html += f"<tr class='{renk}'><td>{s['Kod']}</td><td>{s['Fiyat']}</td><td>{s['RSI']}</td><td>{s['SMA']}</td><td>{s['Hacim']}</td><td>{s['Skor']}/3</td></tr>"
html += "</table></body></html>"

with open("analiz_yeni.html", "w", encoding="utf-8") as f: f.write(html)

# --- TELEGRAM (İLK 5 İYİ VE İLK 5 KÖTÜ) ---
try:
    iyiler = sorted([x for x in sonuclar if x['Skor'] >= 2], key=lambda x: -x['Skor'])
    kotuler = [x for x in sonuclar if x['Skor'] == 0]
    
    msg = f"🚀 *HASAN BEY ANALİZ ÖZETİ*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    msg += "🟢 *TOP 5 İYİ HİSSE*\n"
    if iyiler:
        for i in iyiler[:5]: # Sadece ilk 5
            msg += f"✳️ {i['Kod']}: {i['Fiyat']} (Skor: {i['Skor']}/3)\n"
    else: msg += "Uygun hisse bulunamadı.\n"
    
    msg += "\n🔴 *TOP 5 KÖTÜ HİSSE*\n"
    if kotuler:
        for k in kotuler[:5]: # Sadece ilk 5
            msg += f"❌ {k['Kod']}: {k['Fiyat']} (Skor: 0)\n"
    else: msg += "Riskli hisse bulunamadı.\n"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except: pass
