# admin_dashboard/app.py
import streamlit as st
import sys
import os

# Tambahkan path project root ke sys.path agar bisa impor dari modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from modules.menu_manager import (
        get_menu,
        get_info_pemesanan,
        add_item,
        update_info_pemesanan,
        update_item,  # Fungsi baru untuk diimpor
        delete_item,  # Fungsi baru untuk diimpor
        get_item_by_id # Fungsi baru untuk diimpor
    )
except ImportError as e:
    st.error(f"Gagal mengimpor menu_manager: {e}. Pastikan struktur direktori sudah benar dan file modules/menu_manager.py ada.")
    st.stop()

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Admin Dashboard - Mata Kopian",
    page_icon="☕",
    layout="wide"
)

# Inisialisasi session state jika belum ada
if 'editing_item_id' not in st.session_state:
    st.session_state.editing_item_id = None
if 'editing_item_data' not in st.session_state:
    st.session_state.editing_item_data = None # Untuk menyimpan data item yang sedang diedit
if 'confirming_delete_id' not in st.session_state:
    st.session_state.confirming_delete_id = None


st.title("☕ Admin Dashboard Mata Kopian")
st.markdown("Kelola menu dan informasi kafe Anda di sini.")

# Tombol untuk memuat ulang data menu
if st.button("🔄 Muat Ulang Data Menu dari File", key="reload_main_data"):
    st.cache_data.clear()
    # Reset state edit/delete jika sedang aktif
    st.session_state.editing_item_id = None
    st.session_state.editing_item_data = None
    st.session_state.confirming_delete_id = None
    st.success("Data menu akan dimuat ulang.")
    st.rerun()

# Memuat data menu (menggunakan cache Streamlit)
@st.cache_data
def load_display_menu():
    return get_menu(force_reload=True)

menu_data = load_display_menu()

# --- SIDEBAR UNTUK EDIT ITEM ---
if st.session_state.editing_item_id:
    item_to_edit, category_of_item = get_item_by_id(st.session_state.editing_item_id)
    if item_to_edit:
        st.sidebar.header(f"📝 Edit Item: {item_to_edit.get('nama')}")
        with st.sidebar.form("edit_item_form"):
            # Jika st.session_state.editing_item_data belum diisi, isi dengan data awal
            if st.session_state.editing_item_data is None or st.session_state.editing_item_data.get('id') != item_to_edit.get('id'):
                st.session_state.editing_item_data = item_to_edit.copy()

            edit_nama = st.text_input("Nama Item:", value=st.session_state.editing_item_data.get('nama', ''), key="edit_nama_sidebar")
            edit_harga = st.number_input("Harga (Rp):", value=st.session_state.editing_item_data.get('harga', 0), min_value=0, step=1000, key="edit_harga_sidebar")
            edit_deskripsi = st.text_area("Deskripsi Item:", value=st.session_state.editing_item_data.get('deskripsi', ''), key="edit_desk_sidebar")
            
            # Update st.session_state.editing_item_data secara live saat input berubah
            st.session_state.editing_item_data['nama'] = edit_nama
            st.session_state.editing_item_data['harga'] = edit_harga
            st.session_state.editing_item_data['deskripsi'] = edit_deskripsi

            col1_edit, col2_edit = st.columns(2)
            with col1_edit:
                if st.form_submit_button("Simpan Perubahan"):
                    if not edit_nama:
                        st.sidebar.warning("Nama item tidak boleh kosong.")
                    elif edit_harga <= 0:
                        st.sidebar.warning("Harga item harus lebih besar dari 0.")
                    else:
                        updated_data = {
                            "nama": edit_nama,
                            "harga": int(edit_harga),
                            "deskripsi": edit_deskripsi
                        }
                        success, message = update_item(st.session_state.editing_item_id, updated_data)
                        if success:
                            st.sidebar.success(message)
                            st.cache_data.clear()
                            st.session_state.editing_item_id = None # Selesai edit
                            st.session_state.editing_item_data = None
                            st.rerun()
                        else:
                            st.sidebar.error(f"Gagal memperbarui: {message}")
            with col2_edit:
                if st.form_submit_button("Batal"):
                    st.session_state.editing_item_id = None
                    st.session_state.editing_item_data = None
                    st.rerun()
    else:
        # Jika item tidak ditemukan lagi (misal sudah terhapus dari proses lain)
        st.sidebar.warning("Item yang akan diedit tidak ditemukan lagi.")
        st.session_state.editing_item_id = None
        st.session_state.editing_item_data = None
        st.rerun()


# --- TABS UNTUK KELOLA MENU DAN INFO ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["➕ Tambah Item & ℹ️ Info Pesan", "☕ Es Kopi", "🍵 Non Kopi", "🫕 Espresso Based", "🍸 Refreshment", "🥤 Others", "🥐 Pastry"])

with tab1:
    st.header("➕ Tambah Item Menu Baru")
    with st.form("tambah_item_form", clear_on_submit=True):
        tambah_kategori = st.selectbox("Pilih Kategori:", ["es_kopi", "non_kopi", "espresso_based", "refreshment", "others", "pastry"], key="add_cat_main")
        tambah_nama = st.text_input("Nama Item:", key="add_nama_main")
        tambah_harga = st.number_input("Harga (Rp):", min_value=0, step=1000, key="add_harga_main")
        tambah_deskripsi = st.text_area("Deskripsi Item:", key="add_desc_main")
        
        submitted_tambah = st.form_submit_button("Tambahkan Item")

        if submitted_tambah:
            if not tambah_nama:
                st.warning("Nama item tidak boleh kosong.")
            elif tambah_harga <= 0:
                st.warning("Harga item harus lebih besar dari 0.")
            else:
                success, message_or_id = add_item(
                    category=tambah_kategori,
                    nama=tambah_nama,
                    harga=tambah_harga,
                    deskripsi=tambah_deskripsi
                )
                if success:
                    st.success(f"Item '{tambah_nama}' berhasil ditambahkan dengan ID {message_or_id}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Gagal menambahkan item: {message_or_id}")
    st.divider()

    st.header("✍️ Edit Informasi Pemesanan")
    current_info_pemesanan = get_info_pemesanan(force_reload=True)

    with st.form("edit_info_form"):
        new_info_text = st.text_area("Teks Informasi Pemesanan:", value=current_info_pemesanan, height=100, key="edit_info_text_main")
        submitted_edit_info = st.form_submit_button("Simpan Info Pemesanan")

        if submitted_edit_info:
            if new_info_text.strip() == "":
                st.warning("Informasi pemesanan tidak boleh kosong.")
            elif new_info_text == current_info_pemesanan:
                st.info("Tidak ada perubahan pada informasi pemesanan.")
            else:
                success, message = update_info_pemesanan(new_info_text)
                if success:
                    st.success(message)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)

def display_menu_items(category_name, items_list):
    """Fungsi untuk menampilkan item menu dengan tombol Edit dan Hapus."""
    if items_list:
        for item in items_list:
            item_id = item.get('id', '')
            with st.container(border=True): # Menambahkan border ke container
                col_info1, col_info2, col_actions = st.columns([4, 2, 2]) # Sesuaikan rasio kolom

                with col_info1:
                    st.markdown(f"**{item.get('nama', 'N/A')}**")
                    st.caption(f"ID: {item_id}")
                    st.write(item.get('deskripsi', ''))
                
                with col_info2:
                    st.markdown(f"**Rp{item.get('harga', 0):,}**")

                with col_actions:
                    # Tombol Edit
                    if st.button("✏️ Edit", key=f"edit_{item_id}"):
                        st.session_state.editing_item_id = item_id
                        st.session_state.editing_item_data = None # Reset data edit agar terisi ulang
                        st.session_state.confirming_delete_id = None # Pastikan tidak sedang konfirmasi hapus
                        st.rerun()

                    # Logika Hapus dengan Konfirmasi
                    if st.session_state.confirming_delete_id == item_id:
                        st.warning(f"Hapus '{item.get('nama')}'?")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✔️ Ya, Hapus", key=f"confirm_delete_{item_id}", type="primary"):
                                success, message = delete_item(item_id)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                                st.session_state.confirming_delete_id = None
                                st.cache_data.clear()
                                st.rerun()
                        with col_cancel:
                            if st.button("Batalkan", key=f"cancel_delete_{item_id}"):
                                st.session_state.confirming_delete_id = None
                                st.rerun()
                    else:
                        if st.button("🗑️ Hapus", key=f"delete_{item_id}"):
                            st.session_state.confirming_delete_id = item_id
                            st.session_state.editing_item_id = None # Pastikan tidak sedang edit
                            st.rerun()
            st.markdown("---") # Pemisah antar item lebih jelas
    else:
        st.info(f"Belum ada data {category_name.lower()}.")


with tab2:
    st.header("☕ Es Kopi")
    if not menu_data or "es_kopi" not in menu_data:
        st.warning("Data minuman tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Es Kopi", menu_data.get("es_kopi", []))

with tab3:
    st.header("🍵 Non Kopi")
    if not menu_data or "non_kopi" not in menu_data:
        st.warning("Data minuman tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Non Kopi", menu_data.get("non_kopi", []))

with tab4:
    st.header("🫕 Espresso Based")
    if not menu_data or "espresso_based" not in menu_data:
        st.warning("Data minuman tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Espresso Based", menu_data.get("espresso_based", []))

with tab5:
    st.header("🍸 Refreshment")
    if not menu_data or "refreshment" not in menu_data:
        st.warning("Data minuman tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Refreshment", menu_data.get("refreshment", []))

with tab6:
    st.header("🥤 Others")
    if not menu_data or "others" not in menu_data:
        st.warning("Data minuman tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Other", menu_data.get("others", []))

with tab7:
    st.header("🥐 Pastry")
    if not menu_data or "pastry" not in menu_data:
        st.warning("Data pastry tidak dapat dimuat atau kosong.")
    else:
        display_menu_items("Pastry", menu_data.get("pastry", []))

st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.caption("Dashboard Admin Mata Kopian v0.2")