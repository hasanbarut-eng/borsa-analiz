import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY FAVORİLER
favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]

# GENİŞLETİLMİŞ 120+ LİSTE (BİST En Aktifler)
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
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "ALFAS", "BRSAN",
    "SDTTR", "KOPOL", "FORMT", "HUNER", "ZEDUR", "SAYAS", "YEOTK", "GLYHO", "TSKB", "SKBNK"
]

hisseler = [h + ".IS" for h in sorted(list(set(favoriler + ek_liste)))]

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []
print(f"📡 Toplam {len(hisseler)} hisse taranıyor... Lütfen bekleyin.")

for h in hisseler:
    try:
        # Veri çekme denemesini artırdık
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=20)
        if data.empty or len(data) < 20: 
            print(f"⚠️ {h} verisi çekilemedi.")
            continue
            
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)

        rsi_serisi = rsi_hesapla(data["Close"])
        son_rsi = rsi_serisi.iloc[-1]
        son_fiyat = data["Close"].iloc[-1]
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        
        puan = 0
        if son_rsi < 55: puan += 1
        if son_fiyat > sma20: puan += 1

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{son_fiyat:.2f}",
            "RSI": f"{son_rsi:.1f}",
            "Skor": f"{puan}/2",
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.15)
    except: continue

# --- WEB PANELİ ÜRETİMİ ---
html = f"<html><head><meta charset='UTF-8'></head><body style='background:#121212;color:white;font-family:sans-serif;padding:20px;'>"
html += f"<h2 align='center'>🎯 Hasan Bey 120+ Stratejik Analiz</h2><p align='center'>Toplam Taranan: {len(sonuclar)} Hisse | Güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>"
html += "<table border='1' width='100%' style='border-collapse:collapse;text-align:center;'><tr style='background:#333;'><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor</th></tr>"
for s in sorted(sonuclar, key=lambda x: (not x['Fav'], -int(x['Skor'][0]))):
    renk = "#1e3a8a" if s['Fav'] else "#1e1e1e"
    html += f"<tr style='background:{renk};'><td>{s['Kod']}</td><td>{s['Fiyat']} TL</td><td>{s['RSI']}</td><td>{s['Skor']}</td></tr>"
html += "</table></body></html>"
with open("index_yeni.html", "w", encoding="utf-8") as f: f.write(html)

# --- TELEGRAM: TÜM SONUÇLAR (SEÇENEK B) ---
try:
    if sonuclar:
        msg = f"📊 *HASAN BEY 120+ ANALİZ RAPORU*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n✅ Taranan: {len(sonuclar)} Hisse\n\n"
        for f in sonuclar:
            # Sadece skor 1 ve 2 olanları göndererek mesajı anlamlı tutuyoruz
            if int(f['Skor'][0]) >= 1:
                emoji = "💎" if f['Fav'] else "✅"
                line = f"{emoji} *{f['Kod']}*: {f['Fiyat']} (RSI: {f['RSI']})\n"
                if len(msg) + len(line) > 4000:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                    msg = ""
                msg += line
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
except: pass
