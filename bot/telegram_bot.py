# bot/telegram_bot.py
import logging
import sys
import os
from datetime import datetime, timedelta

# Tambahkan path project root ke sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

try:
    from config import TELEGRAM_BOT_TOKEN
    from modules.menu_manager import get_menu, get_item_by_name, get_info_pemesanan
    from bot.nlp_utils import recognize_intent, extract_entities_item_name, extract_quantity, preprocess_text
except ImportError as e:
    print(f"Gagal melakukan impor: {e}")
    print("Pastikan file config.py, modules/menu_manager.py, dan bot/nlp_utils.py tersedia dan struktur direktori benar.")
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)
print(logger)

# --- State Percakapan untuk Pemesanan ---
STATE_GENERAL = "GENERAL"
STATE_AWAITING_QUANTITY = "AWAITING_QUANTITY"
STATE_AWAITING_DINING_OPTION = "AWAITING_DINING_OPTION"
STATE_AWAITING_TAKEOUT_TYPE = "AWAITING_TAKEOUT_TYPE"
STATE_AWAITING_PAYMENT_METHOD = "AWAITING_PAYMENT_METHOD"
# STATE_AWAITING_CASH_CONFIRMATION = "AWAITING_CASH_CONFIRMATION" # Belum digunakan

# --- Manajemen Konteks Pengguna ---
user_contexts = {} 
CONTEXT_EXPIRY_MINUTES = 30 

REFERENTIAL_KEYWORDS = ["itu", "item itu", "item tersebut", "yang tadi", "yang barusan", "ini"]

def get_user_state(user_id):
    if user_id in user_contexts:
        context_data = user_contexts[user_id]
        if 'timestamp' in context_data and \
           (datetime.now() - context_data['timestamp'] < timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
            return context_data.get('state', STATE_GENERAL)
        else: 
            logger.info(f"Konteks untuk user {user_id} kadaluarsa. Dihapus.")
            if user_id in user_contexts: del user_contexts[user_id] 
            return STATE_GENERAL
    return STATE_GENERAL


def set_user_state(user_id, state):
    now = datetime.now()
    if user_id not in user_contexts or \
       (now - user_contexts[user_id].get('timestamp', datetime.min) >= timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
        user_contexts[user_id] = {
            'state': state,
            'order_details': {
                'items': [], 
                'current_item_to_add_data': None, 
                'dining_option': None,
                'takeout_type': None,
                'payment_method': None,
                'total_price': 0,
                'order_id': None
            },
            'last_inquired_item_data': None, 
            'timestamp': now
        }
        logger.info(f"Konteks baru diinisialisasi untuk user {user_id}. State: {state}")
    else:
        user_contexts[user_id]['state'] = state
        user_contexts[user_id]['timestamp'] = now
    
    logger.info(f"State untuk user {user_id} diatur ke {state}. Detail Konteks: {user_contexts[user_id]}")


def get_order_details(user_id):
    if user_id in user_contexts and get_user_state(user_id) != STATE_GENERAL: # Pastikan konteks valid
        # Inisialisasi order_details jika tidak ada (seharusnya sudah oleh set_user_state)
        if 'order_details' not in user_contexts[user_id]:
             user_contexts[user_id]['order_details'] = {
                'items': [], 'current_item_to_add_data': None, 'dining_option': None,
                'takeout_type': None, 'payment_method': None, 'total_price': 0, 'order_id': None
            }
        return user_contexts[user_id].get('order_details', {})
    return {} # Kembalikan dict kosong jika tidak ada konteks yang sesuai

def set_current_item_to_add(user_id, item_data):
    if user_id in user_contexts: # Pastikan konteks ada
        # Pastikan order_details ada
        if 'order_details' not in user_contexts[user_id]:
             user_contexts[user_id]['order_details'] = {
                'items': [], 'current_item_to_add_data': None, 'dining_option': None,
                'takeout_type': None, 'payment_method': None, 'total_price': 0, 'order_id': None
            }
        user_contexts[user_id]['order_details']['current_item_to_add_data'] = item_data
        user_contexts[user_id]['timestamp'] = datetime.now() 
        logger.info(f"User {user_id}: Item '{item_data['nama']}' disiapkan untuk penambahan kuantitas.")


def add_item_to_current_order(user_id, quantity):
    if user_id not in user_contexts:
        logger.warning(f"User {user_id} tidak memiliki konteks saat mencoba menambah item.")
        return False
        
    order_details = user_contexts[user_id].get('order_details')
    if not order_details: # Safety check
        logger.error(f"User {user_id}: 'order_details' tidak ada di konteks saat add_item_to_current_order.")
        return False

    item_to_add_data = order_details.get('current_item_to_add_data')

    if not item_to_add_data:
        logger.warning(f"User {user_id}: Tidak ada 'current_item_to_add_data' saat menambah kuantitas.")
        return False

    found = False
    if 'items' not in order_details: order_details['items'] = [] # Inisialisasi jika belum ada

    for item_in_order in order_details['items']:
        if item_in_order['item_data']['id'] == item_to_add_data['id']:
            item_in_order['quantity'] += int(quantity)
            found = True
            break
    if not found:
        order_details['items'].append({'item_data': item_to_add_data, 'quantity': int(quantity)})
    
    order_details['current_item_to_add_data'] = None 
    user_contexts[user_id]['timestamp'] = datetime.now()
    calculate_total_price(user_id)
    logger.info(f"User {user_id}: Item '{item_to_add_data['nama']}' x{quantity} berhasil ditambahkan/diupdate ke pesanan.")
    return True


def calculate_total_price(user_id):
    order_details = get_order_details(user_id) # get_order_details sudah menghandle jika tidak ada
    if order_details and order_details.get('items'):
        total = sum(item['item_data']['harga'] * item['quantity'] for item in order_details['items'])
        if user_id in user_contexts and 'order_details' in user_contexts[user_id]: # Pastikan target ada
            user_contexts[user_id]['order_details']['total_price'] = total
            logger.info(f"User {user_id}: Total harga pesanan dihitung Rp{total:,}")
            return total
    return 0

def generate_order_id(user_id):
    now = datetime.now()
    user_part = str(user_id)[-4:] 
    random_part = str(os.urandom(2).hex().upper())
    return f"KC{now.strftime('%y%m%d')}-{user_part}{random_part}"

def reset_order_details(user_id):
    """Membersihkan detail pesanan setelah selesai atau dibatalkan."""
    if user_id in user_contexts and 'order_details' in user_contexts[user_id]:
        user_contexts[user_id]['order_details'] = {
            'items': [], 
            'current_item_to_add_data': None,
            'dining_option': None,
            'takeout_type': None,
            'payment_method': None,
            'total_price': 0,
            'order_id': None
        }
        logger.info(f"Order details untuk user {user_id} telah direset.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    set_user_state(user_id, STATE_GENERAL) 
    reset_order_details(user_id) # Bersihkan sisa order jika ada
    await update.message.reply_html(
        rf"Halo {user.mention_html()}! Selamat datang di Kafe Cerita. Ada yang bisa saya bantu? "
        "Anda bisa tanya tentang menu, harga, atau cara pemesanan.",
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # set_user_state(user_id, STATE_GENERAL) # Melihat menu tidak harus mereset state order
    menu = get_menu(force_reload=True)
    response = "☕ *Menu Kafe Cerita* ☕\n\n"
    
    # Mapping kategori dengan emoji dan nama yang user-friendly
    categories = {
        "es_kopi": {"name": "Es Kopi", "emoji": "☕"},
        "non_kopi": {"name": "Non Kopi", "emoji": "🍵"},
        "espresso_based": {"name": "Espresso Based", "emoji": "🫕"},
        "refreshment": {"name": "Refreshment", "emoji": "🍸"},
        "others": {"name": "Others", "emoji": "🥤"},
        "pastry": {"name": "Pastry", "emoji": "🥐"}
    }
    
    # Tampilkan setiap kategori
    for category_key, category_info in categories.items():
        items = menu.get(category_key, [])
        response += f"*{category_info['name']}* {category_info['emoji']}:\n"
        
        if items:
            for item in items:
                nama = item.get('nama', 'N/A')
                harga = item.get('harga', 0)
                deskripsi = item.get('deskripsi', '')
                
                # Format item dengan harga
                response += f"• {nama}: Rp{harga:,}"
                
                # Tambahkan deskripsi jika ada (opsional, bisa dihilangkan jika terlalu panjang)
                if deskripsi:
                    response += f"\n  _{deskripsi}_"
                response += "\n"
        else:
            response += f"_Belum ada menu {category_info['name'].lower()}._\n"
        
        response += "\n"
    
    # Tambahkan info pemesanan
    response += f"*Info Pemesanan* ℹ️:\n{get_info_pemesanan(force_reload=True)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    
    current_user_state = get_user_state(user_id)
    # Inisialisasi konteks jika belum ada (penting untuk user baru atau konteks kadaluarsa)
    if user_id not in user_contexts: # Jika get_user_state mengembalikan STATE_GENERAL karena kadaluarsa
        set_user_state(user_id, STATE_GENERAL) # Ini akan menginisialisasi struktur konteks
        current_user_state = STATE_GENERAL # Update variabel lokal

    logger.info(f"Pesan dari {user_first_name} (ID: {user_id}, State: {current_user_state}): {text}")

    # --- Logika berdasarkan State Percakapan ---
    if current_user_state == STATE_AWAITING_QUANTITY:
        order_details = get_order_details(user_id) # Sudah dihandle jika user_id tidak ada di user_contexts
        item_to_add_data = order_details.get('current_item_to_add_data') if order_details else None


        if not item_to_add_data:
            logger.warning(f"User {user_id} di state AWAITING_QUANTITY tapi 'current_item_to_add_data' kosong.")
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Maaf, sepertinya ada yang salah. Bisa sebutkan lagi item yang mau dipesan?")
            return

        qty = extract_quantity(text)
        if qty and qty > 0:
            if not add_item_to_current_order(user_id, qty): # Jika gagal tambah item (misal konteks error)
                 set_user_state(user_id, STATE_GENERAL)
                 reset_order_details(user_id)
                 await update.message.reply_text("Maaf, terjadi kendala saat memproses pesanan Anda. Silakan coba lagi.")
                 return

            order_details = get_order_details(user_id) # Ambil lagi untuk mendapatkan 'items' yang terupdate
            current_total = order_details.get('total_price', 0)
            
            item_names_in_order = []
            if order_details.get('items'):
                item_names_in_order = [f"{item['quantity']} {item['item_data']['nama']}" for item in order_details['items']]
            order_summary = ", ".join(item_names_in_order) if item_names_in_order else "Belum ada item"

            set_user_state(user_id, STATE_AWAITING_DINING_OPTION)
            await update.message.reply_text(
                f"Oke, {qty} {item_to_add_data['nama']} sudah ditambahkan. "
                f"Pesanan Anda saat ini: {order_summary} (Total sementara: Rp{current_total:,}).\n\n"
                "Mau dimakan di tempat atau dibungkus?"
            )
        else:
            await update.message.reply_text(f"Jumlah tidak valid, {user_first_name}. Mau pesan berapa banyak untuk {item_to_add_data['nama']}?")
        return

    elif current_user_state == STATE_AWAITING_DINING_OPTION:
        order_details = get_order_details(user_id)
        if not order_details or not order_details.get('items'):
            logger.warning(f"User {user_id} di state AWAITING_DINING_OPTION tapi tidak ada item di pesanan.")
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Maaf, terjadi kesalahan pada pesanan Anda. Bisa dimulai lagi?")
            return

        processed_text = preprocess_text(text)
        DINE_IN_KEYWORDS = ["makan di tempat", "di tempat", "dine in", "disini", "di sini"]
        TAKEAWAY_KEYWORDS = ["bungkus", "dibungkus", "take away", "takeaway", "bawa pulang"]

        chosen_dining_option = None
        if any(keyword in processed_text for keyword in DINE_IN_KEYWORDS):
            chosen_dining_option = "dine_in"
        elif any(keyword in processed_text for keyword in TAKEAWAY_KEYWORDS):
            chosen_dining_option = "takeaway"
        
        if chosen_dining_option:
            if user_id in user_contexts: # Pastikan konteks ada
                user_contexts[user_id]['order_details']['dining_option'] = chosen_dining_option
                total_price = order_details.get('total_price', 0)
                
                if chosen_dining_option == "dine_in":
                    set_user_state(user_id, STATE_AWAITING_PAYMENT_METHOD)
                    await update.message.reply_text(
                        f"Baik, untuk makan di tempat. Total pesanan Anda adalah Rp{total_price:,}.\n\n"
                        "Silakan pilih metode pembayaran: E-Wallet atau Cash di Kasir?"
                    )
                elif chosen_dining_option == "takeaway":
                    set_user_state(user_id, STATE_AWAITING_TAKEOUT_TYPE)
                    await update.message.reply_text(
                        f"Baik, untuk dibungkus. Total pesanan Anda adalah Rp{total_price:,}.\n\n"
                        "Mau diambil sendiri (Self-pickup) atau Delivery?"
                    )
            else: # Konteks hilang
                set_user_state(user_id, STATE_GENERAL)
                await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")

        else:
            await update.message.reply_text("Mohon pilih mau dimakan di tempat atau dibungkus?")
        return

    elif current_user_state == STATE_AWAITING_TAKEOUT_TYPE:
        order_details = get_order_details(user_id)
        if not order_details or order_details.get('dining_option') != 'takeaway':
            logger.warning(f"User {user_id} di state AWAITING_TAKEOUT_TYPE tapi opsi makan bukan takeaway atau tidak ada order.")
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Maaf, terjadi kesalahan. Proses pemesanan diulang.")
            return

        processed_text = preprocess_text(text)
        PICKUP_KEYWORDS = ["ambil sendiri", "pickup", "self pickup", "diambil", "jemput"]
        DELIVERY_KEYWORDS = ["delivery", "diantar", "kirim", "anter"]

        chosen_takeout_type = None
        if any(keyword in processed_text for keyword in PICKUP_KEYWORDS):
            chosen_takeout_type = "pickup"
        elif any(keyword in processed_text for keyword in DELIVERY_KEYWORDS):
            chosen_takeout_type = "delivery"

        if chosen_takeout_type:
            if user_id in user_contexts: # Pastikan konteks ada
                user_contexts[user_id]['order_details']['takeout_type'] = chosen_takeout_type
                
                if chosen_takeout_type == "pickup":
                    set_user_state(user_id, STATE_AWAITING_PAYMENT_METHOD)
                    total_price = order_details.get('total_price', 0)
                    await update.message.reply_text(
                        f"Oke, pesanan akan diambil sendiri. Totalnya tetap Rp{total_price:,}.\n\n"
                        "Silakan pilih metode pembayaran: E-Wallet atau Cash di Kasir?"
                    )
                elif chosen_takeout_type == "delivery":
                    set_user_state(user_id, STATE_GENERAL) 
                    reset_order_details(user_id)
                    await update.message.reply_text(
                        "Mohon maaf, untuk saat ini kami belum bisa melayani delivery.\n"
                        "Pemesanan Anda telah dibatalkan. Jika berkenan, Anda bisa memesan kembali untuk diambil sendiri."
                    )
            else: # Konteks hilang
                set_user_state(user_id, STATE_GENERAL)
                await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")
        else:
            await update.message.reply_text("Mohon pilih mau diambil sendiri atau delivery?")
        return

    elif current_user_state == STATE_AWAITING_PAYMENT_METHOD:
        order_details = get_order_details(user_id)
        if not order_details or not order_details.get('items'):
            logger.warning(f"User {user_id} di state AWAITING_PAYMENT_METHOD tapi tidak ada item di pesanan.")
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Maaf, terjadi kesalahan pada pesanan Anda. Bisa dimulai lagi?")
            return

        processed_text = preprocess_text(text)
        EWALLET_KEYWORDS = ["e-wallet", "wallet", "qris", "gopay", "ovo", "dana", "linkaja", "ewalet", "dompet digital"]
        CASH_KEYWORDS = ["cash", "kasir", "tunai", "kontan", "bayar di kasir"]
        
        chosen_payment_method = None
        if any(keyword in processed_text for keyword in EWALLET_KEYWORDS):
            chosen_payment_method = "E-Wallet"
        elif any(keyword in processed_text for keyword in CASH_KEYWORDS):
            chosen_payment_method = "Cash"

        if chosen_payment_method:
            if user_id in user_contexts: # Pastikan konteks ada
                user_contexts[user_id]['order_details']['payment_method'] = chosen_payment_method
                
                order_id = generate_order_id(user_id)
                user_contexts[user_id]['order_details']['order_id'] = order_id
                
                total_price = order_details.get('total_price', 0)
                dining_option = order_details.get('dining_option')
                takeout_type = order_details.get('takeout_type')

                item_summary_list = [f"{item['quantity']}x {item['item_data']['nama']}" for item in order_details.get('items', [])]
                item_summary_text = "\n- ".join(item_summary_list) if item_summary_list else "Tidak ada item"
                
                receipt_text = (
                    f"--- Struk Pesanan Kafe Cerita ---\n"
                    f"Nomor Pesanan: *{order_id}*\n"
                    f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
                    f"Item Dipesan:\n- {item_summary_text}\n\n"
                    f"Total Harga: *Rp{total_price:,}*\n"
                    f"Metode Pembayaran: {chosen_payment_method}\n"
                )

                preparation_time = "sesuai antrian" # Default
                if dining_option == "dine_in":
                    receipt_text += "Opsi Makan: Makan di Tempat\n"
                    preparation_time = "sekitar 15 menit"
                elif dining_option == "takeaway" and takeout_type == "pickup":
                    receipt_text += "Opsi Makan: Dibungkus (Ambil Sendiri)\n"
                    preparation_time = "sekitar 20 menit"

                final_message = ""
                if chosen_payment_method == "E-Wallet":
                    receipt_text += "\nStatus Pembayaran: *LUNAS (Simulasi)*\n"
                    final_message = (
                        f"Pembayaran via {chosen_payment_method} (simulasi) sebesar Rp{total_price:,} berhasil! 👍\n\n"
                        f"{receipt_text}\n"
                        f"Pesanan Anda akan siap dalam {preparation_time}. Terima kasih sudah memesan, {user_first_name}!"
                    )
                elif chosen_payment_method == "Cash":
                    receipt_text += "\nStatus Pembayaran: *Belum Dibayar*\n"
                    final_message = (
                        f"Baik, silakan lakukan pembayaran sebesar Rp{total_price:,} di kasir dengan menunjukkan Nomor Pesanan *{order_id}*.\n\n"
                        f"{receipt_text}\n"
                        f"Pesanan akan disiapkan setelah pembayaran dan akan siap dalam {preparation_time}. Terima kasih, {user_first_name}!"
                    )
                
                await update.message.reply_text(final_message, parse_mode='Markdown')
                set_user_state(user_id, STATE_GENERAL) 
                reset_order_details(user_id) # Bersihkan detail pesanan setelah selesai
            else: # Konteks hilang
                set_user_state(user_id, STATE_GENERAL)
                await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")
        else:
            await update.message.reply_text("Mohon pilih metode pembayaran: E-Wallet atau Cash di Kasir?")
        return

    # --- Logika berdasarkan Intent (jika state GENERAL) ---
    if current_user_state == STATE_GENERAL:
        # Pastikan user_contexts[user_id] ada sebelum mencoba akses 'last_inquired_item_data'
        if user_id not in user_contexts:
            set_user_state(user_id, STATE_GENERAL) # Inisialisasi jika terlewat

        intent, score = recognize_intent(text)
        logger.info(f"Intent terdeteksi (State GENERAL): {intent} (Skor: {score})")

        if intent == "lihat_menu":
            await menu_command(update, context)
        
        elif intent == "tanya_harga":
            item_data = extract_entities_item_name(text)
            if item_data:
                if user_id in user_contexts: 
                    user_contexts[user_id]['last_inquired_item_data'] = item_data
                    user_contexts[user_id]['timestamp'] = datetime.now()
                # Tidak perlu else karena user_contexts[user_id] sudah dipastikan ada
                await update.message.reply_text(
                    f"Harga untuk {item_data['nama']} adalah Rp{item_data['harga']:,}, {user_first_name}."
                )
            else:
                await update.message.reply_text(
                    f"Untuk informasi harga, mohon sebutkan nama item yang lebih spesifik ya, {user_first_name}. "
                    "Anda juga bisa lihat /menu."
                )
                
        elif intent == "info_pemesanan": 
            item_to_order = None
            explicit_item_data = extract_entities_item_name(text)
            if explicit_item_data: # Ada nama item di pesan "pesan"
                item_to_order = explicit_item_data
                logger.info(f"User {user_id} mau pesan item eksplisit: {item_to_order['nama']}")
            
            # Cek 'last_inquired_item_data' jika tidak ada item eksplisit di pesan "pesan"
            elif any(keyword in text.lower() for keyword in REFERENTIAL_KEYWORDS + ["pesan", "order", "mau itu", "beli itu"]) \
                 and user_id in user_contexts and user_contexts[user_id].get('last_inquired_item_data'):
                # Pastikan last_inquired_item_data tidak kadaluarsa (get_user_state sudah menghandle ini secara implisit)
                 if (datetime.now() - user_contexts[user_id].get('timestamp', datetime.min) < timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
                    item_to_order = user_contexts[user_id]['last_inquired_item_data']
                    logger.info(f"User {user_id} mau pesan item dari konteks 'last_inquired_item_data': {item_to_order['nama']}")
            
            if item_to_order:
                set_user_state(user_id, STATE_AWAITING_QUANTITY) 
                set_current_item_to_add(user_id, item_to_order) 
                await update.message.reply_text(f"Baik, {item_to_order['nama']}. Mau pesan berapa banyak/porsi?")
            else:
                await update.message.reply_text(
                    f"Anda mau pesan apa, {user_first_name}? Sebutkan nama itemnya atau lihat /menu dulu. "
                    f"Info pemesanan umum: {get_info_pemesanan(force_reload=True)}"
                )
            
        elif intent == "sapaan":
            await update.message.reply_text(f"Halo juga, {user_first_name}! Ada yang bisa saya bantu?")
            
        elif intent == "terima_kasih":
            await update.message.reply_text(f"Sama-sama, {user_first_name}! Senang bisa membantu. 😊")

        elif intent == "tanya_bot":
            await update.message.reply_text(
                f"Saya adalah bot Kafe Cerita, {user_first_name}. Saya bisa membantu Anda melihat menu, "
                "cek harga, dan memproses pesanan."
            )
        elif intent == "konfirmasi_tidak": # Jika pengguna bilang "tidak", "batal" di state general
             if user_id in user_contexts and user_contexts[user_id].get('state', STATE_GENERAL) != STATE_GENERAL:
                 # Jika ada state aktif, anggap sebagai pembatalan
                 set_user_state(user_id, STATE_GENERAL)
                 reset_order_details(user_id)
                 await update.message.reply_text("Baik, pesanan saat ini dibatalkan. Ada lagi yang bisa dibantu?")
             else: # Tidak ada state aktif, respons biasa
                 await update.message.reply_text("Oke, {user_first_name}.")
            
        else: # Fallback untuk state GENERAL
            await update.message.reply_text(
                f"Maaf {user_first_name}, saya belum mengerti maksud Anda. "
                "Anda bisa coba tanya tentang menu, harga item, atau cara pemesanan. "
                "Ketik /menu untuk melihat daftar menu lengkap."
            )
    elif current_user_state != STATE_GENERAL: # Pengguna dalam state tertentu tapi input tidak cocok
        logger.info(f"User {user_id} dalam state {current_user_state}, input tidak cocok: '{text}'")
        # Berikan pesan pengingat sesuai state saat ini
        if current_user_state == STATE_AWAITING_DINING_OPTION:
            await update.message.reply_text("Pilihannya mau dimakan di tempat atau dibungkus?")
        elif current_user_state == STATE_AWAITING_TAKEOUT_TYPE:
            await update.message.reply_text("Pilihannya mau diambil sendiri (self-pickup) atau delivery?")
        elif current_user_state == STATE_AWAITING_PAYMENT_METHOD:
            await update.message.reply_text("Pilih metode pembayaran: E-Wallet atau Cash di Kasir?")
        # Jika tidak ada pesan pengingat spesifik untuk state lain, bot akan diam (atau tambahkan default)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("Token Telegram tidak ditemukan atau belum diatur di config.py!")
        sys.exit("Silakan atur TELEGRAM_BOT_TOKEN di config.py")

    logger.info("Memulai bot dengan token...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot sedang berjalan. Tekan Ctrl-C untuk menghentikan.")
    application.run_polling()

if __name__ == "__main__":
    main()