import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header

def render_page():
    render_header("➕ Input Piutang Baru", "Catat piutang pasien berdasarkan pemilihan hirarki layanan (Layanan ➔ Unit ➔ Tindakan) atau input manual.")

    if st.button("⬅️ Kembali ke Daftar Piutang"):
        st.session_state.current_menu = "piutang"
        st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    input_mode = st.radio("Pilih Metode Input Piutang", ["Berdasarkan Tindakan & Unit Layanan", "Input Manual Bebas"], horizontal=True)
    st.markdown("---")

    conn = get_db()
    c = conn.cursor()

    try:
        # Ambil data master hirarki dari database
        service_cats_df = pd.read_sql_query("SELECT id, name FROM service_categories ORDER BY name ASC", conn)
        scats_list = ["Select"] + service_cats_df['name'].tolist() if not service_cats_df.empty else ["Select"]

        categories_df = pd.read_sql_query("SELECT id, service_category_id, name FROM categories ORDER BY name ASC", conn)
        actions_df = pd.read_sql_query("SELECT id, category_id, name, price FROM actions ORDER BY name ASC", conn)
    except:
        scats_list = ["Select"]
        service_cats_df = pd.DataFrame()
        categories_df = pd.DataFrame()
        actions_df = pd.DataFrame()

    if 'piu_form_cnt' not in st.session_state: st.session_state.piu_form_cnt = 0
    cnt = st.session_state.piu_form_cnt

    rm_key = f"piu_rm_{cnt}"
    name_key = f"piu_name_{cnt}"

    if rm_key not in st.session_state: st.session_state[rm_key] = ""
    if name_key not in st.session_state: st.session_state[name_key] = ""

    # Callback Auto-fill Nama berdasarkan database
    def update_patient_name():
        rm_val = st.session_state.get(rm_key, "").strip()
        if rm_val:
            db_c = get_db()
            res = db_c.cursor().execute("SELECT patient_name FROM deposits WHERE patient_id = ? LIMIT 1", (rm_val,)).fetchone()
            if not res:
                res = db_c.cursor().execute("SELECT patient_name FROM receivables WHERE patient_id = ? LIMIT 1", (rm_val,)).fetchone()
            if res:
                st.session_state[name_key] = res[0]
            db_c.close()

    c1, c2, c3 = st.columns(3)
    with c1: no_ref = st.text_input("No. Kuitansi / Ref *", placeholder="PIU-001")
    with c2: norm = st.text_input("No. Rekam Medis (RM)", placeholder="RM-XXXX", key=rm_key, on_change=update_patient_name)
    with c3: nama_pasien = st.text_input("Nama Pasien *", placeholder="Nama lengkap...", key=name_key)

    c4, c5 = st.columns(2)
    with c4: tgl_piutang = st.date_input("Tanggal Piutang", datetime.today())
    with c5: due_date = st.date_input("Tanggal Jatuh Tempo", datetime.today())

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📌 Rincian Item Tagihan Piutang")

    if 'piutang_rows' not in st.session_state: st.session_state.piutang_rows = [1]
    if 'piutang_next_id' not in st.session_state: st.session_state.piutang_next_id = 2

    if st.button("➕ Tambah Baris Item"):
        st.session_state.piutang_rows.append(st.session_state.piutang_next_id)
        st.session_state.piutang_next_id += 1
        st.rerun()

    items_list = []
    total_piutang_baru = 0.0

    for r_id in list(st.session_state.piutang_rows):
        st.markdown(f"<div style='background:#F8FAFC; padding:12px; border-radius:8px; border:1.5px solid #CBD5E1; margin-bottom:10px;'>", unsafe_allow_html=True)
        
        if input_mode == "Berdasarkan Tindakan & Unit Layanan":
            rc1, rc2, rc3, rc4, rc5 = st.columns([1.5, 1.8, 1.8, 2.0, 0.4])
            
            with rc1: 
                scat_val = st.selectbox("Kategori Layanan", scats_list, key=f"piu_scat_{r_id}_{cnt}")
            
            # Filter Unit berdasarkan Kategori Layanan Utama
            sub_units = ["Select Unit"]
            selected_scat_id = None
            if scat_val != "Select" and not service_cats_df.empty:
                m_scat = service_cats_df[service_cats_df['name'] == scat_val]
                if not m_scat.empty:
                    selected_scat_id = m_scat['id'].values[0]
                    sub_units += categories_df[categories_df['service_category_id'] == selected_scat_id]['name'].tolist()

            with rc2: 
                unit_val = st.selectbox("Unit Layanan", sub_units, key=f"piu_unit_{r_id}_{cnt}")
            
            # Filter Tindakan berdasarkan Unit Layanan
            sub_acts = ["Select Tindakan"]
            selected_cat_id = None
            if unit_val != "Select Unit" and not categories_df.empty:
                m_cat = categories_df[categories_df['name'] == unit_val]
                if not m_cat.empty:
                    selected_cat_id = m_cat['id'].values[0]
                    sub_acts += actions_df[actions_df['category_id'] == selected_cat_id]['name'].tolist()
                
            with rc3: 
                act_val = st.selectbox("Jenis Tindakan", sub_acts, key=f"piu_act_{r_id}_{cnt}")
            
            default_p = 0.0
            if act_val != "Select Tindakan" and selected_cat_id is not None:
                m_act = actions_df[(actions_df['category_id'] == selected_cat_id) & (actions_df['name'] == act_val)]
                if not m_act.empty: 
                    default_p = float(m_act['price'].values[0])
                
            with rc4: 
                price_val = st.number_input("Nominal (Rp)", min_value=0.0, value=default_p, step=1000.0, format="%.0f", key=f"piu_price_{r_id}_{cnt}")
            with rc5:
                st.write("")
                st.write("")
                if st.button("❌", key=f"piu_del_{r_id}_{cnt}"):
                    if len(st.session_state.piutang_rows) > 1:
                        st.session_state.piutang_rows.remove(r_id)
                        st.rerun()
            
            cat_final = unit_val if unit_val != "Select Unit" else "UMUM"
            act_final = act_val if act_val != "Select Tindakan" else "Tindakan Medis"
        else:
            rc1, rc2, rc3 = st.columns([3, 1.5, 0.5])
            with rc1: uraian_man = st.text_input("Uraian / Keterangan Tagihan *", placeholder="Contoh: Biaya administrasi...", key=f"man_act_{r_id}_{cnt}")
            with rc2: price_val = st.number_input("Nominal (Rp)", min_value=0.0, value=0.0, step=1000.0, format="%.0f", key=f"man_price_{r_id}_{cnt}")
            with rc3:
                st.write("")
                if st.button("❌", key=f"man_del_{r_id}_{cnt}"):
                    if len(st.session_state.piutang_rows) > 1:
                        st.session_state.piutang_rows.remove(r_id)
                        st.rerun()
            cat_final = "MANUAL"
            act_final = uraian_man if uraian_man.strip() else "Tagihan Manual"

        notes_val = st.text_input("Catatan Item (Opsional)", placeholder="Keterangan tambahan...", key=f"piu_note_{r_id}_{cnt}")
        st.markdown("</div>", unsafe_allow_html=True)

        total_piutang_baru += price_val
        items_list.append({
            "unit": cat_final,
            "action": act_final,
            "amount": price_val,
            "notes": notes_val
        })

    st.markdown(f"<div style='text-align:right; font-size:16px; font-weight:800; margin:15px 0;'>Total Tagihan Piutang: <span style='color:#EF4444; font-size:22px;'>{format_rupiah(total_piutang_baru)}</span></div>", unsafe_allow_html=True)
    catatan_umum = st.text_area("Catatan Piutang Keseluruhan", key=f"piu_notes_all_{cnt}")

    if st.button("💾 Simpan Data Piutang", type="primary", use_container_width=True):
        final_nama = st.session_state.get(name_key, "").strip() or nama_pasien.strip()
        if not no_ref.strip() or not final_nama or total_piutang_baru <= 0:
            st.error("⚠️ No. Ref, Nama Pasien, dan Total Nominal Piutang wajib diisi dengan benar!")
        else:
            try:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS receivables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_no TEXT, patient_id TEXT, patient_name TEXT, 
                        total_bill REAL, paid_amount REAL, remaining_debt REAL, due_date TEXT, status TEXT, notes TEXT, input_by TEXT
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS receivables_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER, category_name TEXT, action_name TEXT, 
                        amount REAL, paid_status TEXT, notes TEXT
                    )
                """)
                c.execute("""
                    INSERT INTO receivables (receipt_no, patient_id, patient_name, total_bill, paid_amount, remaining_debt, due_date, status, notes, input_by)
                    VALUES (?, ?, ?, ?, 0.0, ?, ?, 'Belum Lunas', ?, ?)
                """, (no_ref.strip(), norm.strip(), final_nama, total_piutang_baru, total_piutang_baru, str(due_date), catatan_umum, str(st.session_state.get('user', 'ADMIN')).upper()))
                
                debt_id = c.lastrowid
                for itm in items_list:
                    c.execute("""
                        INSERT INTO receivables_items (debt_id, category_name, action_name, amount, paid_status, notes)
                        VALUES (?, ?, ?, ?, 'Belum Lunas', ?)
                    """, (debt_id, itm['unit'], itm['action'], itm['amount'], itm['notes']))

                conn.commit()
                conn.close()
                st.success("✓ Data piutang berhasil dicatat!")
                st.session_state.piutang_rows = [1]
                st.session_state.piu_form_cnt += 1
                st.session_state.current_menu = "piutang"
                st.rerun()
            except Exception as e:
                conn.close()
                st.error(f"Gagal menyimpan: {e}")
    conn.close()