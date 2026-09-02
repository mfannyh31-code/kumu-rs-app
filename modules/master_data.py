import streamlit as st
import sqlite3
import pandas as pd
from db import get_db, format_rupiah, render_header

# =========================================================
# MODAL EDIT KATEGORI LAYANAN (KEPALA)
# =========================================================
@st.dialog("✏️ Edit Kategori Layanan", width="small")
def edit_service_category_dialog(scat_id, current_name):
    st.markdown(f"Edit nama untuk Kategori Layanan **{current_name}**:")
    with st.form(f"form_edit_scat_{scat_id}"):
        new_name = st.text_input("Nama Kategori Layanan Baru", value=current_name)
        submitted = st.form_submit_button("Simpan Perubahan 💾", use_container_width=True)
        if submitted:
            if new_name.strip():
                conn = get_db()
                c = conn.cursor()
                try:
                    c.execute("UPDATE service_categories SET name = ? WHERE id = ?", (new_name.strip(), scat_id))
                    conn.commit()
                    conn.close()
                    st.success("Kategori layanan berhasil diubah!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Nama kategori layanan tersebut sudah ada.")
            else:
                st.warning("Nama kategori layanan tidak boleh kosong.")

# =========================================================
# MODAL KONFIRMASI HAPUS KATEGORI LAYANAN
# =========================================================
@st.dialog("⚠️ Konfirmasi Hapus Kategori Layanan", width="small")
def delete_service_category_dialog(scat_id, scat_name):
    st.markdown(f"""
        <div style="text-align:center; padding: 5px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🗑️</div>
            <div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                Apakah Anda benar-benar ingin menghapus kategori layanan <b>{scat_name}</b>?
            </div>
            <div style="font-size: 12px; color: #EF4444; font-weight: 600;">
                Unit dan tindakan di dalam kategori ini mungkin akan terpengaruh.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_scat_{scat_id}"):
            st.rerun()
    with c2:
        if st.button("Ya, Hapus", use_container_width=True, type="primary", key=f"confirm_del_scat_{scat_id}"):
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM service_categories WHERE id = ?", (scat_id,))
            conn.commit()
            conn.close()
            st.success("Kategori layanan berhasil dihapus!")
            st.rerun()

# =========================================================
# MODAL EDIT KATEGORI UNIT
# =========================================================
@st.dialog("✏️ Edit Kategori Unit", width="small")
def edit_category_dialog(cat_id, current_name, current_scat_id):
    conn = get_db()
    scat_df = pd.read_sql_query("SELECT id, name FROM service_categories ORDER BY name ASC", conn)
    conn.close()
    
    scat_list = scat_df['name'].tolist()
    curr_scat_name = scat_df[scat_df['id'] == current_scat_id]['name'].values[0] if current_scat_id in scat_df['id'].values else (scat_list[0] if scat_list else "")
    
    with st.form(f"form_edit_cat_{cat_id}"):
        sel_scat = st.selectbox("Kategori Layanan Utama", scat_list, index=scat_list.index(curr_scat_name) if curr_scat_name in scat_list else 0)
        new_name = st.text_input("Nama Kategori Unit Baru", value=current_name)
        submitted = st.form_submit_button("Simpan Perubahan 💾", use_container_width=True)
        if submitted:
            if new_name.strip():
                new_scat_id = scat_df[scat_df['name'] == sel_scat]['id'].values[0]
                conn = get_db()
                c = conn.cursor()
                try:
                    c.execute("UPDATE categories SET service_category_id = ?, name = ? WHERE id = ?", (int(new_scat_id), new_name.strip(), cat_id))
                    conn.commit()
                    conn.close()
                    st.success("Kategori unit berhasil diubah!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Nama kategori unit tersebut sudah ada.")
            else:
                st.warning("Nama kategori tidak boleh kosong.")

# =========================================================
# MODAL KONFIRMASI HAPUS KATEGORI UNIT
# =========================================================
@st.dialog("⚠️ Konfirmasi Hapus Kategori Unit", width="small")
def delete_category_dialog(cat_id, cat_name):
    st.markdown(f"""
        <div style="text-align:center; padding: 5px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🗑️</div>
            <div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                Apakah Anda benar-benar ingin menghapus kategori unit <b>{cat_name}</b>?
            </div>
            <div style="font-size: 12px; color: #EF4444; font-weight: 600;">
                Tindakan ini tidak dapat dibatalkan.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_cat_{cat_id}"):
            st.rerun()
    with c2:
        if st.button("Ya, Hapus", use_container_width=True, type="primary", key=f"confirm_del_cat_{cat_id}"):
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            st.success("Kategori unit berhasil dihapus!")
            st.rerun()

# =========================================================
# MODAL EDIT TINDAKAN & TARIF
# =========================================================
@st.dialog("✏️ Edit Tindakan & Tarif", width="medium")
def edit_action_dialog(act_id, current_cat_id, current_name, current_price):
    conn = get_db()
    all_cat_df = pd.read_sql_query("SELECT id, name FROM categories ORDER BY name ASC", conn)
    conn.close()
    
    cats_list = all_cat_df['name'].tolist()
    curr_cat_name = all_cat_df[all_cat_df['id'] == current_cat_id]['name'].values[0] if current_cat_id in all_cat_df['id'].values else (cats_list[0] if cats_list else "")
    
    with st.form(f"form_edit_act_{act_id}"):
        sel_cat = st.selectbox("Kategori Unit", cats_list, index=cats_list.index(curr_cat_name) if curr_cat_name in cats_list else 0)
        ed_name = st.text_input("Nama Tindakan", value=current_name)
        ed_price = st.number_input("Tarif Standar (Rp)", min_value=0.0, value=float(current_price), step=10000.0, format="%.0f")
        
        submitted = st.form_submit_button("Simpan Perubahan 💾", use_container_width=True)
        if submitted:
            if ed_name.strip() and ed_price > 0:
                new_cat_id = all_cat_df[all_cat_df['name'] == sel_cat]['id'].values[0]
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE actions SET category_id = ?, name = ?, price = ? WHERE id = ?", (int(new_cat_id), ed_name.strip(), ed_price, act_id))
                conn.commit()
                conn.close()
                st.success("Tindakan berhasil diupdate!")
                st.rerun()
            else:
                st.warning("Lengkapi data dengan benar.")

# =========================================================
# MODAL KONFIRMASI HAPUS TINDAKAN
# =========================================================
@st.dialog("⚠️ Konfirmasi Hapus Tindakan", width="small")
def delete_action_dialog(act_id, act_name):
    st.markdown(f"""
        <div style="text-align:center; padding: 5px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🗑️</div>
            <div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                Apakah Anda benar-benar ingin menghapus tindakan <b>{act_name}</b>?
            </div>
            <div style="font-size: 12px; color: #EF4444; font-weight: 600;">
                Tindakan ini tidak dapat dibatalkan.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_act_{act_id}"):
            st.rerun()
    with c2:
        if st.button("Ya, Hapus", use_container_width=True, type="primary", key=f"confirm_del_act_{act_id}"):
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM actions WHERE id = ?", (act_id,))
            conn.commit()
            conn.close()
            st.success("Tindakan berhasil dihapus!")
            st.rerun()

# =========================================================
# HALAMAN UTAMA MASTER DATA
# =========================================================
def render_page():
    conn = get_db()
    render_header("⚙️ Kelola Master Data Layanan", "Penambahan, pencarian, dan pengaturan kategori layanan, kategori unit, serta tarif tindakan")

    st.markdown("""
        <style>
        .master-box-title { font-size: 14px; font-weight: 800; color: #0F172A; margin-bottom: 6px; }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] { height: 38px; font-weight: 700; font-size: 13px; border-radius: 6px 6px 0 0; padding: 0 12px; color: #475569; }
        .stTabs [aria-selected="true"] { color: #028090 !important; border-bottom: 3px solid #028090 !important; }
        
        .compact-container {
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }

        .master-row-card {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 4px !important;
            padding: 4px 10px !important;
            margin-bottom: 3px !important;
            font-size: 13px !important;
        }
        .master-row-card:hover {
            background-color: #F8FAFC !important;
        }
        .master-row-card div[data-testid="column"] {
            display: flex;
            align-items: center;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
        .master-row-card div[data-testid="column"] div.stButton {
            margin-bottom: 0px !important;
        }
        .master-row-card div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            height: 24px !important;
            min-height: 24px !important;
            font-size: 11px !important;
            border-radius: 3px !important;
            padding: 0px !important;
            border: none !important;
            color: #FFFFFF !important;
        }
        .btn-act-edit button { background-color: #F59E0B !important; }
        .btn-act-del button { background-color: #EF4444 !important; }
        </style>
    """, unsafe_allow_html=True)

    tab_scat, tab_cat, tab_act = st.tabs([
        "🏷️ Master Kategori Layanan", 
        "📁 Master Kategori Unit", 
        "💉 Master Tindakan & Tarif"
    ])

    # =========================================================
    # TAB 1: MASTER KATEGORI LAYANAN (KEPALA)
    # =========================================================
    with tab_scat:
        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Tambah Kategori Layanan Utama Baru</div>", unsafe_allow_html=True)
        
        c_form1, c_form2 = st.columns([4, 1])
        with c_form1:
            new_scat_name = st.text_input("Nama Kategori Layanan", placeholder="Contoh: Rawat Jalan, Rawat Inap", key="input_new_scat", label_visibility="collapsed")
        with c_form2:
            if st.button("Simpan ➕", use_container_width=True, type="primary", key="btn_save_scat"):
                if new_scat_name.strip():
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO service_categories (name) VALUES (?)", (new_scat_name.strip(),))
                        conn.commit()
                        conn.close()
                        st.success(f"Kategori layanan '{new_scat_name.strip()}' ditambahkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Kategori layanan tersebut sudah terdaftar.")
                else:
                    st.warning("Nama tidak boleh kosong.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Daftar Kategori Layanan Aktif</div>", unsafe_allow_html=True)
        
        search_scat_kw = st.text_input("🔍 Cari Kategori Layanan...", placeholder="Ketik nama...", key="search_scat_box", label_visibility="collapsed")
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        query_scat = "SELECT id, name FROM service_categories"
        params_scat = []
        if search_scat_kw.strip():
            query_scat += " WHERE name LIKE ?"
            params_scat.append(f"%{search_scat_kw.strip()}%")
        query_scat += " ORDER BY name ASC"
        
        scat_df = pd.read_sql_query(query_scat, conn, params=params_scat)
        
        if not scat_df.empty:
            st.markdown("""
                <div style="background:#028090; color:white; padding:6px 10px; border-radius:4px; font-weight:700; font-size:12.5px; margin-bottom:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="width:10%;">ID</span>
                        <span style="width:78%;">Nama Kategori Layanan Utama</span>
                        <span style="width:12%; text-align:center;">Aksi</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for idx, r in scat_df.iterrows():
                scat_id = r['id']
                scat_name = r['name']
                
                st.markdown('<div class="master-row-card">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([0.8, 7.2, 1.0, 1.0])
                with col1:
                    st.markdown(f"<b>#{scat_id}</b>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<b>{scat_name}</b>", unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="btn-act-edit">', unsafe_allow_html=True)
                    if st.button("✏️", key=f"ed_scat_{scat_id}", help="Edit", use_container_width=True):
                        edit_service_category_dialog(scat_id, scat_name)
                    st.markdown('</div>', unsafe_allow_html=True)
                with col4:
                    st.markdown('<div class="btn-act-del">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_scat_{scat_id}", help="Hapus", use_container_width=True):
                        delete_service_category_dialog(scat_id, scat_name)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Kategori layanan tidak ditemukan.")
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================
    # TAB 2: MASTER KATEGORI UNIT
    # =========================================================
    with tab_cat:
        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Tambah Kategori Unit Baru</div>", unsafe_allow_html=True)
        
        scat_opt_df = pd.read_sql_query("SELECT id, name FROM service_categories ORDER BY name ASC", conn)
        
        if not scat_opt_df.empty:
            c_form1, c_form2, c_form3 = st.columns([2, 2.5, 1])
            with c_form1:
                parent_scat_name = st.selectbox("Kategori Layanan", scat_opt_df['name'].tolist(), key="select_parent_scat", label_visibility="collapsed")
            with c_form2:
                new_cat_name = st.text_input("Nama Kategori Unit", placeholder="Contoh: Poli Mata", key="input_new_cat", label_visibility="collapsed")
            with c_form3:
                if st.button("Simpan ➕", use_container_width=True, type="primary", key="btn_save_cat"):
                    if new_cat_name.strip():
                        parent_scat_id = scat_opt_df[scat_opt_df['name'] == parent_scat_name]['id'].values[0]
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO categories (service_category_id, name) VALUES (?, ?)", (int(parent_scat_id), new_cat_name.strip()))
                            conn.commit()
                            conn.close()
                            st.success(f"Unit '{new_cat_name.strip()}' ditambahkan!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Kategori unit tersebut sudah ada.")
                    else:
                        st.warning("Nama tidak boleh kosong.")
        else:
            st.warning("⚠️ Harap buat 'Master Kategori Layanan' terlebih dahulu pada tab sebelumnya.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Daftar Kategori Unit Aktif</div>", unsafe_allow_html=True)
        
        search_cat_kw = st.text_input("🔍 Cari Kategori Unit...", placeholder="Ketik nama unit...", key="search_cat_box", label_visibility="collapsed")
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        query_cat = """
            SELECT c.id as cat_id, c.name as cat_name, s.name as scat_name, c.service_category_id as scat_id
            FROM categories c
            LEFT JOIN service_categories s ON c.service_category_id = s.id
            WHERE 1=1
        """
        params_cat = []
        if search_cat_kw.strip():
            query_cat += " AND c.name LIKE ?"
            params_cat.append(f"%{search_cat_kw.strip()}%")
        query_cat += " ORDER BY s.name ASC, c.name ASC"
        
        cats_df = pd.read_sql_query(query_cat, conn, params=params_cat)
        
        if not cats_df.empty:
            st.markdown("""
                <div style="background:#028090; color:white; padding:6px 10px; border-radius:4px; font-weight:700; font-size:12.5px; margin-bottom:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="width:30%;">Kategori Layanan Utama</span>
                        <span style="width:58%;">Nama Kategori Unit</span>
                        <span style="width:12%; text-align:center;">Aksi</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for idx, r in cats_df.iterrows():
                cid = r['cat_id']
                cname = r['cat_name']
                scat_name = r['scat_name'] or '-'
                scat_id = r['scat_id']
                
                st.markdown('<div class="master-row-card">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3.0, 5.8, 1.0, 1.0])
                with col1:
                    st.markdown(f"<b>{scat_name}</b>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<b>{cname}</b>", unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="btn-act-edit">', unsafe_allow_html=True)
                    if st.button("✏️", key=f"ed_cat_{cid}", help="Edit", use_container_width=True):
                        edit_category_dialog(cid, cname, scat_id)
                    st.markdown('</div>', unsafe_allow_html=True)
                with col4:
                    st.markdown('<div class="btn-act-del">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_cat_{cid}", help="Hapus", use_container_width=True):
                        delete_category_dialog(cid, cname)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Kategori unit tidak ditemukan.")
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================
    # TAB 3: MASTER TINDAKAN & TARIF
    # =========================================================
    with tab_act:
        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Tambah Tindakan & Tarif Baru</div>", unsafe_allow_html=True)
        all_cat_df = pd.read_sql_query("SELECT id, name FROM categories ORDER BY name ASC", conn)
        
        if not all_cat_df.empty:
            ac1, ac2, ac3, ac4 = st.columns([1.5, 2.2, 1.2, 0.8])
            with ac1:
                target_cat = st.selectbox("Unit", all_cat_df['name'].tolist(), key="select_cat_parent", label_visibility="collapsed")
            with ac2:
                act_name = st.text_input("Nama Tindakan", placeholder="Nama tindakan...", key="input_new_act_name", label_visibility="collapsed")
            with ac3:
                act_price = st.number_input("Tarif", min_value=0.0, step=10000.0, format="%.0f", key="input_new_act_price", label_visibility="collapsed")
            with ac4:
                if st.button("Simpan ➕", use_container_width=True, type="primary", key="btn_save_act"):
                    if act_name.strip() and act_price > 0:
                        c_id = all_cat_df[all_cat_df['name'] == target_cat]['id'].values[0]
                        c = conn.cursor()
                        c.execute("INSERT INTO actions (category_id, name, price) VALUES (?, ?, ?)", (int(c_id), act_name.strip(), act_price))
                        conn.commit()
                        conn.close()
                        st.success("Disimpan!")
                        st.rerun()
                    else:
                        st.warning("Lengkapi!")
        else:
            st.warning("⚠️ Harap tambahkan 'Kategori Unit' terlebih dahulu.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="compact-container">', unsafe_allow_html=True)
        st.markdown("<div class='master-box-title'>Katalog Tarif Layanan & Tindakan</div>", unsafe_allow_html=True)
        
        f_col1, f_col2 = st.columns([2, 1.5])
        with f_col1:
            search_act_kw = st.text_input("🔍 Cari Tindakan...", placeholder="Ketik tindakan...", key="search_act_box", label_visibility="collapsed")
        with f_col2:
            cat_filter_options = ["Semua Kategori Unit"] + (all_cat_df['name'].tolist() if not all_cat_df.empty else [])
            selected_cat_filter = st.selectbox("Filter Unit", cat_filter_options, key="filter_cat_select", label_visibility="collapsed")
            
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        query_acts = """
            SELECT a.id as act_id, a.category_id as cat_id, c.name as cat_name, a.name as act_name, a.price as act_price
            FROM actions a 
            JOIN categories c ON a.category_id = c.id
            WHERE 1=1
        """
        params_acts = []
        if search_act_kw.strip():
            query_acts += " AND a.name LIKE ?"
            params_acts.append(f"%{search_act_kw.strip()}%")
        if selected_cat_filter != "Semua Kategori Unit":
            query_acts += " AND c.name = ?"
            params_acts.append(selected_cat_filter)
            
        query_acts += " ORDER BY c.name ASC, a.name ASC"
        acts_df = pd.read_sql_query(query_acts, conn, params=params_acts)
        
        if not acts_df.empty:
            st.markdown("""
                <div style="background:#028090; color:white; padding:6px 10px; border-radius:4px; font-weight:700; font-size:12.5px; margin-bottom:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="width:25%;">Kategori Unit</span>
                        <span style="width:48%;">Nama Tindakan / Layanan</span>
                        <span style="width:17%; text-align:right;">Tarif Standar</span>
                        <span style="width:10%; text-align:center;">Aksi</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for idx, r in acts_df.iterrows():
                aid = r['act_id']
                acid = r['cat_id']
                aname = r['act_name']
                aprice = r['act_price']
                
                st.markdown('<div class="master-row-card">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([2.5, 4.8, 1.8, 0.7, 0.7])
                with col1:
                    st.markdown(f"<b>{r['cat_name']}</b>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"{aname}", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='text-align:right; font-weight:700; color:#028090;'>{format_rupiah(aprice)}</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown('<div class="btn-act-edit">', unsafe_allow_html=True)
                    if st.button("✏️", key=f"ed_act_{aid}", help="Edit", use_container_width=True):
                        edit_action_dialog(aid, acid, aname, aprice)
                    st.markdown('</div>', unsafe_allow_html=True)
                with col5:
                    st.markdown('<div class="btn-act-del">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_act_{aid}", help="Hapus", use_container_width=True):
                        delete_action_dialog(aid, aname)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Tidak ada data tindakan ditemukan.")
        st.markdown('</div>', unsafe_allow_html=True)

    conn.close()