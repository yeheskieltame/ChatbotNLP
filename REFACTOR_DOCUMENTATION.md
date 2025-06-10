# Dokumentasi Struktur Bot Kafe Cerita

## Overview Pemecahan File

Aplikasi bot Telegram Kafe Cerita telah dipecah menjadi 4 modul utama untuk meningkatkan keterbacaan dan kemudahan maintenance:

```
bot/
├── telegram_bot.py      # Main entry point & router
├── user_context.py      # State & context management
├── commands.py          # Command handlers (/start, /menu)
├── message_handlers.py  # State-based message handlers
└── nlp_utils.py        # NLP utilities (sudah ada)
```

## File Details

### 1. `bot/telegram_bot.py` (MAIN FILE)
**Tanggung Jawab:** Entry point utama dan router pesan
- Setup aplikasi Telegram Bot
- Main message handler yang mengarahkan ke handler yang tepat
- Error handling tingkat atas
- Fungsi `main()` untuk menjalankan bot

**Key Functions:**
- `handle_message()` - Router utama semua pesan text
- `main()` - Setup dan jalankan bot

### 2. `bot/user_context.py`
**Tanggung Jawab:** Manajemen state dan context pengguna
- Konstanta state (STATE_GENERAL, STATE_AWAITING_QUANTITY, dll)
- Storage context pengguna (`user_contexts`)
- Functions untuk manipulasi state dan order data

**Key Functions:**
- `get_user_state()` / `set_user_state()` - Manajemen state
- `get_order_details()` / `update_order_field()` - Manipulasi pesanan
- `add_item_to_current_order()` - Tambah item ke pesanan
- `calculate_total_price()` - Hitung total harga
- `generate_order_id()` - Generate ID pesanan unik
- `reset_order_details()` - Reset pesanan

### 3. `bot/commands.py`
**Tanggung Jawab:** Handler untuk semua command bot
- Handler untuk `/start` command
- Handler untuk `/menu` command
- Logic formatting menu dengan kategori dan emoji

**Key Functions:**
- `start_command()` - Welcome message dan reset context
- `menu_command()` - Tampilkan menu lengkap dengan format rapi

### 4. `bot/message_handlers.py`
**Tanggung Jawab:** Handler pesan berdasarkan state conversation
- Handler untuk setiap state pemesanan
- Intent processing untuk state GENERAL
- Receipt generation untuk pesanan selesai

**Key Functions:**
- `handle_quantity_input()` - Input jumlah item
- `handle_dining_option_input()` - Pilih dine-in/takeaway
- `handle_takeout_type_input()` - Pilih pickup/delivery
- `handle_payment_method_input()` - Pilih metode bayar
- `handle_general_intent()` - Intent recognition state GENERAL
- `generate_receipt()` - Generate struk pesanan
- `handle_invalid_state_input()` - Handler input tidak valid

## Cara Menjalankan Bot

Cara menjalankan bot **TETAP SAMA** seperti sebelumnya:

```bash
cd /Users/kiel/ChatbotNLP
python3 bot/telegram_bot.py
```

## Keuntungan Pemecahan

### ✅ **Organizatisi yang Lebih Baik**
- Setiap file punya tanggung jawab spesifik
- Mudah mencari function tertentu
- Kode lebih terstruktur dan rapi

### ✅ **Kemudahan Maintenance**
- Bug di fitur tertentu mudah dilacak
- Perubahan pada satu fitur tidak affect yang lain
- Testing bisa dilakukan per module

### ✅ **Readability & Understanding**
- Setiap file ukurannya lebih kecil
- Function names yang descriptive
- Komentar yang jelas di setiap function

### ✅ **Reusability**
- Functions bisa digunakan ulang
- Module bisa diimport secara terpisah
- Scaling aplikasi lebih mudah

## Import Dependencies

Setiap module mengimport hanya yang dibutuhkan:
- `user_context.py` - Standalone, hanya butuh datetime dan logging
- `commands.py` - Import dari user_context dan modules.menu_manager  
- `message_handlers.py` - Import dari user_context, nlp_utils, dan modules
- `telegram_bot.py` - Import semua handler dari module lain

## State Flow (Tidak Berubah)

Flow conversation tetap sama:
```
STATE_GENERAL -> 
STATE_AWAITING_QUANTITY -> 
STATE_AWAITING_DINING_OPTION -> 
STATE_AWAITING_TAKEOUT_TYPE (jika takeaway) ->
STATE_AWAITING_PAYMENT_METHOD -> 
STATE_GENERAL (selesai)
```

## Key Features (Tetap Sama)

✅ Context expiry management (30 menit)
✅ Referential keywords ("itu", "yang tadi")  
✅ Order management dengan multiple items
✅ NLP intent recognition
✅ Receipt generation dengan order ID
✅ Error handling & fallback messages
✅ Logging comprehensive

## Notes

- Semua fitur dan fungsi bot **100% sama** dengan versi sebelumnya
- Hanya organisasi kode yang berubah untuk kemudahan development
- Performance tidak terpengaruh karena hanya pemecahan logical
- Compatible dengan semua dependencies yang sudah ada
