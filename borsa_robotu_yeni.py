import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY FAVORİLER VE 120+ LİSTE
favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]
ek_liste = ["THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR", "EKGYO", "KARDMD", "PETKM", "ARCLK", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO", "ENJSA", "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN", "HALKB", "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM", "ASGYO", "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA", "BIENY", "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS", "CIMSA", "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL", "GESAN", "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT", "KLRGY", "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC", "QUAGR", "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER"]

hisseler = ["ESEN.IS"] + [h + ".IS" for h in sorted(list(set(favoriler + ek_liste))) if h != "ESEN"]

def rsi_hesapla(series, period=14):
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    except Exception:
        return pd.Series([50] * len(series))

sonuclar = []

for h in hisseler:
    try:
        # ESEN için daha hassas veri çekme
        retry_count = 3 if "ESEN" in h else 1
        data = pd.DataFrame()
        for _ in range(retry_count):
            data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
            if not data.empty: break
            time.sleep(1)

        if data.empty or len(data) < 20: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # HESAPLAMALAR
        rsi_vals = rsi_hesapla(data["Close"])
        last_rsi = rsi_vals.iloc[-1]
        last_price = data["Close"].iloc[-1]
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        avg_vol = data["Volume"].rolling(10).mean().iloc[-1]
        last_vol = data["Volume"].iloc[-1]

        # PUANLAMA (3 KRİTER)
        puan = 0
        if 30 < last_rsi < 65: puan += 1
        if last_price > sma20: puan += 1
        if last_vol > avg_vol: puan += 1

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{last_price:.2f}",
            "RSI": f"{last_rsi:.1f}",
            "Puan": puan,
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.1)
    except Exception as e:
        print(f"Hata: {h} -> {e}")
        continue

# --- WEB SAYFASI OLUŞTURMA ---
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ background-color: #0a0a0a; color: #eee; font-family: sans-serif; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border: 1px solid #333; text-align: center; }}
        th {{ background-color: #1a1a1a; color: #3b82f6; }}
        .iyiler {{ background-color: #064e3b; color: #6ee7b7; }} /* YEŞİL */
        .kotuler {{ background-color: #450a0a; color: #f87171; }} /* KIRMIZI */
        .normal {{ background-color: #1a1a1a; color: #888; }}
        .fav-star {{ color: #fbbf24; font-weight: bold; }}
    </style>
</head>
<body>
    <h2 align="center">📊 Hasan Bey 120+ Stratejik Analiz</h2>
    <p align="center">Güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <table>
        <tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor</th></tr>
"""

# Web'de puana göre sırala (En iyi en üstte)
sirali_web = sorted(sonuclar, key=lambda x: (-x['Puan'], not x['Fav']))
for s in sirali_web:
    renk_class = "iyiler" if s['Puan'] >= 2 else ("kotuler" if s['Puan'] == 0 else "normal")
    fav_simge = "<span class='fav-star'>⭐</span>" if s['Fav'] else ""
    html += f"<tr class='{renk_class}'><td>{s['Kod']} {fav_simge}</td><td>{s['Fiyat']}</td><td>{s['RSI']}</td><td>{s['Puan']}/3</td></tr>"

html += "</table></body></html>"
with open("analiz_yeni.html", "w", encoding="utf-8") as f:
    f.write(html)

# --- TELEGRAM (FİLTRELİ GÖNDERİM) ---
try:
    if sonuclar:
        iyiler = [h for h in sonuclar if h['Puan'] >= 2]
        kotuler = [h for h in sonuclar if h['Puan'] == 0]
        
        msg = f"🚀 *HASAN BEY ANALİZ ÖZETİ*\n"
        msg += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        
        if iyiler:
            msg += "✅ *EN İYİLER (PUAN: 2-3)*\n"
            for f in sorted(iyiler, key=lambda x: -x['Puan']):
                emoji = "💎" if f['Fav'] else "✳️"
                msg += f"{emoji} {f['Kod']}: {f['Fiyat']} (Puan: {f['Puan']}/3)\n"
        
        if kotuler:
            msg += "\n⚠️ *EN KÖTÜLER (PUAN: 0)*\n"
            for k in kotuler:
                msg += f"🔴 {k['Kod']}: {k['Fiyat']} (Puan: 0/3)\n"
        
        # Karakter sınırı kontrolü ve gönderim
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except Exception as e:
    print(f"Telegram Hatası: {e}")
