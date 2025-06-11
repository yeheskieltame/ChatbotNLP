# bot/nlp_utils.py
import re
import sys 
import os 

try:
    from modules.menu_manager import get_menu
except ImportError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.dirname(current_script_dir) 
    if project_root_dir not in sys.path:
        sys.path.append(project_root_dir)
    from modules.menu_manager import get_menu


# --- Definisi Keyword untuk Intent ---
INTENT_KEYWORDS = {
    "lihat_menu": [
        "menu", "daftar makanan", "daftar minuman", "list makanan", "list minuman",
        "apa aja menunya", "ada apa aja", "lihat menu", "tampilkan menu", "menu dong", 
        "menu hari ini", "menunya apa", "kasih lihat menu", "bisa lihat menu",
        "bisa liat menu", "liatin menu", "makanannya apa aja", "minumannya apa aja",
        "menunya ada apa aja sih", "apa aja yang ada di menu", "menu apa aja yang ada",
        "kasi liat menu", "kasi tau menu", "kasih menu dong", "show me the menu",
        "show menu", "tampilkan daftar menu", "lihat daftar menu", "menu apa aja"
    ],
    "tanya_harga": [
        "harga", "berapa", "rp", "biaya", "harganya", "berapaan", "price",
        "berapa duitnya", "harganya berapa", "berapa ya", "berapa sih", "berapa rupiah",
        "tarif", "fee", "brp ya", "pinten nggih", "piro", "how much", "berapa ya harganya",
        "berapa harganya", "berapa sih harganya"
    ],
    "info_pemesanan": [ 
        "pesan", "order", "pemesanan", "cara pesan", "gimana pesannya", "mau pesan", "mau order",
        "beli", "saya mau", "bisa pesan", "bisa order", "order dong", "pesenin", "bisa beli",
        "pesan sekarang", "booking", "mau beli", "aku mau", "pesan yuk", "bisa booking",
        "mau order dong", "mau pesan dong", "gue mau order", "gue mau pesan", "aku pesen dong"
    ],
    "sapaan": [
        "halo", "hai", "hi", "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
        "pagi", "siang", "sore", "malam", "hei", "heii", "heyyo", "met pagi", "met siang", 
        "met sore", "met malam", "hello", "konnichiwa", "ohayou", "konbanwa", "hallo", "haloo",
        "hey", "halo halo", "hai hai", "hi hi"
    ],
    "terima_kasih": [
        "makasih", "terima kasih", "thanks", "thank you", "nuhun", "suwun", "matur nuwun", "nuwun"
        "trims", "makasih ya", "thank u", "tengkyu", "makasii", "makasih banyak", "thx", 
        "arigatou", "tenkyu", "makasih loh", "makasi banget", "makaci", "makacih", "ty", "trims ya",
        "thx ya", "thx bgt", "thank you so much", "thanks a lot", "thank you very much",
        "terima kasih banyak", "makasih banget loh", "makacihh ya"
    ],
    "tanya_bot": [ 
        "kamu siapa", "ini siapa", "ini bot apa", "apa yang bisa kamu lakukan",
        "lu siapa", "siapa kamu", "bot apa ini", "bisa ngapain", "apa tugas kamu",
        "bot bisa apa", "kenalin dong", "fungsi kamu apa"
    ],
    "konfirmasi_ya": [ # Berguna untuk konfirmasi dalam alur state
        "ya", "iya", "betul", "benar", "ok", "oke", "baik", "sip", "setuju", "lanjut", "mau",
        "yup", "yoi", "yo", "oke banget", "ya dong", "okelah", "boleh", "lets go", "gas", 
        "gasskeun", "yuk", "cus", "oke siap", "yess", "iya dong", "oke sip", "oke deh",
        "oke aja", "oke yuk", "oke gas", "oke gasskeun", "oke lets go", "oke yuk gas",
        "boleh dong", "sip gas", "yuhuu"
    ],
    "konfirmasi_tidak": [ # Berguna untuk konfirmasi dalam alur state
        "tidak", "bukan", "jangan", "ga", "gak", "nggak", "batal", "cancel", "gak jadi",
        "tidak jadi", "enggak", "skip", "ga usah", "nggak deh", "nanti aja",
        "ga dulu", "nanti aja deh", "gajadi deh", "ga dulu deh", "skip dulu", 
        "ntar aja ya", "gajadi ya", "ga jadi deh", "skip aja deh", "besok aja deh", 
        "ga usah deh", "cancel aja deh", "nanti dulu"
    ]
}

def preprocess_text(text):
    """Membersihkan dan menormalkan teks."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text) 
    text = text.strip()
    return text

def recognize_intent(text):
    """Mengenali intent pengguna berdasarkan keyword."""
    processed_text = preprocess_text(text)
    if not processed_text:
        return None, 0

    intent_scores = {intent: 0 for intent in INTENT_KEYWORDS}
    best_intent = None
    highest_score = 0

    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', processed_text):
                score += 2
            elif keyword in processed_text:
                score += 1
        
        if score > highest_score:
            highest_score = score
            best_intent = intent
        elif score == highest_score and score > 0: # Jika skor sama, bisa ambil yang pertama atau lainnya
            pass 

    if highest_score < 1: # Threshold minimal skor untuk dianggap sebagai intent
        return None, 0
        
    return best_intent, highest_score


def extract_entities_item_name(text):
    """Mengekstrak nama item menu dari teks."""
    processed_text = preprocess_text(text)
    menu = get_menu(force_reload=False) 
    
    # Perbaikan: Ambil semua item dari semua kategori yang ada
    all_items = []
    
    # Daftar kategori yang sesuai dengan struktur menu
    categories = ["es_kopi", "non_kopi", "espresso_based", "refreshment", "others", "pastry"]
    
    for category in categories:
        if menu.get(category):
            all_items.extend(menu[category])

    found_items_data = []
    sorted_items_by_name_len = sorted(all_items, key=lambda x: len(x.get("nama","")), reverse=True)

    for item_data in sorted_items_by_name_len:
        item_name_processed = preprocess_text(item_data.get("nama", ""))
        if item_name_processed and item_name_processed in processed_text:
            is_substring_of_found = False
            for fi_data in found_items_data:
                if item_name_processed in preprocess_text(fi_data.get("nama","")):
                    is_substring_of_found = True
                    break
            if not is_substring_of_found:
                found_items_data.append(item_data) 

    if not found_items_data:
        return None
    
    return found_items_data[0]

ANGKA_TEKS_KE_INT = {
    "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10,
}

def extract_quantity(text):
    """Mengekstrak kuantitas (angka) dari teks."""
    processed_text = preprocess_text(text) 
    if not processed_text:
        return None

    match_digit = re.search(r'\b\d+\b', processed_text)
    if not match_digit: 
        match_digit = re.search(r'\d+', processed_text)

    if match_digit:
        try:
            return int(match_digit.group(0))
        except ValueError:
            pass

    words_in_text = processed_text.split()
    for kata, angka in ANGKA_TEKS_KE_INT.items():
        if kata in words_in_text: 
            return angka
            
    return None

if __name__ == '__main__':
    print("--- Pengujian NLP Utils ---")
    # ... (blok pengujian bisa Anda uncomment jika ingin menjalankan file ini sendiri) ...
    pass