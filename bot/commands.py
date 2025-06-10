"""
Module untuk command handlers (/start, /menu, etc.)
Memisahkan logic command dari message handling
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.user_context import set_user_state, reset_order_details, STATE_GENERAL

# Import modules yang diperlukan
try:
    from modules.menu_manager import get_menu, get_info_pemesanan
except ImportError as e:
    print(f"Gagal mengimpor modules: {e}")

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk command /start
    Inisialisasi user context dan greeting message
    """
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Reset state dan order details untuk user baru/restart
    set_user_state(user_id, STATE_GENERAL) 
    reset_order_details(user_id)
    
    await update.message.reply_html(
        rf"Halo {user.mention_html()}! Selamat datang di Bot Mata Kopian. Ada yang bisa saya bantu? "
        "Anda bisa tanya tentang menu, harga, atau cara pemesanan.",
    )
    logger.info(f"User {user_id} ({user.first_name}) memulai bot dengan /start")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk command /menu
    Menampilkan daftar menu lengkap dengan kategorisasi
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} meminta menu dengan /menu")
    
    menu = get_menu(force_reload=True)
    response = "☕ *Menu Mata Kopian* ☕\n\n"
    
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
                
                # Tambahkan deskripsi jika ada (untuk informasi lengkap)
                if deskripsi:
                    response += f"\n  _{deskripsi}_"
                response += "\n"
        else:
            response += f"_Belum ada menu {category_info['name'].lower()}._\n"
        
        response += "\n"
    
    # Tambahkan info pemesanan di akhir
    response += f"*Info Pemesanan* ℹ️:\n{get_info_pemesanan(force_reload=True)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')
