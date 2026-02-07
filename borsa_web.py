import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os

# --- KONFİGÜRASYON ---
st.set_page_config(page_title="Hasan Bey BİST Terminal", layout="wide")

def save_user_data(username, data):
    """Kullanıcı ismine özel listeyi dosyaya kaydeder."""
    try:
        if not os.path.exists("users"):
            os.makedirs("users")
        with open(f"users/{username}.json", "w") as f:
            json.dump(data, f)
        return True
    except Exception as e:
        st.error(f"Kaydetme hatası: {e}")
        return False

def load_user_data(username):
    """Kullanıcı ismine göre listeyi geri yükler."""
    try:
        file_path = f"users/{username}.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None
    except:
        return None

# --- ANA PANEL ---
def main():
    st.sidebar.title("👤 Kullanıcı Girişi")
    username = st.sidebar.text_input("İsminizi Girin:", value="Hasan_Bey").strip()
    
    # Kullanıcı değiştiğinde veya sayfa yüklendiğinde listeyi getir
    if username:
        saved_list = load_user_data(username)
        if saved_list and 'user_watchlist' not in st.session_state:
            st.session_state.user_watchlist = saved_list
        elif 'user_watchlist' not in st.session_state:
            st.session_state.user_watchlist = ["ESEN", "SASA", "THYAO"] # Varsayılan
    
    # --- HİSSE SEÇİMİ ---
    from borsa_web import get_bist_list # Mevcut tam listenizi buradan aldığını varsayıyoruz
    all_symbols = get_bist_list()
    
    st.sidebar.header("📋 Takip Listeniz")
    selected_stocks = st.sidebar.multiselect(
        f"{username} kullanıcısının listesi:",
        options=all_symbols,
        default=st.session_state.get('user_watchlist', ["ESEN"])
    )

    # --- KAYDETME BUTONU ---
    if st.sidebar.button("💾 LİSTEMİ İSMİME KAYDET"):
        if username:
            if save_user_data(username, selected_stocks):
                st.session_state.user_watchlist = selected_stocks
                st.sidebar.success(f"✅ {username}, listen başarıyla kaydedildi!")
                st.rerun()
        else:
            st.sidebar.warning("Lütfen önce bir isim girin!")

    # --- 10 İNDİKATÖRLÜ ANALİZ MOTORU ---
    st.title(f"🛡️ {username} - BİST Karar Destek Terminali")
    
    if st.button(f"🚀 {len(selected_stocks)} Hisseyi Analiz Et"):
        # Buraya profesyonel_analiz_10 fonksiyonunuz gelecek
        run_analysis_logic(selected_stocks)

def run_analysis_logic(stocks):
    """10 indikatörü hesaplayıp tabloyu basan kısım"""
    # ... (Önceki mesajdaki analiz döngüsü burada aynen kalacak)
    pass

if __name__ == "__main__":
    main()
