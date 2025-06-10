"""
Main Telegram Bot File
Entry point untuk menjalankan chatbot Kafe Cerita
Mengorganisir handler dan routing message berdasarkan state
"""
import logging
import sys
import os

# Setup path untuk import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import konfigurasi
try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError as e:
    print(f"Gagal mengimpor config: {e}")
    print("Pastikan file config.py tersedia dan berisi TELEGRAM_BOT_TOKEN")
    sys.exit(1)

# Import modules bot
from bot.user_context import (
    get_user_state, set_user_state, STATE_GENERAL, STATE_AWAITING_QUANTITY,
    STATE_AWAITING_MORE_ITEMS, STATE_AWAITING_DINING_OPTION, STATE_AWAITING_TAKEOUT_TYPE, 
    STATE_AWAITING_PAYMENT_METHOD, user_contexts
)
from bot.commands import start_command, menu_command
from bot.message_handlers import (
    handle_quantity_input, handle_dining_option_input, handle_takeout_type_input,
    handle_payment_method_input, handle_general_intent, handle_invalid_state_input,
    handle_more_items_input  # Handler baru untuk multiple items
)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main message handler - router untuk semua pesan text
    Mengarahkan ke handler yang sesuai berdasarkan user state
    """
    text = update.message.text
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    
    # Dapatkan state user saat ini
    current_user_state = get_user_state(user_id)
    
    # Inisialisasi konteks jika belum ada (untuk user baru atau konteks kadaluarsa)
    if user_id not in user_contexts:
        set_user_state(user_id, STATE_GENERAL)
        current_user_state = STATE_GENERAL

    logger.info(f"Pesan dari {user_first_name} (ID: {user_id}, State: {current_user_state}): {text}")

    # Route ke handler yang sesuai berdasarkan state
    try:
        if current_user_state == STATE_AWAITING_QUANTITY:
            await handle_quantity_input(update, user_id, user_first_name, text)
            
        elif current_user_state == STATE_AWAITING_MORE_ITEMS:
            await handle_more_items_input(update, user_id, user_first_name, text)
            
        elif current_user_state == STATE_AWAITING_DINING_OPTION:
            await handle_dining_option_input(update, user_id, text)
            
        elif current_user_state == STATE_AWAITING_TAKEOUT_TYPE:
            await handle_takeout_type_input(update, user_id, text)
            
        elif current_user_state == STATE_AWAITING_PAYMENT_METHOD:
            await handle_payment_method_input(update, user_id, user_first_name, text)
            
        elif current_user_state == STATE_GENERAL:
            await handle_general_intent(update, user_id, user_first_name, text)
            
        else:
            # State tidak dikenali atau input tidak sesuai state
            logger.warning(f"User {user_id} dalam state {current_user_state}, input tidak cocok: '{text}'")
            await handle_invalid_state_input(update, current_user_state)
            
    except Exception as e:
        logger.error(f"Error handling message untuk user {user_id}: {e}")
        await update.message.reply_text(
            "Maaf, terjadi kesalahan sistem. Silakan coba lagi atau gunakan /start untuk memulai ulang."
        )

def main() -> None:
    """
    Fungsi utama untuk menjalankan bot
    Setup handlers dan mulai polling
    """
    # Validasi token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("Token Telegram tidak ditemukan atau belum diatur di config.py!")
        sys.exit("Silakan atur TELEGRAM_BOT_TOKEN di config.py")

    logger.info("Memulai Telegram Bot Kafe Cerita...")
    
    # Build application dengan token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Register message handler untuk semua text (bukan command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot siap dan mulai polling. Tekan Ctrl-C untuk menghentikan.")
    
    # Mulai polling untuk menerima message
    application.run_polling()

if __name__ == "__main__":
    main()