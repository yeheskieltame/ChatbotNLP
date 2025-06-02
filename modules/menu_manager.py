# modules/menu_manager.py
import json
import os
import uuid # Untuk generate ID unik

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE_PATH = os.path.join(BASE_DIR, 'data', 'menu_data.json')

_menu_cache = None

def load_menu_data():
    """Memuat data menu dari file JSON."""
    global _menu_cache
    try:
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            _menu_cache = json.load(f)
            return _menu_cache
    except FileNotFoundError:
        print(f"Error: File data menu tidak ditemukan di {DATA_FILE_PATH}")
        _menu_cache = {"makanan": [], "minuman": [], "info_pemesanan": "Data menu tidak tersedia."}
        return _menu_cache
    except json.JSONDecodeError:
        print(f"Error: Gagal membaca format JSON dari {DATA_FILE_PATH}")
        _menu_cache = {"makanan": [], "minuman": [], "info_pemesanan": "Data menu rusak."}
        return _menu_cache

def save_menu_data():
    """Menyimpan data menu (dari cache) ke file JSON."""
    global _menu_cache
    if _menu_cache is None:
        print("Tidak ada data di cache untuk disimpan.")
        return False
    try:
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(_menu_cache, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saat menyimpan data menu: {e}")
        return False

def get_menu(force_reload=False):
    """Mengembalikan seluruh menu, menggunakan cache jika memungkinkan."""
    global _menu_cache
    if _menu_cache is None or force_reload:
        load_menu_data()
    return _menu_cache

def get_items_by_category(category_name, force_reload=False):
    menu = get_menu(force_reload)
    if category_name:
        return menu.get(category_name.lower(), [])
    return []

def get_item_by_id(item_id, force_reload=False): # Fungsi baru untuk mendapatkan item berdasarkan ID
    """Mencari item berdasarkan ID uniknya di semua kategori."""
    menu = get_menu(force_reload)
    if item_id:
        for category_key in menu:
            if category_key == "info_pemesanan":
                continue
            if isinstance(menu[category_key], list):
                for item in menu[category_key]:
                    if item.get("id") == item_id:
                        return item, category_key # Kembalikan item dan kategorinya
    return None, None


def get_item_by_name(item_name, force_reload=False):
    menu = get_menu(force_reload)
    if item_name:
        for category_key in menu:
            if category_key == "info_pemesanan":
                continue
            if isinstance(menu[category_key], list):
                for item in menu[category_key]:
                    if item.get("nama", "").lower() == item_name.lower():
                        return item
    return None

def get_info_pemesanan(force_reload=False):
    menu = get_menu(force_reload)
    return menu.get("info_pemesanan", "Informasi pemesanan tidak tersedia.")

# --- Fungsi CRUD Baru ---
def generate_new_id(prefix="ITEM"):
    """Menghasilkan ID unik baru."""
    return f"{prefix}_{uuid.uuid4().hex[:6].upper()}"

def add_item(category, nama, harga, deskripsi):
    """Menambahkan item baru ke menu."""
    global _menu_cache
    menu = get_menu() # Pastikan cache sudah terisi
    
    if category.lower() not in menu:
        menu[category.lower()] = [] # Buat kategori jika belum ada (meskipun idealnya sudah ada "makanan" dan "minuman")

    # Cek apakah item dengan nama yang sama sudah ada di kategori tersebut
    for item_existing in menu[category.lower()]:
        if item_existing.get("nama", "").lower() == nama.lower():
            return False, "Item dengan nama tersebut sudah ada di kategori ini."

    new_item_id = generate_new_id(prefix=category[0].upper())
    new_item = {
        "id": new_item_id,
        "nama": nama,
        "harga": int(harga), # Pastikan harga adalah integer
        "deskripsi": deskripsi
    }
    menu[category.lower()].append(new_item)
    if save_menu_data():
        return True, new_item_id
    else:
        # Rollback jika gagal simpan (opsional, tergantung kompleksitas)
        menu[category.lower()].pop() # Hapus item yang baru ditambahkan dari cache
        return False, "Gagal menyimpan data menu."

def update_item(item_id, updated_data):
    """Memperbarui item yang ada berdasarkan ID."""
    global _menu_cache
    menu = get_menu()
    item_to_update, category_key = get_item_by_id(item_id, force_reload=False) # Cari di cache dulu

    if not item_to_update:
        return False, "Item tidak ditemukan."

    # Cek duplikasi nama jika nama diubah
    if "nama" in updated_data and updated_data["nama"].lower() != item_to_update.get("nama","").lower():
        for item_existing in menu[category_key]:
            if item_existing.get("id") != item_id and item_existing.get("nama", "").lower() == updated_data["nama"].lower():
                return False, "Nama item duplikat dengan item lain di kategori yang sama."

    item_to_update.update(updated_data)
    if "harga" in updated_data: # Pastikan harga adalah integer
        item_to_update["harga"] = int(updated_data["harga"])

    if save_menu_data():
        return True, "Item berhasil diperbarui."
    else:
        # Untuk rollback yang lebih kompleks, kita perlu menyimpan state item sebelum diubah.
        # Untuk sekarang, kita asumsikan save berhasil atau errornya ditangani di level atas.
        return False, "Gagal menyimpan data menu setelah pembaruan."

def delete_item(item_id):
    """Menghapus item dari menu berdasarkan ID."""
    global _menu_cache
    menu = get_menu()
    item_to_delete, category_key = get_item_by_id(item_id, force_reload=False)

    if not item_to_delete:
        return False, "Item tidak ditemukan."

    menu[category_key].remove(item_to_delete)
    
    if save_menu_data():
        return True, "Item berhasil dihapus."
    else:
        # Rollback jika gagal simpan
        menu[category_key].append(item_to_delete) # Tambahkan kembali ke cache
        return False, "Gagal menyimpan data setelah penghapusan."

def update_info_pemesanan(new_info):
    """Memperbarui informasi pemesanan."""
    global _menu_cache
    menu = get_menu()
    menu["info_pemesanan"] = new_info
    if save_menu_data():
        return True, "Info pemesanan berhasil diperbarui."
    else:
        # Rollback (opsional)
        # menu["info_pemesanan"] = old_info # Perlu menyimpan old_info sebelumnya
        return False, "Gagal menyimpan info pemesanan."

# Pastikan load_menu_data dipanggil sekali di awal agar _menu_cache terisi
if _menu_cache is None:
    load_menu_data()