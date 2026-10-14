# -*- coding: utf-8 -*-
"""
TEKNOFEST Yönetim Kurulu Aday Değerlendirme & Mülakat Paneli (Streamlit Dashboard)
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="TEKNOFEST YK Seçim & Mülakat Paneli",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel Stil (Modern TEKNOFEST Teması)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        border: 1px solid #334155;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .main-title {
        color: #F8FAFC;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .metric-card {
        background: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38BDF8;
    }
    .metric-val {
        font-size: 32px;
        font-weight: 800;
        color: #38BDF8;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .question-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%);
        border-left: 5px solid #EF4444;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 18px 0;
        border-top: 1px solid rgba(239, 68, 68, 0.2);
        border-right: 1px solid rgba(239, 68, 68, 0.2);
        border-bottom: 1px solid rgba(239, 68, 68, 0.2);
    }
    .question-title {
        font-size: 14px;
        font-weight: 700;
        color: #F87171;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .question-text {
        font-size: 16px;
        font-weight: 600;
        color: #F1F5F9;
        line-height: 1.5;
        font-style: italic;
    }
    .pill-green {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 8px;
        padding: 14px 18px;
        color: #4ADE80;
    }
    .pill-red {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 8px;
        padding: 14px 18px;
        color: #F87171;
    }
    .candidate-card-header {
        background: #1E293B;
        padding: 20px 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 16px;
    }
    .score-badge-high {
        background: #15803D;
        color: #DCFCE7;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    .score-badge-mid {
        background: #B45309;
        color: #FEF3C7;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    .score-badge-low {
        background: #B91C1C;
        color: #FEE2E2;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Veri Yükleme Fonksiyonu
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    csv_candidates = [
        os.path.join(current_dir, "degerlendirilmis_basvurular.csv"),
        os.path.join(current_dir, "TEKNOFEST Yönetim Kurulu Aday Üye Başvuru Formu.csv"),
        "degerlendirilmis_basvurular.csv",
        "TEKNOFEST Yönetim Kurulu Aday Üye Başvuru Formu.csv"
    ]
    file_to_load = None
    for f in csv_candidates:
        if os.path.exists(f):
            file_to_load = f
            break

    if not file_to_load:
        all_csvs = glob.glob(os.path.join(current_dir, "*.csv")) + glob.glob("*.csv")
        if all_csvs:
            file_to_load = all_csvs[0]

    if not file_to_load:
        return None

    try:
        df = pd.read_csv(file_to_load, encoding='utf-8-sig')
    except Exception:
        df = pd.read_csv(file_to_load, encoding='utf-8')
    return df

    # Eğer puanlanmamışsa evaluate.py'yi otomatik tetikleyelim
    if 'toplam_puan' not in df.columns:
        import subprocess
        subprocess.run([sys.executable, "evaluate.py"], check=True)
        df = pd.read_csv("degerlendirilmis_basvurular.csv", encoding='utf-8-sig')

    return df

df_raw = load_data()

if df_raw is None or len(df_raw) == 0:
    st.error("⚠️ Başvuru verisi bulunamadı! Lütfen dizinde CSV dosyasının olduğundan emin olun.")
    st.stop()

# İsim sütununu belirle
name_col = None
for c in ['std_name', 'Ad Soyad', 'ad soyad']:
    if c in df_raw.columns:
        name_col = c
        break
if not name_col:
    name_col = df_raw.columns[1]

# Geçerli satırları al
df = df_raw.dropna(subset=[name_col]).copy()

# Standart takma isimleri garantile
def get_val(row, std_key, fallback_idx=None):
    if f"std_{std_key}" in row and pd.notna(row[f"std_{std_key}"]):
        return str(row[f"std_{std_key}"])
    for c in row.index:
        if std_key in str(c).lower():
            val = row[c]
            return "" if pd.isna(val) else str(val)
    if fallback_idx is not None and fallback_idx < len(row):
        val = row.iloc[fallback_idx]
        return "" if pd.isna(val) else str(val)
    return "Belirtilmemiş"

# Sınıfları standartlaştır
def clean_grade(val):
    s = str(val).strip().lower()
    if 'hazır' in s:
        return 'Hazırlık'
    elif '1' in s or 'bir' in s:
        return '1. Sınıf'
    elif '2' in s:
        return '2. Sınıf'
    elif '3' in s:
        return '3. Sınıf'
    elif '4' in s:
        return '4. Sınıf'
    return str(val).strip()

df['clean_grade'] = df.apply(lambda r: clean_grade(get_val(r, 'grade', 3)), axis=1)
df['clean_dept'] = df.apply(lambda r: get_val(r, 'department', 2), axis=1)

# Başlık
st.markdown("""
<div class="main-header">
    <div class="main-title">
        <span>🚀 TEKNOFEST Yönetim Kurulu Aday Seçim & Mülakat Paneli</span>
    </div>
    <div class="sub-title">
        Aday başvurularının Yapay Zeka destekli puanlaması, kriz yönetimi analizi ve mülakat soru önerileri
    </div>
</div>
""", unsafe_allow_html=True)

# 1. ÜST METRİKLER
toplam_basvuru = len(df)
ortalama_puan = df['toplam_puan'].mean() if 'toplam_puan' in df else 0
mulakat_aday_sayisi = (df['toplam_puan'] >= 70).sum() if 'toplam_puan' in df else 0
en_yuksek_puan = df['toplam_puan'].max() if 'toplam_puan' in df else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{toplam_basvuru}</div>
        <div class="metric-label">Toplam Başvuru</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{ortalama_puan:.1f}</div>
        <div class="metric-label">Ortalama Puan (100 Üzerinden)</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #4ADE80;">{mulakat_aday_sayisi}</div>
        <div class="metric-label">Mülakata Çağrılabilir (70+ Puan)</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #F59E0B;">{en_yuksek_puan}</div>
        <div class="metric-label">En Yüksek Aday Puanı</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 2. YAN PANEL (FİLTRELER & AYARLAR)
with st.sidebar:
    st.header("🔍 Filtreleme ve Arama")
    
    # İsim arama
    search_query = st.text_input("Aday Ara (İsim / Bölüm)", placeholder="Örn: Burak, Mekatronik...")
    
    # Puan Slider
    min_score = st.slider("Minimum Toplam Puan", min_value=0, max_value=100, value=0, step=5)
    
    # Sınıf Filtresi
    all_grades = sorted(list(df['clean_grade'].unique()))
    selected_grades = st.multiselect("Sınıf Seçimi", options=all_grades, default=all_grades)
    
    # Bölüm Filtresi
    all_depts = sorted(list(df['clean_dept'].unique()))
    selected_depts = st.multiselect("Bölüm Seçimi", options=all_depts, default=[])

    # Sıralama
    sort_option = st.selectbox(
        "Aday Sıralaması",
        options=["Puana Göre (Azalan)", "Puana Göre (Artan)", "İsme Göre (A-Z)"]
    )

    st.markdown("---")
    st.markdown("### ⚙️ LLM Yeniden Değerlendirme")
    user_api_key = st.text_input("Google Gemini API Key (Opsiyonel)", type="password", help="Kendi Gemini API anahtarınız ile adayları yeniden puanlamak için giriniz.")
    if st.button("🚀 Tüm Adayları LLM ile Puanla"):
        if not user_api_key:
            st.warning("Lütfen geçerli bir Gemini API anahtarı giriniz.")
        else:
            with st.spinner("Adaylar Gemini 2.5 Flash ile değerlendiriliyor..."):
                import subprocess
                cmd = [sys.executable, "evaluate.py", "--api-key", user_api_key]
                res = subprocess.run(cmd, capture_output=True, text=True)
                st.cache_data.clear()
                st.success("Yeniden değerlendirme tamamlandı! Sayfa yenileniyor...")
                st.rerun()

# Filtreleri uygula
filtered_df = df.copy()

if min_score > 0:
    filtered_df = filtered_df[filtered_df['toplam_puan'] >= min_score]

if selected_grades:
    filtered_df = filtered_df[filtered_df['clean_grade'].isin(selected_grades)]

if selected_depts:
    filtered_df = filtered_df[filtered_df['clean_dept'].isin(selected_depts)]

if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[
        filtered_df[name_col].astype(str).str.lower().str.contains(q) |
        filtered_df['clean_dept'].astype(str).str.lower().str.contains(q)
    ]

# Sıralama uygula
if sort_option == "Puana Göre (Azalan)":
    filtered_df = filtered_df.sort_values(by="toplam_puan", ascending=False)
elif sort_option == "Puana Göre (Artan)":
    filtered_df = filtered_df.sort_values(by="toplam_puan", ascending=True)
else:
    filtered_df = filtered_df.sort_values(by=name_col, ascending=True)

# 3. ANA SAYFA DÜZENİ (SOL: Histogram & Liste, SAĞ: Aday Detay)
col_left, col_right = st.columns([1, 1.4], gap="large")

with col_left:
    st.subheader("📊 Puan Dağılımı")
    
    # Histogram Grafiği
    fig_hist = px.histogram(
        df,
        x="toplam_puan",
        nbins=12,
        color_discrete_sequence=['#38BDF8'],
        labels={'toplam_puan': 'Toplam Puan', 'count': 'Aday Sayısı'},
        opacity=0.85
    )
    fig_hist.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=200,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#334155', range=[0, 105]),
        yaxis=dict(showgrid=True, gridcolor='#334155'),
        font=dict(color='#94A3B8')
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader(f"👥 Aday Listesi ({len(filtered_df)} Aday)")

    if len(filtered_df) == 0:
        st.info("Filtre kriterlerine uygun aday bulunamadı.")
        selected_candidate_idx = None
    else:
        # Aday seçim listesi formatı
        candidate_options = []
        candidate_indices = []
        for idx, row in filtered_df.iterrows():
            cand_name = str(row[name_col]).strip()
            cand_score = row['toplam_puan']
            cand_dept = str(row['clean_dept'])[:25]
            badge_icon = "🟢" if cand_score >= 70 else ("🟡" if cand_score >= 50 else "🔴")
            label = f"{badge_icon} [{cand_score} Puan] {cand_name} - {cand_dept}"
            candidate_options.append(label)
            candidate_indices.append(idx)

        selected_label_idx = st.radio(
            "İncelemek istediğiniz adayı seçin:",
            options=range(len(candidate_options)),
            format_func=lambda i: candidate_options[i],
            label_visibility="collapsed"
        )
        selected_candidate_idx = candidate_indices[selected_label_idx]

        # CSV İndirme Butonu
        st.write("")
        csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Filtrelenmiş Listeyi İndir (CSV)",
            data=csv_data,
            file_name="teknofest_degerlendirilmis_adaylar.csv",
            mime="text/csv",
            use_container_width=True
        )

with col_right:
    if selected_candidate_idx is not None:
        cand_row = df.loc[selected_candidate_idx]
        cand_name = str(cand_row[name_col]).strip()
        cand_score = int(cand_row['toplam_puan'])
        cand_dept = get_val(cand_row, 'department', 2)
        cand_grade = get_val(cand_row, 'grade', 3)
        cand_phone = get_val(cand_row, 'phone', 4)
        cand_email = get_val(cand_row, 'email', 5)
        cand_std_no = get_val(cand_row, 'student_no', 6)
        cand_timestamp = get_val(cand_row, 'timestamp', 0)

        p_deneyim = int(cand_row.get('deneyim_puan', 0))
        p_takim = int(cand_row.get('takim_uyumu_puan', 0))
        p_devam = int(cand_row.get('devamlilik_puan', 0))
        p_iletisim = int(cand_row.get('iletisim_puan', 0))

        one_cikan = cand_row.get('one_cikan_yon', 'Belirtilmemiş')
        riskli_yon = cand_row.get('riskli_supheli_yon', 'Belirtilmemiş')
        soru_onerisi = cand_row.get('mulakat_soru_onerisi', 'Mülakat sorusu bulunamadı.')
        kaynak = cand_row.get('degerlendirme_kaynagi', 'Kural & Semantik Analiz')

        # Skor rozeti rengi
        if cand_score >= 70:
            badge_html = f'<span class="score-badge-high">⭐ {cand_score}/100 - MÜLAKATA UYGUN</span>'
        elif cand_score >= 50:
            badge_html = f'<span class="score-badge-mid">⚡ {cand_score}/100 - DEĞERLENDİRİLEBİLİR</span>'
        else:
            badge_html = f'<span class="score-badge-low">⚠️ {cand_score}/100 - DÜŞÜK UYUM</span>'

        # Aday Başlık Kartı
        st.markdown(f"""
        <div class="candidate-card-header">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h2 style="margin: 0; color: #F8FAFC; font-size: 24px; font-weight: 700;">{cand_name}</h2>
                <div>{badge_html}</div>
            </div>
            <div style="color: #94A3B8; font-size: 14px; margin-bottom: 12px;">
                🎓 <b>Bölüm:</b> {cand_dept} | <b>Sınıf:</b> {cand_grade}
            </div>
            <div style="display: flex; gap: 16px; flex-wrap: wrap; color: #CBD5E1; font-size: 13px; border-top: 1px solid #334155; padding-top: 10px;">
                <span>📞 <b>Tel:</b> {cand_phone}</span>
                <span>✉️ <b>E-posta:</b> {cand_email}</span>
                <span>🆔 <b>Öğrenci No:</b> {cand_std_no}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4 Kriter Puan Kartları
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Topluluk & TEKNOFEST", f"{p_deneyim}/25")
        with sc2:
            st.metric("Takım Uyumu & Kriz", f"{p_takim}/30")
        with sc3:
            st.metric("Devamlılık & Zaman", f"{p_devam}/20")
        with sc4:
            st.metric("Öz Farkındalık", f"{p_iletisim}/25")

        # Radar Grafiği & Karşılaştırma
        categories = ['Deneyim (25)', 'Takım Uyumu (30)', 'Devamlılık (20)', 'Öz Farkındalık (25)']
        candidate_values = [
            (p_deneyim / 25) * 100,
            (p_takim / 30) * 100,
            (p_devam / 20) * 100,
            (p_iletisim / 25) * 100
        ]
        # Genel ortalama değerleri
        avg_deneyim = (df['deneyim_puan'].mean() / 25) * 100
        avg_takim = (df['takim_uyumu_puan'].mean() / 30) * 100
        avg_devam = (df['devamlilik_puan'].mean() / 20) * 100
        avg_iletisim = (df['iletisim_puan'].mean() / 25) * 100
        avg_values = [avg_deneyim, avg_takim, avg_devam, avg_iletisim]

        # Radar chart
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=candidate_values + [candidate_values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(56, 189, 248, 0.3)',
            line=dict(color='#38BDF8', width=2),
            name=f"{cand_name}"
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_values + [avg_values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(148, 163, 184, 0.15)',
            line=dict(color='#94A3B8', width=1.5, dash='dash'),
            name="Genel Ortalama"
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#334155'),
                angularaxis=dict(linecolor='#334155', tickfont=dict(color='#CBD5E1', size=11))
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#CBD5E1')),
            margin=dict(l=30, r=30, t=20, b=30),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # MÜLAKATTA KESİNLİKLE SORULMASI GEREKEN STRATEJİK SORU KUTUSU
        st.markdown(f"""
        <div class="question-box">
            <div class="question-title">
                🎯 MÜLAKATTA KESİNLİKLE SORULMASI GEREKEN STRATEJİK SORU
            </div>
            <div class="question-text">
                "{soru_onerisi}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Güçlü & Riskli Yönler
        col_strong, col_risk = st.columns(2)
        with col_strong:
            st.markdown(f"""
            <div class="pill-green">
                <div style="font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    ✅ ÖNE ÇIKAN GÜÇLÜ YÖN
                </div>
                <div style="font-size: 13.5px; line-height: 1.4; color: #DCFCE7;">
                    {one_cikan}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_risk:
            st.markdown(f"""
            <div class="pill-red">
                <div style="font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    ⚠️ RİSKLİ / ŞÜPHELİ YÖN
                </div>
                <div style="font-size: 13.5px; line-height: 1.4; color: #FEE2E2;">
                    {riskli_yon}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # FORMDA VERİLEN TÜM HAM YANITLAR (AKORDİYON)
        with st.expander("📝 Adayın Formda Verdiği Tüm Ham Yanıtlar", expanded=False):
            st.markdown(f"""
            **1. Daha önce topluluk deneyiminiz oldu mu?**  
            > {get_val(cand_row, 'community_exp', 7)}

            **2. Daha önce TEKNOFEST kapsamında görev aldınız mı?**  
            > {get_val(cand_row, 'teknofest_exp', 8)}

            **3. Kendinizde güçlü gördüğünüz özellikler nelerdir?**  
            > {get_val(cand_row, 'strengths', 9)}

            **4. Toplantılara düzenli katılım sağlayabilir misiniz?**  
            > {get_val(cand_row, 'attendance', 10)}

            **5. Yönetim kurulunda alınan bir karara katılmıyorsunuz fakat karar çoğunluk tarafından kabul edildi. Nasıl bir tutum sergilersiniz?**  
            > {get_val(cand_row, 'crisis_conflict', 11)}

            **6. Eklemek istediğiniz başka bir şey var mı?**  
            > {get_val(cand_row, 'additional_notes', 12)}

            ---
            *Başvuru Zamanı:* `{cand_timestamp}` | *Değerlendirme Motoru:* `{kaynak}`
            """)
    else:
        st.info("Lütfen sol taraftan detaylarını görmek istediğiniz adayı seçin.")
