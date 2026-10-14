# -*- coding: utf-8 -*-
"""
TEKNOFEST Yönetim Kurulu Aday Değerlendirme Sistemi (Backend / LLM Puanlama)
"""

import os
import sys
import glob
import json
import re
import argparse
from typing import Dict, Any, Optional, List
import pandas as pd
from dotenv import load_dotenv

# UTF-8 stdout desteği
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

# Sütun eşleştirme anahtarları
COL_PATTERNS = {
    'timestamp': ['zaman damgası', 'timestamp'],
    'name': ['ad soyad', 'isim', 'ad'],
    'department': ['bölüm-fakülte', 'bölüm', 'fakülte', 'bolum'],
    'grade': ['sınıf', 'sinif'],
    'phone': ['telefon numarası', 'telefon', 'tel'],
    'email': ['e-posta', 'eposta', 'email', 'mail'],
    'student_no': ['öğrenci numarası', 'öğrenci no', 'ogrenci no'],
    'community_exp': ['daha önce topluluk deneyiminiz oldu mu', 'topluluk deneyiminiz', 'topluluk'],
    'teknofest_exp': ['daha önce teknofest kapsamında görev aldınız mı', 'teknofest kapsamında', 'teknofest'],
    'strengths': ['kendinizde güçlü gördüğünüz özellikler', 'güçlü gördüğünüz özellikler', 'güçlü'],
    'attendance': ['toplantılara düzenli katılım sağlayabilir misiniz', 'düzenli katılım', 'katılım'],
    'crisis_conflict': ['yönetim kurulunda alınan bir karara katılmıyorsunuz', 'alınan bir karara katılmıyorsunuz', 'çoğunluk tarafından kabul edildi', 'tutum sergilersiniz'],
    'additional_notes': ['eklemek istediğiniz başka bir şey var mı', 'eklemek istediğiniz']
}

def find_column(df: pd.DataFrame, key: str) -> Optional[str]:
    patterns = COL_PATTERNS.get(key, [])
    for col in df.columns:
        clean_col = str(col).strip().lower()
        for p in patterns:
            if p in clean_col:
                return col
    return None

def get_input_file() -> str:
    candidates = glob.glob('*TEKNOFEST*.csv') + glob.glob('*Formu*.csv') + glob.glob('*.csv')
    valid = [f for f in candidates if 'degerlendirilmis' not in f.lower()]
    if valid:
        return valid[0]
    raise FileNotFoundError("Başvuru CSV dosyası bulunamadı!")

def evaluate_with_gemini(client, model_name: str, candidate_data: Dict[str, str]) -> Dict[str, Any]:
    """Gemini API kullanarak adayı değerlendirir."""
    system_instruction = """Sen profesyonel bir TEKNOFEST Yönetim Kurulu Seçim Analistisin. 
Sana bir adayın başvuru formundaki yanıtları verilecek. 
Adayı TEKNOFEST öğrenci kulübü yönetim kurulu üyeliği için şu 4 ana kritere göre değerlendireceksin:

1. Topluluk & TEKNOFEST Deneyimi (0-25 puan):
   - Topluluk tecrübesi (kulüp üyeliği, aktif görev, organizasyon, liderlik) ve TEKNOFEST geçmişi (yarışmacı, takım kaptanı, teknik görev, gönüllü). 
   - İkisi de yoksa veya sadece izleyiciyse düşük (0-7), kulüp veya lise tecrübesi varsa orta (8-16), TEKNOFEST takımı/yarışmacılığı ve aktif kulüp yöneticiliği varsa yüksek (17-25).

2. Kriz Yönetimi & Takım Uyumu (0-30 puan):
   - 'Alınan karara katılmıyorsunuz...' sorusuna verilen tutum.
   - İdeal yönetim kurulu tutumu: Karar öncesinde yapıcı ve saygılı şekilde fikrini savunur, ancak çoğunluk kararı aldıktan sonra karara saygı gösterir ve takımın başarısı için kararı sahiplenir (25-30 puan).
   - Pasif/kayıtsız kabulleniş ('yapacak bir şey yok', 'çoğunluk ne derse o') fikir üretme zayıflığı gösterir (15-22 puan).
   - 'Ben kendi fikrimde direnirim / katılmam' tutumu yönetim kurulunu kilitleyecek çatışmacı bir risktir (0-12 puan).
   - Boş veya ciddiyetsiz tek nokta/kelimelik cevaplar (0-5 puan).

3. Devamlılık & Zaman Taahhüdü (0-20 puan):
   - 'Toplantılara düzenli katılım...' sorusuna odaklan.
   - Sorumluluk bilinciyle net, planlı taahhüt ve öngörülemeyen durumlarda şeffaf iletişim belirtenler (17-20 puan).
   - Standart kuru 'evet' cevabı (12-15 puan).
   - Çakışma, sınav, ders şartı koşan veya 'gelemeyebilirim' diyenler (6-11 puan).
   - Ciddiyetsiz veya isteksiz olanlar (0-5 puan).

4. Öz Farkındalık & İletişim Becerisi (0-25 puan):
   - 'Güçlü yönler' sorusu ve form genelindeki dil, imla, kendini ifade yeteneği, üslup ve ciddiyet.
   - Somut, analitik, özgüvenli ve saygılı ifade (20-25 puan).
   - Sıradan birkaç kelimelik genel ifadeler (12-18 puan).
   - Baştan savma, tek noktalı veya lakayt cevaplar (0-10 puan).

Çıktıyı KESİNLİKLE aşağıdaki katı JSON şemasıyla ver:
{
  "deneyim_puan": int (0-25),
  "takim_uyumu_puan": int (0-30),
  "devamlilik_puan": int (0-20),
  "iletisim_puan": int (0-25),
  "toplam_puan": int (bu dördünün toplamı, 0-100),
  "one_cikan_yon": "Kısa 1 cümle",
  "riskli_supheli_yon": "Kısa 1 cümle",
  "mulakat_soru_onerisi": "Adayın mülakatta köşeye sıkıştırılacağı veya teyit edileceği spesifik 1 soru"
}
"""

    prompt = f"""
Aday Bilgileri:
- Ad Soyad: {candidate_data.get('name', 'Bilinmiyor')}
- Bölüm / Fakülte: {candidate_data.get('department', 'Bilinmiyor')}
- Sınıf: {candidate_data.get('grade', 'Bilinmiyor')}

Adayın Form Yanıtları:
1. Daha önce topluluk deneyiminiz oldu mu? Kısaca bahsediniz:
"{candidate_data.get('community_exp', '')}"

2. Daha önce TEKNOFEST kapsamında görev aldınız mı? Kısaca bahsediniz:
"{candidate_data.get('teknofest_exp', '')}"

3. Kendinizde güçlü gördüğünüz özellikler nelerdir? Kısaca bahsediniz:
"{candidate_data.get('strengths', '')}"

4. Toplantılara düzenli katılım sağlayabilir misiniz?:
"{candidate_data.get('attendance', '')}"

5. Yönetim kurulunda alınan bir karara katılmıyorsunuz fakat karar çoğunluk tarafından kabul edildi. Nasıl bir tutum sergilersiniz?:
"{candidate_data.get('crisis_conflict', '')}"

6. Eklemek istediğiniz başka bir şey var mı?:
"{candidate_data.get('additional_notes', '')}"
"""

    response = client.models.generate_content(
        model=model_name,
        contents=[system_instruction, prompt],
        config={
            'response_mime_type': 'application/json',
            'temperature': 0.2
        }
    )
    
    text = response.text.strip()
    return json.loads(text)


def evaluate_heuristically(candidate_data: Dict[str, str]) -> Dict[str, Any]:
    """
    LLM API anahtarı bulunmadığında çalışan, insan değerlendirici hassasiyetinde
    semantik ve kural tabanlı değerlendirme motoru.
    """
    comm = str(candidate_data.get('community_exp', '')).strip().lower()
    tekno = str(candidate_data.get('teknofest_exp', '')).strip().lower()
    strength = str(candidate_data.get('strengths', '')).strip()
    strength_lower = strength.lower()
    att = str(candidate_data.get('attendance', '')).strip().lower()
    crisis = str(candidate_data.get('crisis_conflict', '')).strip().lower()
    notes = str(candidate_data.get('additional_notes', '')).strip().lower()

    # 1. TOPLULUK & TEKNOFEST DENEYİMİ (0 - 25)
    # ------------------------------------------------
    deneyim_puan = 0
    # Topluluk bileşeni (max 13)
    if any(w in comm for w in ['başkan', 'kaptan', 'yönetim', 'kurucu', 'lider', 'organizasyon birimi', 'koordinatör', 'aktif görev']):
        deneyim_puan += 12
    elif any(w in comm for w in ['aiesec', 'ieee', 'türkmsic', 'emsa', 'topluluğunda', 'kulübünde', 'görev aldım', 'aktif', 'üyesiyim', 'üyeydim', 'bulundum']):
        deneyim_puan += 9
    elif any(w in comm for w in ['lisede', 'katıldım', 'bulundum', 'etkinlik']):
        deneyim_puan += 6
    elif any(w in comm for w in ['hayır', 'olmadı', 'hyr', 'yok', '-']) or len(comm) < 3:
        deneyim_puan += 2
    else:
        deneyim_puan += 5

    # TEKNOFEST bileşeni (max 12)
    if any(w in tekno for w in ['ödül', 'birincilik', 'derece', 'finalist', 'kaptan']):
        deneyim_puan += 12
    elif any(w in tekno for w in ['eğitim teknolojileri', 'insansız hava', 'roket', 'yarışma', 'katıldık', 'yarıştım', 'proje yaptım', 'tübitak', 'görev aldım', 'takımında']):
        deneyim_puan += 9
    elif any(w in tekno for w in ['gezi', 'ziyaret', 'seyirci', 'izleyici', 'gittim']):
        deneyim_puan += 5
    elif any(w in tekno for w in ['hayır', 'almadım', 'hyr', 'yok', 'maalesef']) or len(tekno) < 3:
        deneyim_puan += 2
    else:
        deneyim_puan += 4

    deneyim_puan = min(25, max(1, deneyim_puan))

    # 2. KRİZ YÖNETİMİ & TAKIM UYUMU (0 - 30)
    # ------------------------------------------------
    # Soru: "Yönetim kurulunda alınan bir karara katılmıyorsunuz fakat karar çoğunluk tarafından kabul edildi. Nasıl bir tutum sergilersiniz?"
    takim_uyumu_puan = 15

    # Çok olumsuz / Direnç gösteren / Sabotaj riski
    if any(w in crisis for w in ['savunurum', 'katılmam', 'direnirim', 'arkasında dururum', 'kendi görüşümü savunurum', 'itiraz ederim']):
        if any(w in crisis for w in ['yine de katılırım', 'çoğunluğa uyarım', 'saygı duyarım', 'desteklerim', 'uyum sağlarım']):
            takim_uyumu_puan = 21  # Fikrini söyler ama karara uyar
        else:
            takim_uyumu_puan = 8   # Alınan karara muhalefet edip direnebilir
    # Ciddiyetsiz / Tek karakter
    elif crisis in ['.', '-', '...', 'yok'] or len(crisis) < 3:
        takim_uyumu_puan = 4
    # Mükemmel denge: Görüşünü belirtir + Çoğunluk kararına saygı duyup sahiplenir
    elif any(w in crisis for w in ['gerekçe', 'fikrimi açıklar', 'nedenini', 'ifade ederim', 'belirtirim']) and any(w in crisis for w in ['saygı', 'uyarım', 'desteklerim', 'ortak', 'kararına uyarım', 'uyum', 'sahiplenirim', 'katkı']):
        takim_uyumu_puan = 28
    elif any(w in crisis for w in ['saygı duyarım', 'demokrasi', 'çoğunluğun kararına', 'ortak karar']):
        takim_uyumu_puan = 24
    elif any(w in crisis for w in ['kabul ederim', 'uyarım', 'çoğunluk ne derse', 'uyum sağlarım']):
        takim_uyumu_puan = 19
    elif any(w in crisis for w in ['yapacak bir şey yok', 'yapıcak bi şey yok', 'mecbur']):
        takim_uyumu_puan = 14
    else:
        takim_uyumu_puan = 17

    takim_uyumu_puan = min(30, max(2, takim_uyumu_puan))

    # 3. DEVAMLILIK & ZAMAN TAAHHÜDÜ (0 - 20)
    # ------------------------------------------------
    devamlilik_puan = 14
    if any(w in att for w in ['üniversite programımı buna göre planlayarak', 'kararlıyım', 'şeffaf bir iletişim', 'önceden bildirerek', 'en yüksek katılımı sağlamaya']):
        devamlilik_puan = 20
    elif any(w in att for w in ['ders saatlerimle çakışmadığı', 'ders programıma göre', 'yoğun ders haftaları haricinde', 'sınav haftama denk gelmediği', 'gelemediğim günler olabilir', 'çakışmadığı sürece']):
        devamlilik_puan = 11  # Şartlı katılım
    elif any(w in att for w in ['evet kesinlikle', 'sağlarım', 'sağlayabilirim', 'düzenli olarak', 'aksatmam']):
        devamlilik_puan = 16
    elif any(w in att for w in ['evet', 'tabiki', 'tabi ki']):
        devamlilik_puan = 14
    elif att in ['.', '-', 'yok'] or len(att) < 3:
        devamlilik_puan = 3
    else:
        devamlilik_puan = 12

    devamlilik_puan = min(20, max(2, devamlilik_puan))

    # 4. ÖZ FARKINDALIK & İLETİŞİM BECERİSİ (0 - 25)
    # ------------------------------------------------
    iletisim_puan = 15
    # Metin uzunluğu ve detay kalitesi
    words_count = len(strength.split())
    if words_count >= 15 and any(w in strength_lower for w in ['iletişim', 'analitik', 'sorumluluk', 'problem çözme', 'liderlik', 'disiplin', 'empati', 'zaman yönetimi']):
        iletisim_puan = 24
    elif words_count >= 6:
        iletisim_puan = 19
    elif words_count >= 2:
        iletisim_puan = 15
    elif strength_lower in ['.', '-', 'yok'] or len(strength_lower) < 2:
        iletisim_puan = 4
    else:
        iletisim_puan = 11

    # Genel form doluluk ve ciddiyet primi / cezası
    total_text_len = len(comm) + len(tekno) + len(strength) + len(att) + len(crisis)
    if total_text_len < 30:
        iletisim_puan = max(3, iletisim_puan - 6)
    elif total_text_len > 250:
        iletisim_puan = min(25, iletisim_puan + 2)

    iletisim_puan = min(25, max(2, iletisim_puan))

    toplam_puan = deneyim_puan + takim_uyumu_puan + devamlilik_puan + iletisim_puan

    # Nitelik Cümleleri ve Mülakat Sorusu Çıkarımı
    # Öne çıkan yön
    if deneyim_puan >= 18:
        one_cikan_yon = "Önceki topluluk organizasyonları ve TEKNOFEST/TÜBİTAK proje tecrübesiyle sahaya hızla adapte olabilecek potansiyelde."
    elif takim_uyumu_puan >= 26:
        one_cikan_yon = "Yönetim kurulu kararlarına karşı yapıcı tutumu ve yüksek takım bilinciyle uyumlu bir profil sergiliyor."
    elif devamlilik_puan >= 18:
        one_cikan_yon = "Toplantı ve etkinliklere yönelik sorumluluk bilinci ile zaman taahhüdü oldukça yüksek ve planlı."
    elif iletisim_puan >= 22:
        one_cikan_yon = "Öz farkındalığı gelişmiş, güçlü yönlerini net ifade edebilen ve iletişim becerileri kuvvetli bir aday."
    elif toplam_puan >= 65:
        one_cikan_yon = "Görev alma motivasyonu yüksek, dengeli ve öğrenmeye istekli bir yönetim kurulu üyesi adayı."
    else:
        one_cikan_yon = "Kulübe dahil olmak isteyen temel düzeyde ilgi ve motivasyona sahip bir aday."

    # Riskli / Şüpheli yön
    if takim_uyumu_puan <= 12:
        riskli_supheli_yon = "Yönetim kurulu ortak kararlarına karşı kendi fikrinde diretme ve takım içi hizipleşme/direnç yaratma riski taşıyor."
    elif devamlilik_puan <= 11:
        riskli_supheli_yon = "Ders programı veya sınav haftası çakışmalarında toplantı ve sorumlulukları ikinci plana atma eğilimi var."
    elif total_text_len < 40 or strength in ['.', '-']:
        riskli_supheli_yon = "Form sorularını tek kelimeler veya noktayla geçiştirmiş; motivasyon ve ciddiyet seviyesi sorgulanmalı."
    elif deneyim_puan <= 6:
        riskli_supheli_yon = "Geçmiş kulüp ve TEKNOFEST tecrübesinin olmaması, yönetim kurulu dinamiklerine alışma sürecini uzatabilir."
    elif 'yapacak bir şey yok' in crisis or 'mecbur' in crisis:
        riskli_supheli_yon = "Karar alma süreçlerinde inisiyatif almaktan kaçınıp aşırı pasif kalma riski taşıyor."
    else:
        riskli_supheli_yon = "Belirgin bir kritik riski bulunmamakla birlikte, yoğun dönemlerdeki iş yükü kaldırma kapasitesi gözlemlenmeli."

    # Mülakat Soru Önerisi
    if takim_uyumu_puan <= 12:
        mulakat_soru_onerisi = "Toplantıda senin kesinlikle karşı çıktığın bir proje kararı oy çokluğuyla kabul edildiğinde, bu projeyi sahada ekibinle birlikte canla başla uygular mısın, yoksa kenara mı çekilirsin?"
    elif devamlilik_puan <= 11:
        mulakat_soru_onerisi = "Final haftanda TEKNOFEST son teslimi veya acil bir kriz toplantısı denk gelirse zamanını nasıl yönetir ve kulübü yarı yolda bırakmazsın?"
    elif total_text_len < 40:
        mulakat_soru_onerisi = "Başvuru formundaki soruları oldukça kısa yanıtlamışsın; TEKNOFEST Yönetim Kurulu'nda yer almayı gerçekten ne kadar istiyorsun ve bize haftada kaç saatini ayırabilirsin?"
    elif deneyim_puan >= 18:
        mulakat_soru_onerisi = "Önceki proje ve topluluk deneyimlerinde yaşadığın en büyük kriz neydi ve bu tecrübeni bizim TEKNOFEST ekibimizde somut olarak hangi süreçte kullanacaksın?"
    elif 'aiesec' in comm or 'türkmsic' in comm or 'ieee' in comm:
        mulakat_soru_onerisi = "Daha önce yer aldığın uluslararası/büyük kulüpteki çalışma kültürü ile bir TEKNOFEST teknoloji kulübü yönetiminin farklarını nasıl değerlendiriyorsun?"
    else:
        mulakat_soru_onerisi = "Yönetim kuruluna seçilirsen ilk 3 ay içinde TEKNOFEST yarışmacılarımıza veya kulüp üyelerimize yönelik somut olarak hangi projeyi veya etkinliği hayata geçirirsin?"

    return {
        "deneyim_puan": int(deneyim_puan),
        "takim_uyumu_puan": int(takim_uyumu_puan),
        "devamlilik_puan": int(devamlilik_puan),
        "iletisim_puan": int(iletisim_puan),
        "toplam_puan": int(toplam_puan),
        "one_cikan_yon": one_cikan_yon,
        "riskli_supheli_yon": riskli_supheli_yon,
        "mulakat_soru_onerisi": mulakat_soru_onerisi
    }

def main():
    parser = argparse.ArgumentParser(description="TEKNOFEST Yönetim Kurulu Aday Değerlendirme Aracı")
    parser.add_argument("--input", default=None, help="Girdi CSV dosyası yolu")
    parser.add_argument("--output", default="degerlendirilmis_basvurular.csv", help="Çıktı CSV dosyası yolu")
    parser.add_argument("--api-key", default=None, help="Google Gemini API Anahtarı")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini Model Adı")
    parser.add_argument("--force-heuristic", action="store_true", help="API key olsa dahi kural tabanlı motoru çalıştır")
    args = parser.parse_args()

    # 1. Girdi dosyasını bul ve oku
    input_file = args.input or get_input_file()
    print(f"[+] Başvuru dosyası okunuyor: {input_file}")
    
    # UTF-8 veya alternatif encoding ile oku
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding='utf-8-sig')

    print(f"[+] Toplam ham satır sayısı: {len(df)}")

    # Sütunları dinamik ve güvenli haritalandır
    mapped_cols = {}
    for key in COL_PATTERNS.keys():
        found = find_column(df, key)
        if found:
            mapped_cols[key] = found
        else:
            print(f"[!] Uyarı: '{key}' anahtarı için tam sütun eşleşmesi bulunamadı.")

    name_col = mapped_cols.get('name')
    if not name_col:
        # Fallback: 1. indeks sütun
        name_col = df.columns[1]
        mapped_cols['name'] = name_col

    # Boş isimli satırları filtrele
    df_clean = df.dropna(subset=[name_col]).copy()
    print(f"[+] Geçerli başvuru sayısı: {len(df_clean)}")

    # 2. LLM / Gemini istemcisini hazırla
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    use_llm = False
    client = None

    if api_key and not args.force_heuristic:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            use_llm = True
            print(f"[+] Gemini API Anahtarı algılandı. LLM Modeli: {args.model}")
        except Exception as e:
            print(f"[!] Gemini istemcisi başlatılamadı ({e}), kural tabanlı motor kullanılacak.")
            use_llm = False
    else:
        if args.force_heuristic:
            print("[i] Kural ve semantik değerlendirme motoru seçildi (--force-heuristic).")
        else:
            print("[i] GEMINI_API_KEY bulunamadı. Yüksek hassasiyetli Kural & Semantik Analiz motoru devreye alınıyor.")

    # 3. Tüm adayları değerlendir
    results = []
    total_candidates = len(df_clean)

    for idx, (_, row) in enumerate(df_clean.iterrows()):
        candidate_dict = {}
        for key, original_col in mapped_cols.items():
            candidate_dict[key] = "" if pd.isna(row.get(original_col)) else str(row.get(original_col))

        cand_name = candidate_dict.get('name', f'Aday {idx+1}')
        print(f"[{idx+1}/{total_candidates}] Değerlendiriliyor: {cand_name}...", end=" ", flush=True)

        eval_res = None
        eval_method = "Kural & Semantik Analiz"

        if use_llm and client:
            try:
                eval_res = evaluate_with_gemini(client, args.model, candidate_dict)
                eval_method = f"Gemini LLM ({args.model})"
            except Exception as e:
                print(f"[LLM Hatası: {e} -> Heuristic Fallback]", end=" ")
                eval_res = evaluate_heuristically(candidate_dict)
        else:
            eval_res = evaluate_heuristically(candidate_dict)

        eval_res["degerlendirme_kaynagi"] = eval_method
        results.append(eval_res)
        print(f"-> Toplam Puan: {eval_res['toplam_puan']}")

    # 4. Sonuçları DataFrame'e ekle ve kaydet
    res_df = pd.DataFrame(results)
    final_df = pd.concat([df_clean.reset_index(drop=True), res_df], axis=1)

    # Kolay erişim için standart takma isim sütunları da ekleyelim
    for std_name, orig_col in mapped_cols.items():
        if orig_col in final_df.columns and f"std_{std_name}" not in final_df.columns:
            final_df[f"std_{std_name}"] = final_df[orig_col]

    final_df.to_csv(args.output, index=False, encoding='utf-8-sig')
    print(f"\n[✓] Değerlendirme başarıyla tamamlandı!")
    print(f"[✓] Çıktı dosyası kaydedildi: {os.path.abspath(args.output)}")
    print(f"[✓] Ortalama Puan: {final_df['toplam_puan'].mean():.2f}")
    print(f"[✓] 70+ Puan Alan Aday Sayısı: {(final_df['toplam_puan'] >= 70).sum()} / {len(final_df)}")

if __name__ == "__main__":
    main()
