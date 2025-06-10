"""
Module untuk mengelola konteks dan state pengguna
Menangani session management, order details, dan state transitions
"""
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# --- Konstanta State ---
STATE_GENERAL = "GENERAL"
STATE_AWAITING_QUANTITY = "AWAITING_QUANTITY"
STATE_AWAITING_DINING_OPTION = "AWAITING_DINING_OPTION"
STATE_AWAITING_TAKEOUT_TYPE = "AWAITING_TAKEOUT_TYPE"
STATE_AWAITING_PAYMENT_METHOD = "AWAITING_PAYMENT_METHOD"

# --- Konfigurasi Context ---
CONTEXT_EXPIRY_MINUTES = 30
REFERENTIAL_KEYWORDS = ["itu", "item itu", "item tersebut", "yang tadi", "yang barusan", "ini"]

# --- Storage Global Context ---
user_contexts = {}

def get_user_state(user_id):
    """
    Mendapatkan state user saat ini dengan validasi expiry
    Returns: STATE_GENERAL jika expired atau tidak ada
    """
    if user_id in user_contexts:
        context_data = user_contexts[user_id]
        if 'timestamp' in context_data and \
           (datetime.now() - context_data['timestamp'] < timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
            return context_data.get('state', STATE_GENERAL)
        else: 
            logger.info(f"Konteks untuk user {user_id} kadaluarsa. Dihapus.")
            if user_id in user_contexts: 
                del user_contexts[user_id] 
            return STATE_GENERAL
    return STATE_GENERAL

def set_user_state(user_id, state):
    """
    Mengatur state user dan menginisialisasi struktur data context
    """
    now = datetime.now()
    if user_id not in user_contexts or \
       (now - user_contexts[user_id].get('timestamp', datetime.min) >= timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
        # Inisialisasi context baru
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
        # Update state existing context
        user_contexts[user_id]['state'] = state
        user_contexts[user_id]['timestamp'] = now
    
    logger.info(f"State untuk user {user_id} diatur ke {state}.")

def get_order_details(user_id):
    """
    Mendapatkan detail pesanan user dengan validasi
    Returns: dict order_details atau {} jika tidak valid
    """
    if user_id in user_contexts and get_user_state(user_id) != STATE_GENERAL:
        # Inisialisasi order_details jika tidak ada (safety check)
        if 'order_details' not in user_contexts[user_id]:
             user_contexts[user_id]['order_details'] = {
                'items': [], 'current_item_to_add_data': None, 'dining_option': None,
                'takeout_type': None, 'payment_method': None, 'total_price': 0, 'order_id': None
            }
        return user_contexts[user_id].get('order_details', {})
    return {}

def set_current_item_to_add(user_id, item_data):
    """
    Menyimpan item yang akan ditambahkan ke pesanan (menunggu input quantity)
    """
    if user_id in user_contexts:
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
    """
    Menambahkan item dengan quantity ke pesanan saat ini
    Returns: True jika berhasil, False jika gagal
    """
    if user_id not in user_contexts:
        logger.warning(f"User {user_id} tidak memiliki konteks saat mencoba menambah item.")
        return False
        
    order_details = user_contexts[user_id].get('order_details')
    if not order_details:
        logger.error(f"User {user_id}: 'order_details' tidak ada di konteks saat add_item_to_current_order.")
        return False

    item_to_add_data = order_details.get('current_item_to_add_data')
    if not item_to_add_data:
        logger.warning(f"User {user_id}: Tidak ada 'current_item_to_add_data' saat menambah kuantitas.")
        return False

    # Cek apakah item sudah ada di pesanan, jika ya tambah quantity
    found = False
    if 'items' not in order_details: 
        order_details['items'] = []

    for item_in_order in order_details['items']:
        if item_in_order['item_data']['id'] == item_to_add_data['id']:
            item_in_order['quantity'] += int(quantity)
            found = True
            break
    
    if not found:
        order_details['items'].append({'item_data': item_to_add_data, 'quantity': int(quantity)})
    
    # Reset current_item_to_add setelah berhasil ditambahkan
    order_details['current_item_to_add_data'] = None 
    user_contexts[user_id]['timestamp'] = datetime.now()
    calculate_total_price(user_id)
    logger.info(f"User {user_id}: Item '{item_to_add_data['nama']}' x{quantity} berhasil ditambahkan/diupdate ke pesanan.")
    return True

def calculate_total_price(user_id):
    """
    Menghitung total harga pesanan dan menyimpannya di context
    Returns: total price atau 0 jika tidak ada item
    """
    order_details = get_order_details(user_id)
    if order_details and order_details.get('items'):
        total = sum(item['item_data']['harga'] * item['quantity'] for item in order_details['items'])
        if user_id in user_contexts and 'order_details' in user_contexts[user_id]:
            user_contexts[user_id]['order_details']['total_price'] = total
            logger.info(f"User {user_id}: Total harga pesanan dihitung Rp{total:,}")
            return total
    return 0

def generate_order_id(user_id):
    """
    Generate ID unik untuk pesanan
    Format: KC[YYMMDD]-[4digit_user][2hex_random]
    """
    now = datetime.now()
    user_part = str(user_id)[-4:] 
    random_part = str(os.urandom(2).hex().upper())
    return f"KC{now.strftime('%y%m%d')}-{user_part}{random_part}"

def reset_order_details(user_id):
    """
    Membersihkan detail pesanan setelah selesai atau dibatalkan
    """
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

def set_last_inquired_item(user_id, item_data):
    """
    Menyimpan item terakhir yang ditanyakan user (untuk referensi 'itu', 'yang tadi', dll)
    """
    if user_id in user_contexts:
        user_contexts[user_id]['last_inquired_item_data'] = item_data
        user_contexts[user_id]['timestamp'] = datetime.now()
        logger.info(f"User {user_id}: Last inquired item set to '{item_data['nama']}'")

def get_last_inquired_item(user_id):
    """
    Mendapatkan item terakhir yang ditanyakan user dengan validasi expiry
    """
    if user_id in user_contexts and user_contexts[user_id].get('last_inquired_item_data'):
        if (datetime.now() - user_contexts[user_id].get('timestamp', datetime.min) < timedelta(minutes=CONTEXT_EXPIRY_MINUTES)):
            return user_contexts[user_id]['last_inquired_item_data']
    return None

def update_order_field(user_id, field_name, value):
    """
    Update field tertentu di order_details
    """
    if user_id in user_contexts and 'order_details' in user_contexts[user_id]:
        user_contexts[user_id]['order_details'][field_name] = value
        user_contexts[user_id]['timestamp'] = datetime.now()
        logger.info(f"User {user_id}: Order field '{field_name}' updated to '{value}'")
