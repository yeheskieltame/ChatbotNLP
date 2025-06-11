# Mata Kopian - Chatbot NLP

Aplikasi Chatbot Telegram dengan fitur NLP (Natural Language Processing) untuk "Mata Kopian" yang memungkinkan pengguna memesan makanan dan minuman melalui chat. Dilengkapi dengan dashboard admin untuk mengelola menu.

## Kontributor

Dibuat oleh:
- Yeheskiel Yunus Tame - 71220903              
- P. Harimurti Adi Bagaskara - 71220918
- Nahason Christian Ade Herlambang - 71220888

## Fitur Utama

### 1. Telegram Chatbot
- Melihat menu makanan dan minuman
- Memesan item dengan deteksi bahasa alami
- Simulasi proses pemesanan lengkap (pemilihan jumlah, opsi makan, dan metode pembayaran)
- Konfirmasi pesanan dengan struk digital

### 2. Dashboard Admin
- Menambahkan item menu baru (makanan/minuman)
- Mengedit item menu yang sudah ada
- Menghapus item menu
- Mengubah informasi pemesanan
- Tampilan yang responsif dan user-friendly

### 3. NLP (Natural Language Processing)
- Deteksi intent pengguna (pertanyaan harga, pemesanan, sapaan, dll)
- Ekstraksi entitas (nama item, jumlah)
- Konteks percakapan yang berkelanjutan
- Pengenalan referensi (misalnya "pesan itu" untuk item yang baru disebutkan)

## Struktur Proyek

```
ChatbotNLP/
├── config.py                # Konfigurasi aplikasi (token bot)
├── requirements.txt         # Dependensi Python
├── README.md                # Dokumentasi proyek
├── admin_dashboard/
│   └── app.py               # Aplikasi Streamlit untuk admin dashboard
├── bot/
│   ├── telegram_bot.py      # Implementasi bot Telegram
│   └── nlp_utils.py         # Utilitas NLP untuk memproses bahasa alami
├── data/
│   └── menu_data.json       # Data menu dalam format JSON
└── modules/
    └── menu_manager.py      # Pengelolaan data menu (CRUD)
```

## Cara Menggunakan

### 1. Persiapan Awal

1. Clone repository ini:
   ```bash
   git clone https://github.com/yeheskieltame/ChatbotNLP.git
   cd ChatbotNLP
   ```

2. Install semua dependensi yang diperlukan:
   ```bash
   pip install -r requirements.txt
   ```

3. Pastikan token bot Telegram sudah dikonfigurasi di `config.py`:
   ```python
   # config.py
   TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   ```

### 2. Menjalankan Admin Dashboard

Dashboard admin digunakan untuk mengelola menu kafe:

```bash
streamlit run admin_dashboard/app.py
```

Dashboard akan terbuka di browser Anda (biasanya di http://localhost:8501).

#### Fitur Dashboard Admin:
- **Tab Tambah Item & Info Pesan**: Menambahkan item menu baru dan mengedit informasi pemesanan
- **Tab Makanan**: Melihat, mengedit, atau menghapus item makanan
- **Tab Minuman**: Melihat, mengedit, atau menghapus item minuman

### 3. Menjalankan Bot Telegram

Bot Telegram memungkinkan pelanggan memesan melalui chat:

```bash
python bot/telegram_bot.py
```

#### Cara Menggunakan Bot:
1. Mulai percakapan dengan mengirim `/start`
2. Lihat menu dengan mengirim `/menu`
3. Tanyakan harga dengan mengirim "Berapa harga [nama item]?"
4. Pesan makanan/minuman dengan mengirim "Saya mau pesan [nama item]"
5. Ikuti panduan chatbot untuk menyelesaikan pesanan

#### Contoh Alur Pemesanan:
1. "Saya mau pesan Nasi Goreng Mata Kopian"
2. Bot akan bertanya jumlah: "Mau pesan berapa banyak/porsi?"
3. Jawab dengan angka: "2"
4. Bot akan bertanya opsi makan: "Mau dimakan di tempat atau dibungkus?"
5. Pilih: "Makan di tempat"
6. Bot akan bertanya metode pembayaran: "Silakan pilih metode pembayaran: E-Wallet atau Cash di Kasir?"
7. Pilih: "E-Wallet"
8. Bot akan memberikan struk pesanan dengan detail pembayaran

## Penjelasan Metode NLP yang Digunakan

Aplikasi ini menggunakan beberapa metode NLP berbasis aturan (rule-based) untuk memahami dan memproses bahasa alami pengguna:

### 1. Intent Recognition (Pengenalan Intent)
- **Metode:** Rule-based keyword matching
- **Penjelasan:**
  - Setiap intent (misal: lihat_menu, tanya_harga, info_pemesanan, sapaan, dsb) memiliki daftar kata kunci.
  - Skor diberikan jika keyword ditemukan dalam pesan pengguna:
    - Skor 2 jika keyword cocok sebagai kata utuh
    - Skor 1 jika keyword hanya sebagai substring
  - Intent dengan skor tertinggi dipilih sebagai hasil.
- **Rumus:**
  ```python
  score(intent) = jumlah keyword intent yang cocok di pesan
  intent_terpilih = intent dengan score tertinggi (score > 0)
  ```

### 2. Entity Extraction (Ekstraksi Entitas)
- **Metode:** String matching dan regular expression
- **Penjelasan:**
  - Nama item diekstrak dengan mencocokkan nama menu pada pesan pengguna.
  - Kuantitas diekstrak dengan regex angka atau kata bilangan ("satu", "dua", dst).
- **Rumus:**
  ```python
  quantity = int(angka_pertama_ditemukan) 
  # atau
  quantity = mapping_kata_ke_angka[kata_angka_pertama_ditemukan]
  item = item_menu jika nama_item_menu in pesan_pengguna
  ```

### 3. Text Preprocessing (Pra-pemrosesan Teks)
- **Metode:** Lowercasing, hapus tanda baca, trim whitespace
- **Penjelasan:**
  - Semua teks pengguna diproses dengan: lowercase, hapus tanda baca, dan spasi berlebih.

### 4. Context Management (Manajemen Konteks)
- **Metode:** State machine & context dictionary per user
- **Penjelasan:**
  - Setiap user memiliki state (misal: GENERAL, AWAITING_QUANTITY, dst)
  - Konteks seperti item terakhir yang ditanyakan, pesanan sementara, dsb, disimpan dalam dictionary `user_contexts`
  - Bot dapat mengenali referensi seperti "itu", "item tadi" dengan melihat konteks sebelumnya

> **Catatan:** Semua proses NLP di aplikasi ini menggunakan metode rule-based (berbasis aturan/kata kunci), tanpa model machine learning/statistik.

## Troubleshooting

- **Bot tidak merespon**: Pastikan `TELEGRAM_BOT_TOKEN` valid dan bot sedang berjalan
- **Data menu tidak muncul**: Periksa file `data/menu_data.json` dan pastikan formatnya benar
- **Dashboard tidak dapat memperbarui menu**: Periksa izin penulisan file di direktori `data/`

## Pengembangan Lebih Lanjut

- Integrasi dengan sistem pembayaran nyata
- Fitur delivery yang berfungsi
- Implementasi machine learning untuk pemahaman bahasa yang lebih baik
- Riwayat pesanan dan manajemen pelanggan
- Notifikasi dan promosi otomatis
