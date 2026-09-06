import streamlit as st
import pandas as pd
import os
from sqlalchemy import text
from db import get_db, render_header

# --- MODAL DETAIL & EDIT ---
@st.dialog("📋 Detail & Pengaturan Akun Karyawan", width="large")
def show_edit_user_dialog(sel_id):
    conn = get_db()
    try:
        user_res = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": sel_id})
        user = user_res.mappings().fetchone()
    except Exception:
        user = None

    if not user:
        st.error("Data user tidak ditemukan.")
        conn.close()
        return

    # Layout Header
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        p_path = user['photo_path']
        if p_path and os.path.exists(p_path):
            disp_img = p_path
        else:
            disp_nm = user['full_name'] if user['full_name'] else user['username']
            disp_img = f"https://ui-avatars.com/api/?name={disp_nm}&background=028090&color=fff&size=256"
            
        st.image(disp_img, width=130)
        
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
        
        roles_lst = ["Kasir", "Bendahara", "Manajer", "Asisten Manajer", "Staff Piutang", "Super Admin"]
        curr_role = user['role']
        if curr_role not in roles_lst:
            roles_lst.append(curr_role)
            
        e_role = st.selectbox("Hak Akses (Role / Jabatan)", roles_lst, index=roles_lst.index(curr_role) if curr_role in roles_lst else 0)
        
        e_photo = st.file_uploader("Unggah Foto Profil Baru (Ganti Foto)", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("💾 Simpan Perubahan Akun", use_container_width=True, type="primary"):
            photo_url_to_save = user['photo_path']
            if e_photo is not None:
                os.makedirs("assets", exist_ok=True)
                file_path = os.path.join("assets", f"user_{e_username.strip()}.png")
                with open(file_path, "wb") as f:
                    f.write(e_photo.getbuffer())
                photo_url_to_save = file_path

            try:
                conn.execute(text("""
                    UPDATE users 
                    SET username = :username, full_name = :full_name, password = :password, role = :role, photo_path = :photo_path 
                    WHERE id = :id
                """), {
                    "username": e_username.strip(),
                    "full_name": e_fullname.strip(),
                    "password": e_password.strip(),
                    "role": e_role,
                    "photo_path": photo_url_to_save,
                    "id": sel_id
                })
                conn.commit()
                st.success("✓ Perubahan akun berhasil disimpan!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Gagal menyimpan perubahan: {e}")
            finally:
                conn.close()

# --- MODAL KONFIRMASI HAPUS USER ---
@st.dialog("⚠️ Konfirmasi Hapus Akun Pengguna", width="small")
def delete_user_dialog(user_id, username):
    st.markdown(f"""
        <div style="text-align:center; padding: 5px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🗑️</div>
            <div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                Apakah Anda benar-benar ingin menghapus akun <b>{username}</b>?
            </div>
            <div style="font-size: 12px; color: #EF4444; font-weight: 600;">
                Tindakan ini tidak dapat dibatalkan secara permanen.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_user_{user_id}"):
            st.rerun()
    with c2:
        if st.button("Ya, Hapus", use_container_width=True, type="primary", key=f"confirm_del_user_{user_id}"):
            conn = get_db()
            try:
                conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
                conn.commit()
                conn.close()
                st.success("Akun pengguna berhasil dihapus!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                conn.close()
                st.error(f"Gagal menghapus akun: {e}")

def render_page():
    if st.session_state.get('role') != "Super Admin":
        st.error("⚠️ Akses ditolak! Menu ini khusus untuk Super Admin.")
        return

    render_header("⚙️ Pengaturan & Manajemen Akun User", "Kelola data akun karyawan, ubah password, hak akses, sembunyikan, atau hapus akun.")

    conn = get_db()

    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                full_name TEXT,
                password TEXT,
                role TEXT,
                photo_path TEXT,
                status TEXT DEFAULT 'ACTIVE'
            )
        """))
        conn.commit()
    except Exception:
        conn.rollback()

    try:
        res_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'")).fetchall()
        u_cols = [row[0] for row in res_cols]
        if "photo_path" not in u_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN photo_path TEXT"))
            conn.commit()
        if "status" not in u_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'ACTIVE'"))
            conn.commit()
    except Exception:
        conn.rollback()

    try:
        users_df = pd.read_sql_query("SELECT * FROM users ORDER BY id ASC", conn)
    except Exception:
        users_df = pd.DataFrame(columns=['id', 'username', 'full_name', 'password', 'role', 'photo_path', 'status'])

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
        .btn-act-edit button { background-color: #F59E0B !important; color: #FFF !important; }
        .btn-act-hide button { background-color: #64748B !important; color: #FFF !important; }
        .btn-act-del button { background-color: #EF4444 !important; color: #FFF !important; }
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

            h1, h2, h3, h4, h5, h6, h7 = st.columns([0.5, 1, 2.2, 1.2, 1.2, 1.0, 1.4])
            h1.markdown("**ID**")
            h2.markdown("**Foto**")
            h3.markdown("**Nama Lengkap**")
            h4.markdown("**Username**")
            h5.markdown("**Status**")
            h6.markdown("**Edit**")
            h7.markdown("<div style='text-align:center;'>**Aksi Lain**</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 5px 0 10px 0; border: 1px solid #CBD5E1;'>", unsafe_allow_html=True)

            for _, r in filtered_df.iterrows():
                st.markdown("<div class='user-row'>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1, 2.2, 1.2, 1.2, 1.0, 1.4], vertical_alignment="center")
                
                c1.markdown(f"**#{r['id']}**")
                
                p_path = r['photo_path']
                if p_path and os.path.exists(p_path):
                    from db import get_base64_image
                    b64 = get_base64_image(p_path)
                    if b64:
                        c2.markdown(f"<img src='data:image/png;base64,{b64}' style='width:42px; height:42px; border-radius:50%; object-fit:cover; border:2px solid #CBD5E1;'>", unsafe_allow_html=True)
                    else:
                        c2.image(p_path, width=42)
                else:
                    disp_nm = r['full_name'] if r['full_name'] else r['username']
                    c2.markdown(f"<img src='https://ui-avatars.com/api/?name={disp_nm}&background=028090&color=fff' style='width:42px; height:42px; border-radius:50%; object-fit:cover; border:2px solid #CBD5E1;'>", unsafe_allow_html=True)
                
                user_status = r.get('status', 'ACTIVE') or 'ACTIVE'
                is_hidden = user_status == 'HIDDEN'
                status_badge = "<span style='background:#EF4444; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>HIDDEN</span>" if is_hidden else "<span style='background:#10B981; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>ACTIVE</span>"

                c3.markdown(f"<span style='{'color:#94A3B8; text-decoration:line-through;' if is_hidden else 'color:#0F172A;'}'><strong>{r['full_name']}</strong></span><br><span style='font-size:11.5px; color:#028090; font-weight:700;'>{r['role']}</span>", unsafe_allow_html=True)
                c4.markdown(f"`{r['username']}`")
                c5.markdown(f"<div style='text-align:center;'>{status_badge}</div>", unsafe_allow_html=True)
                
                with c6:
                    st.markdown('<div class="btn-act-edit">', unsafe_allow_html=True)
                    if st.button("✏️ Edit", key=f"btn_edit_{r['id']}", use_container_width=True):
                        show_edit_user_dialog(r['id'])
                    st.markdown('</div>', unsafe_allow_html=True)
                        
                with c7:
                    sub_c1, sub_c2 = st.columns(2)
                    with sub_c1:
                        st.markdown('<div class="btn-act-hide">', unsafe_allow_html=True)
                        hide_label = "👁️" if is_hidden else "🔒"
                        if st.button(hide_label, key=f"hide_user_{r['id']}", help="Sembunyikan / Tampilkan", use_container_width=True):
                            new_st = 'ACTIVE' if is_hidden else 'HIDDEN'
                            try:
                                conn.execute(text("UPDATE users SET status = :status WHERE id = :id"), {"status": new_st, "id": r['id']})
                                conn.commit()
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Gagal update status: {e}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with sub_c2:
                        st.markdown('<div class="btn-act-del">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_user_{r['id']}", help="Hapus Akun", use_container_width=True):
                            delete_user_dialog(r['id'], r['username'])
                        st.markdown('</div>', unsafe_allow_html=True)

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
            
            # Opsi role pilihan dropdown atau input manual jika jabatan lain
            role_options = ["Kasir", "Bendahara", "Manajer", "Asisten Manajer", "Staff Piutang", "Super Admin", "Lainnya (Ketik Manual)"]
            selected_role_option = st.selectbox("Hak Akses (Role) *", role_options)
            
            if selected_role_option == "Lainnya (Ketik Manual)":
                a_role = st.text_input("Masukkan Nama Jabatan / Role Baru *").strip()
            else:
                a_role = selected_role_option

            a_photo = st.file_uploader("Unggah Foto Profil Awal (Opsional)", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("🚀 Daftarkan Karyawan", use_container_width=True, type="primary"):
                if not a_username.strip() or not a_password.strip() or not a_fullname.strip() or not a_role:
                    st.error("Semua kolom bertanda bintang (*) wajib diisi dengan benar!")
                else:
                    saved_photo_path = ""
                    if a_photo is not None:
                        os.makedirs("assets", exist_ok=True)
                        saved_photo_path = os.path.join("assets", f"user_{a_username.strip()}.png")
                        with open(saved_photo_path, "wb") as f:
                            f.write(a_photo.getbuffer())

                    try:
                        conn.execute(text("""
                            INSERT INTO users (username, full_name, password, role, photo_path, status) 
                            VALUES (:username, :full_name, :password, :role, :photo_path, 'ACTIVE')
                        """), {
                            "username": a_username.strip(),
                            "full_name": a_fullname.strip(),
                            "password": a_password.strip(),
                            "role": a_role,
                            "photo_path": saved_photo_path
                        })
                        conn.commit()
                        st.success(f"✓ Akun karyawan **{a_fullname}** dengan jabatan **{a_role}** berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Gagal menambah user (Username mungkin sudah ada / duplikat): {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    conn.close()