import streamlit as st
import pandas as pd
import os
from db import get_db, render_header
from sqlalchemy import text

# --- MODAL DETAIL & EDIT ---
@st.dialog("📋 Detail & Pengaturan Akun Karyawan", width="large")
def show_edit_user_dialog(sel_id):
    with get_db() as conn:
        res = conn.execute(text("SELECT * FROM users WHERE id = :sid"), {"sid": sel_id})
        user_row = res.fetchone()
        col_names = list(res.keys())
    
    if not user_row:
        st.error("Data user tidak ditemukan.")
        return

    user = dict(zip(col_names, user_row))

    # Layout Header
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        p_path = user['photo_path']
        if p_path and os.path.exists(p_path):
            disp_img = p_path
        else:
            disp_nm = user['full_name'] if user['full_name'] else user['username']
            disp_img = f"https://ui-avatars.com/api/?name={disp_nm}&background=028090&color=fff&size=256"
            
        # Foto Kecil
        st.image(disp_img, width=130)
        
        # Trik Perbesar Foto tanpa Nested Dialog menggunakan Expander
        with st.expander("🔍 Perbesar Foto"):
            st.image(disp_img, use_container_width=True)
            
    with c2:
        st.markdown(f"<h3 style='margin:0; color:#0F172A;'>{user['full_name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='background:#E6FFFA; color:#028090; padding:4px 10px; border-radius:6px; font-weight:800; font-size:13px;'>{user['role']}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Username Login:** `{user['username']}`")
        st.markdown(f"**Password Asli:** <span style='color:#EF4444; font-family: monospace; font-size: 16px; font-weight:bold;'>{user['password']}</span>", unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

    with st.form(f"form_edit_detailed_{sel_id}"):
        st.markdown("##### ✏️ Perbarui Data Karyawan")
        e_fullname = st.text_input("Nama Lengkap", value=user['full_name'] or "")
        e_username = st.text_input("Username Login", value=user['username'])
        
        e_password = st.text_input("Password (Terlihat)", value=user['password'])
        
        roles_lst = ["Super Admin", "Bendahara", "Kasir"]
        curr_idx = roles_lst.index(user['role']) if user['role'] in roles_lst else 2
        e_role = st.selectbox("Hak Akses (Role)", roles_lst, index=curr_idx)
        
        e_photo = st.file_uploader("Unggah Foto Profil Baru (Ganti Foto)", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("💾 Simpan Perubahan Akun", use_container_width=True, type="primary"):
            photo_url_to_save = user['photo_path']
            if e_photo is not None:
                os.makedirs("assets", exist_ok=True)
                file_path = os.path.join("assets", f"user_{e_username.strip()}.png")
                with open(file_path, "wb") as f:
                    f.write(e_photo.getbuffer())
                photo_url_to_save = file_path

            with get_db() as conn:
                with conn.begin():
                    conn.execute(text("""
                        UPDATE users 
                        SET username = :uname, full_name = :fname, password = :pwd, role = :role, photo_path = :ppath 
                        WHERE id = :sid
                    """), {
                        "uname": e_username.strip(),
                        "fname": e_fullname.strip(),
                        "pwd": e_password.strip(),
                        "role": e_role,
                        "ppath": photo_url_to_save,
                        "sid": sel_id
                    })
            st.success("✓ Perubahan akun berhasil disimpan!")
            st.rerun()

def render_page():
    if st.session_state.get('role') != "Super Admin":
        st.error("⚠️ Akses ditolak! Menu ini khusus untuk Super Admin.")
        return

    render_header("⚙️ Pengaturan & Manajemen Akun User", "Kelola data akun karyawan, ubah password, dan hak akses dengan kontrol penuh.")

    with get_db() as conn:
        try:
            users_df = pd.read_sql_query(text("SELECT * FROM users"), conn)
        except Exception:
            users_df = pd.DataFrame(columns=['id', 'username', 'full_name', 'password', 'role', 'photo_path'])

    st.markdown("""
        <style>
        .user-row {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .user-row:hover { border-color: #028090; }
        </style>
    """, unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["👥 Daftar Akun Pengguna", "➕ Tambah User Baru"])

    with tab_list:
        st.markdown('<div class="custom-card" style="background:#F8FAFC; padding:20px; border-radius:10px; border:1px solid #E2E8F0;">', unsafe_allow_html=True)
        
        search_query = st.text_input("🔍 Cari Pengguna", placeholder="Ketik nama atau username...")
        
        if not users_df.empty:
            if search_query.strip():
                mask = users_df['username'].str.contains(search_query, case=False, na=False) | users_df['full_name'].str.contains(search_query, case=False, na=False)
                filtered_df = users_df[mask]
            else:
                filtered_df = users_df

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            h1, h2, h3, h4, h5, h6 = st.columns([0.5, 1, 2.5, 1.5, 1.5, 1.5])
            h1.markdown("**ID**")
            h2.markdown("**Foto**")
            h3.markdown("**Nama Lengkap**")
            h4.markdown("**Username**")
            h5.markdown("**Password**")
            h6.markdown("<div style='text-align:center;'>**Aksi**</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 5px 0 10px 0; border: 1px solid #CBD5E1;'>", unsafe_allow_html=True)

            for _, r in filtered_df.iterrows():
                st.markdown("<div class='user-row'>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1, 2.5, 1.5, 1.5, 1.5], vertical_alignment="center")
                
                c1.markdown(f"**#{r['id']}**")
                
                p_path = r['photo_path']
                if p_path and os.path.exists(p_path):
                    from db import get_base64_image
                    b64 = get_base64_image(p_path)
                    if b64:
                        c2.markdown(f"<img src='data:image/png;base64,{b64}' style='width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #CBD5E1;'>", unsafe_allow_html=True)
                    else:
                        c2.image(p_path, width=45)
                else:
                    disp_nm = r['full_name'] if r['full_name'] else r['username']
                    c2.markdown(f"<img src='https://ui-avatars.com/api/?name={disp_nm}&background=028090&color=fff' style='width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #CBD5E1;'>", unsafe_allow_html=True)
                
                c3.markdown(f"<strong style='color:#0F172A;'>{r['full_name']}</strong><br><span style='font-size:12px; color:#028090; font-weight:700;'>{r['role']}</span>", unsafe_allow_html=True)
                c4.markdown(f"`{r['username']}`")
                c5.markdown(f"<code style='color:#EF4444; font-weight:bold;'>{r['password']}</code>", unsafe_allow_html=True)
                
                with c6:
                    if st.button("👁️ / ✏️ Detail", key=f"btn_edit_{r['id']}", use_container_width=True):
                        show_edit_user_dialog(r['id'])
                        
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Belum ada data user.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_add:
        st.markdown('<div class="custom-card" style="background:#FFFFFF; padding:20px; border-radius:10px; border:1px solid #E2E8F0;">', unsafe_allow_html=True)
        st.markdown("#### ➕ Pendaftaran Akun Karyawan Baru")

        with st.form("form_add_user_new"):
            a_username = st.text_input("Username Login *")
            a_fullname = st.text_input("Nama Lengkap *")
            
            a_password = st.text_input("Password Awal *")
            
            a_role = st.selectbox("Hak Akses (Role) *", ["Kasir", "Bendahara", "Super Admin"])
            a_photo = st.file_uploader("Unggah Foto Profil Awal (Opsional)", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("🚀 Daftarkan Karyawan", use_container_width=True, type="primary"):
                if not a_username.strip() or not a_password.strip() or not a_fullname.strip():
                    st.error("Username, Nama, dan Password wajib diisi!")
                else:
                    saved_photo_path = ""
                    if a_photo is not None:
                        os.makedirs("assets", exist_ok=True)
                        saved_photo_path = os.path.join("assets", f"user_{a_username.strip()}.png")
                        with open(saved_photo_path, "wb") as f:
                            f.write(a_photo.getbuffer())

                    try:
                        with get_db() as conn:
                            with conn.begin():
                                conn.execute(text("""
                                    INSERT INTO users (username, full_name, password, role, photo_path) 
                                    VALUES (:uname, :fname, :pwd, :role, :ppath)
                                """), {
                                    "uname": a_username.strip(),
                                    "fname": a_fullname.strip(),
                                    "pwd": a_password.strip(),
                                    "role": a_role,
                                    "ppath": saved_photo_path
                                })
                        st.success(f"✓ Akun karyawan **{a_fullname}** berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah user (Username mungkin sudah ada / duplikat): {e}")
        st.markdown('</div>', unsafe_allow_html=True)