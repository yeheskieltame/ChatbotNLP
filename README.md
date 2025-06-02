# Kafe Cerita - Chatbot NLP

Aplikasi Chatbot Telegram dengan fitur NLP (Natural Language Processing) untuk "Kafe Cerita" yang memungkinkan pengguna memesan makanan dan minuman melalui chat. Dilengkapi dengan dashboard admin untuk mengelola menu.

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
   git clone https://github.com/username/ChatbotNLP.git
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
cd /Users/kiel/Desktop/ChatbotNLP
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
cd /Users/kiel/Desktop/ChatbotNLP
python bot/telegram_bot.py
```

#### Cara Menggunakan Bot:
1. Mulai percakapan dengan mengirim `/start`
2. Lihat menu dengan mengirim `/menu`
3. Tanyakan harga dengan mengirim "Berapa harga [nama item]?"
4. Pesan makanan/minuman dengan mengirim "Saya mau pesan [nama item]"
5. Ikuti panduan chatbot untuk menyelesaikan pesanan

#### Contoh Alur Pemesanan:
1. "Saya mau pesan Nasi Goreng Cerita"
2. Bot akan bertanya jumlah: "Mau pesan berapa banyak/porsi?"
3. Jawab dengan angka: "2"
4. Bot akan bertanya opsi makan: "Mau dimakan di tempat atau dibungkus?"
5. Pilih: "Makan di tempat"
6. Bot akan bertanya metode pembayaran: "Silakan pilih metode pembayaran: E-Wallet atau Cash di Kasir?"
7. Pilih: "E-Wallet"
8. Bot akan memberikan struk pesanan dengan detail pembayaran

## Fitur NLP

Bot ini menggunakan teknik NLP sederhana untuk memahami bahasa alami:

1. **Intent Recognition**: Mengenali maksud pengguna dari pesan teks
   - lihat_menu, tanya_harga, info_pemesanan, sapaan, dll.

2. **Entity Extraction**: Mengekstrak informasi spesifik dari pesan
   - Nama item menu
   - Jumlah/kuantitas pesanan

3. **Context Management**: Menjaga konteks percakapan
   - Mengingat item terakhir yang ditanyakan
   - Mengelola alur pemesanan dengan state machine

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