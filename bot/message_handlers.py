"""
Module untuk menangani berbagai jenis pesan dan state conversation
Memisahkan logic handling berdasarkan state dan intent
"""
import logging
from datetime import datetime, timedelta

from bot.user_context import *

# Import NLP utilities dan modules
try:
    from bot.nlp_utils import recognize_intent, extract_entities_item_name, extract_quantity, preprocess_text
    from modules.menu_manager import get_info_pemesanan
except ImportError as e:
    print(f"Gagal mengimpor dependencies: {e}")

logger = logging.getLogger(__name__)

async def handle_quantity_input(update, user_id, user_first_name, text):
    """
    Handler untuk input quantity saat STATE_AWAITING_QUANTITY
    """
    order_details = get_order_details(user_id)
    item_to_add_data = order_details.get('current_item_to_add_data') if order_details else None

    if not item_to_add_data:
        logger.warning(f"User {user_id} di state AWAITING_QUANTITY tapi 'current_item_to_add_data' kosong.")
        set_user_state(user_id, STATE_GENERAL)
        reset_order_details(user_id)
        await update.message.reply_text("Maaf, sepertinya ada yang salah. Bisa sebutkan lagi item yang mau dipesan?")
        return

    qty = extract_quantity(text)
    if qty and qty > 0:
        if not add_item_to_current_order(user_id, qty):
             set_user_state(user_id, STATE_GENERAL)
             reset_order_details(user_id)
             await update.message.reply_text("Maaf, terjadi kendala saat memproses pesanan Anda. Silakan coba lagi.")
             return

        order_details = get_order_details(user_id)
        current_total = order_details.get('total_price', 0)
        
        item_names_in_order = []
        if order_details.get('items'):
            item_names_in_order = [f"{item['quantity']} {item['item_data']['nama']}" for item in order_details['items']]
        order_summary = ", ".join(item_names_in_order) if item_names_in_order else "Belum ada item"

        set_user_state(user_id, STATE_AWAITING_MORE_ITEMS)
        await update.message.reply_text(
            f"Oke, {qty} {item_to_add_data['nama']} sudah ditambahkan. "
            f"Pesanan Anda saat ini: {order_summary} (Total sementara: Rp{current_total:,}).\n\n"
            "Apakah ingin menambah item lain? Ketik nama menu yang ingin ditambah atau ketik 'selesai' untuk lanjut ke pembayaran."
        )
    else:
        await update.message.reply_text(f"Jumlah tidak valid, {user_first_name}. Mau pesan berapa banyak untuk {item_to_add_data['nama']}?")

async def handle_dining_option_input(update, user_id, text):
    """
    Handler untuk input dining option (dine-in/takeaway)
    """
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
        if user_id in user_contexts:
            update_order_field(user_id, 'dining_option', chosen_dining_option)
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
        else:
            set_user_state(user_id, STATE_GENERAL)
            await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")
    else:
        await update.message.reply_text("Mohon pilih mau dimakan di tempat atau dibungkus?")

async def handle_takeout_type_input(update, user_id, text):
    """
    Handler untuk input takeout type (pickup/delivery)
    """
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
        if user_id in user_contexts:
            update_order_field(user_id, 'takeout_type', chosen_takeout_type)
            
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
        else:
            set_user_state(user_id, STATE_GENERAL)
            await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")
    else:
        await update.message.reply_text("Mohon pilih mau diambil sendiri atau delivery?")

async def handle_payment_method_input(update, user_id, user_first_name, text):
    """
    Handler untuk input payment method dan finalisasi order
    """
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
        if user_id in user_contexts:
            update_order_field(user_id, 'payment_method', chosen_payment_method)
            
            order_id = generate_order_id(user_id)
            update_order_field(user_id, 'order_id', order_id)
            
            # Generate receipt
            receipt_message = await generate_receipt(order_details, order_id, chosen_payment_method, user_first_name)
            await update.message.reply_text(receipt_message, parse_mode='Markdown')
            
            # Reset order after completion
            set_user_state(user_id, STATE_GENERAL) 
            reset_order_details(user_id)
        else:
            set_user_state(user_id, STATE_GENERAL)
            await update.message.reply_text("Maaf, sesi pesanan Anda tidak ditemukan. Silakan mulai lagi.")
    else:
        await update.message.reply_text("Mohon pilih metode pembayaran: E-Wallet atau Cash di Kasir?")

async def generate_receipt(order_details, order_id, payment_method, user_first_name):
    """
    Generate receipt text untuk pesanan yang sudah selesai
    """
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
        f"Metode Pembayaran: {payment_method}\n"
    )

    preparation_time = "sesuai antrian"
    if dining_option == "dine_in":
        receipt_text += "Opsi Makan: Makan di Tempat\n"
        preparation_time = "sekitar 15 menit"
    elif dining_option == "takeaway" and takeout_type == "pickup":
        receipt_text += "Opsi Makan: Dibungkus (Ambil Sendiri)\n"
        preparation_time = "sekitar 20 menit"

    if payment_method == "E-Wallet":
        receipt_text += "\nStatus Pembayaran: *LUNAS (Simulasi)*\n"
        final_message = (
            f"Pembayaran via {payment_method} (simulasi) sebesar Rp{total_price:,} berhasil! 👍\n\n"
            f"{receipt_text}\n"
            f"Pesanan Anda akan siap dalam {preparation_time}. Terima kasih sudah memesan, {user_first_name}!"
        )
    elif payment_method == "Cash":
        receipt_text += "\nStatus Pembayaran: *Belum Dibayar*\n"
        final_message = (
            f"Baik, silakan lakukan pembayaran sebesar Rp{total_price:,} di kasir dengan menunjukkan Nomor Pesanan *{order_id}*.\n\n"
            f"{receipt_text}\n"
            f"Pesanan akan disiapkan setelah pembayaran dan akan siap dalam {preparation_time}. Terima kasih, {user_first_name}!"
        )
    
    return final_message

async def handle_general_intent(update, user_id, user_first_name, text):
    """
    Handler untuk intent di state GENERAL (menu, harga, pemesanan, dll)
    """
    # Pastikan user context ada
    if user_id not in user_contexts:
        set_user_state(user_id, STATE_GENERAL)

    intent, score = recognize_intent(text)
    logger.info(f"Intent terdeteksi (State GENERAL): {intent} (Skor: {score})")

    if intent == "lihat_menu":
        from bot.commands import menu_command
        await menu_command(update, None)
    
    elif intent == "tanya_harga":
        item_data = extract_entities_item_name(text)
        if item_data:
            set_last_inquired_item(user_id, item_data)
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
        
        if explicit_item_data:
            item_to_order = explicit_item_data
            logger.info(f"User {user_id} mau pesan item eksplisit: {item_to_order['nama']}")
        elif any(keyword in text.lower() for keyword in REFERENTIAL_KEYWORDS + ["pesan", "order", "mau itu", "beli itu"]):
            item_to_order = get_last_inquired_item(user_id)
            if item_to_order:
                logger.info(f"User {user_id} mau pesan item dari konteks: {item_to_order['nama']}")
        
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
    elif intent == "konfirmasi_tidak":
        if user_id in user_contexts and user_contexts[user_id].get('state', STATE_GENERAL) != STATE_GENERAL:
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Baik, pesanan saat ini dibatalkan. Ada lagi yang bisa dibantu?")
        else:
            await update.message.reply_text(f"Oke, {user_first_name}.")
        
    else:
        await update.message.reply_text(
            f"Maaf {user_first_name}, saya belum mengerti maksud Anda. "
            "Anda bisa coba tanya tentang menu, harga item, atau cara pemesanan. "
            "Ketik /menu untuk melihat daftar menu lengkap."
        )

async def handle_invalid_state_input(update, current_user_state):
    """
    Handler untuk input yang tidak sesuai dengan state saat ini
    Memberikan reminder message sesuai state
    """
    if current_user_state == STATE_AWAITING_MORE_ITEMS:
        await update.message.reply_text("Sebutkan nama menu yang ingin ditambah atau ketik 'selesai' untuk lanjut pembayaran.")
    elif current_user_state == STATE_AWAITING_DINING_OPTION:
        await update.message.reply_text("Pilihannya mau dimakan di tempat atau dibungkus?")
    elif current_user_state == STATE_AWAITING_TAKEOUT_TYPE:
        await update.message.reply_text("Pilihannya mau diambil sendiri (self-pickup) atau delivery?")
    elif current_user_state == STATE_AWAITING_PAYMENT_METHOD:
        await update.message.reply_text("Pilih metode pembayaran: E-Wallet atau Cash di Kasir?")
    elif current_user_state == STATE_AWAITING_QUANTITY:
        await update.message.reply_text("Mohon masukkan jumlah item yang ingin dipesan (angka).")

async def handle_more_items_input(update, user_id, user_first_name, text):
    """
    Handler untuk input saat STATE_AWAITING_MORE_ITEMS
    User bisa menambah item lain atau selesai untuk lanjut pembayaran
    """
    processed_text = text.lower().strip()
    
    # Keywords untuk menyelesaikan pemesanan
    FINISH_KEYWORDS = ["selesai", "tidak", "enggak", "nggak", "cukup", "lanjut", "bayar", "checkout"]
    
    if any(keyword in processed_text for keyword in FINISH_KEYWORDS):
        # User selesai memesan, lanjut ke dining option
        order_details = get_order_details(user_id)
        if not order_details or not order_details.get('items'):
            set_user_state(user_id, STATE_GENERAL)
            reset_order_details(user_id)
            await update.message.reply_text("Maaf, tidak ada item dalam pesanan. Silakan mulai memesan lagi.")
            return
            
        current_total = order_details.get('total_price', 0)
        item_names_in_order = [f"{item['quantity']} {item['item_data']['nama']}" for item in order_details['items']]
        order_summary = ", ".join(item_names_in_order)
        
        set_user_state(user_id, STATE_AWAITING_DINING_OPTION)
        await update.message.reply_text(
            f"Baik! Ringkasan pesanan Anda:\n{order_summary}\n"
            f"Total: Rp{current_total:,}\n\n"
            "Mau dimakan di tempat atau dibungkus?"
        )
        return
    
    # User ingin menambah item lain - coba extract nama item
    item_data = extract_entities_item_name(text)
    if item_data:
        set_user_state(user_id, STATE_AWAITING_QUANTITY)
        set_current_item_to_add(user_id, item_data)
        await update.message.reply_text(f"Mau pesan {item_data['nama']} berapa banyak?")
    else:
        # Item tidak ditemukan, minta input yang lebih spesifik
        await update.message.reply_text(
            f"Maaf {user_first_name}, saya tidak menemukan menu '{text}'. "
            "Coba sebutkan nama menu yang lebih spesifik, lihat /menu, atau ketik 'selesai' jika sudah cukup."
        )
