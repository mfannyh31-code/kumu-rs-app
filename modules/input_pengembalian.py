import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header

def render_page():
    render_header("➕ Input Pengembalian Dana (Refund)", "Catat pengembalian dana dengan pemilihan hierarki layanan (Layanan ➔ Unit ➔ Tindakan).")

    if st.button("⬅️ Kembali ke Daftar Pengembalian"):
        st.session_state.current_menu = "pengembalian"
        st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    
    tab_kuitansi, tab_manual = st.tabs(["📄 Refund Kuitansi", "📑 Refund Manual (Mandiri)"])

    conn = get_db()

    # ==========================================
    # TAB 1: REFUND KUITANSI
    # ==========================================
    with tab_kuitansi:
        if 'rf_form_reset_cnt' not in st.session_state:
            st.session_state.rf_form_reset_cnt = 0
        cnt = st.session_state.rf_form_reset_cnt

        if 'rf_rows_list' not in st.session_state:
            st.session_state.rf_rows_list = [1]
        if 'rf_next_row_id' not in st.session_state:
            st.session_state.rf_next_row_id = 2

        try:
            service_cats_df = pd.read_sql_query("SELECT id, name FROM service_categories ORDER BY name ASC", conn)
            scats_list = ["Select"] + service_cats_df['name'].tolist() if not service_cats_df.empty else ["Select"]

            categories_df = pd.read_sql_query("SELECT id, service_category_id, name FROM categories ORDER BY name ASC", conn)
            actions_df = pd.read_sql_query("SELECT id, category_id, name, price FROM actions ORDER BY name ASC", conn)
        except Exception:
            scats_list = ["Select"]
            service_cats_df = pd.DataFrame()
            categories_df = pd.DataFrame()
            actions_df = pd.DataFrame()

        st.markdown("##### 📄 Informasi Dokumen Pengembalian")
        h1, h2, h3 = st.columns([1.5, 1.5, 1.5])
        with h1:
            no_urut_kertas = st.text_input("No. Kertas / Referensi *", placeholder="Contoh: REF-308678", key=f"rf_rcpt_{cnt}")
        with h2:
            tgl_kuitansi = st.date_input("Tanggal Pengembalian *", value=datetime.today(), key=f"rf_date_{cnt}")
        with h3:
            shift_val = st.selectbox("Shift *", ["Pagi", "Sore", "Malam"], key=f"rf_shift_{cnt}")

        st.markdown("<hr style='margin:12px 0; border:none; border-top:1.5px solid #CBD5E1;'>", unsafe_allow_html=True)
        st.markdown("##### 💉 Rincian Tindakan & Layanan yang Direfund")

        if st.button("➕ Tambah Baris Tindakan", use_container_width=False, key=f"rf_add_row_{cnt}"):
            st.session_state.rf_rows_list.append(st.session_state.rf_next_row_id)
            st.session_state.rf_next_row_id += 1
            st.rerun()

        items_data = []
        grand_total_actions = 0.0

        for row_id in list(st.session_state.rf_rows_list):
            st.markdown("<div style='background:#F8FAFC; border:1.5px solid #CBD5E1; padding:14px 18px; border-radius:10px; margin-bottom:12px;'>", unsafe_allow_html=True)

            f_top1, f_top2, f_top3, f_top4, f_top5 = st.columns([1.1, 1.8, 1.8, 2.3, 0.4])
            with f_top1:
                bk_val = st.text_input("No. Bukti", placeholder="BK-01", key=f"rf_bk_{row_id}_{cnt}")
            with f_top2:
                scat_val = st.selectbox("Kategori Layanan", scats_list, key=f"rf_scat_{row_id}_{cnt}")

            # Filter Unit berdasarkan Layanan
            sub_units = ["Select"]
            selected_scat_id = None
            if scat_val != "Select" and not service_cats_df.empty:
                m_scat = service_cats_df[service_cats_df['name'] == scat_val]
                if not m_scat.empty:
                    selected_scat_id = m_scat['id'].values[0]
                    sub_units += categories_df[categories_df['service_category_id'] == selected_scat_id]['name'].tolist()

            with f_top3:
                cat_val = st.selectbox("Unit Layanan", sub_units, key=f"rf_cat_{row_id}_{cnt}")

            # Filter Tindakan berdasarkan Unit
            sub_acts = ["Select"]
            selected_cat_id = None
            if cat_val != "Select" and not categories_df.empty:
                m_cat = categories_df[categories_df['name'] == cat_val]
                if not m_cat.empty:
                    selected_cat_id = m_cat['id'].values[0]
                    sub_acts += actions_df[actions_df['category_id'] == selected_cat_id]['name'].tolist()

            with f_top4:
                act_val = st.selectbox("Jenis Tindakan", sub_acts, key=f"rf_act_{row_id}_{cnt}")

            with f_top5:
                st.write("")
                st.write("")
                if st.button("❌", key=f"rf_del_{row_id}_{cnt}", help="Hapus Baris Ini"):
                    if len(st.session_state.rf_rows_list) > 1:
                        st.session_state.rf_rows_list.remove(row_id)
                        st.rerun()

            default_price = 0.0
            if act_val != "Select" and selected_cat_id is not None:
                match_act = actions_df[(actions_df['category_id'] == selected_cat_id) & (actions_df['name'] == act_val)]
                if not match_act.empty:
                    default_price = float(match_act['price'].values[0])

            price_state_key = f"rf_price_{row_id}_{cnt}"
            prev_act_key = f"rf_prev_act_{row_id}_{cnt}"

            if prev_act_key not in st.session_state or st.session_state[prev_act_key] != act_val:
                st.session_state[prev_act_key] = act_val
                st.session_state[price_state_key] = default_price

            f_btm1, f_btm2, f_btm3, f_btm4 = st.columns([1.5, 1, 1.5, 1.5])

            with f_btm1:
                price_val = st.number_input("Tarif Satuan (Rp) *", min_value=0.0, value=float(st.session_state.get(price_state_key, default_price)), step=10000.0, format="%.0f", key=price_state_key)
            with f_btm2:
                qty_i = st.number_input("Jumlah (Qty)", min_value=1, value=1, step=1, key=f"rf_qty_{row_id}_{cnt}")
            with f_btm3:
                disc_i = st.number_input("Pengurangan (Rp)", min_value=0.0, value=0.0, step=5000.0, format="%.0f", key=f"rf_disc_{row_id}_{cnt}")

            subtot_i = (price_val * qty_i) - disc_i if act_val != "Select" else 0.0
            grand_total_actions += subtot_i

            with f_btm4:
                st.write("")
                st.markdown(f"""
                    <div style='margin-top:2px;'>
                        <div style='font-size:12px; color:#64748B; font-weight:600;'>Subtotal Refund:</div>
                        <div style='color:#EF4444; font-size:17px; font-weight:800;'>{format_rupiah(subtot_i)}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if act_val != "Select":
                items_data.append({
                    "book_no": bk_val,
                    "category_name": cat_val,
                    "action_name": act_val,
                    "price": price_val,
                    "qty": qty_i,
                    "discount": disc_i,
                    "subtotal": subtot_i
                })

        st.markdown(f"""
            <div style="text-align: right; margin: 15px 0; font-size: 16px; font-weight: 800; color: #0F172A;">
                Grand Total Pengembalian: <span style="font-size: 22px; font-weight: 800; color: #EF4444;">{format_rupiah(grand_total_actions)}</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin:12px 0; border:none; border-top:1.5px solid #CBD5E1;'>", unsafe_allow_html=True)
        st.markdown("##### 💰 Rincian Metode Pengembalian (Tunai / Transfer)")

        col_p_left, col_p_right = st.columns(2)
        with col_p_right:
            pay_transfer = st.number_input("Refund via Transfer Bank (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"rf_in_tf_{cnt}")
            
        with col_p_left:
            auto_tunai = max(0.0, grand_total_actions - pay_transfer)
            tunai_key = f"rf_in_tunai_{cnt}"
            if tunai_key not in st.session_state:
                st.session_state[tunai_key] = float(auto_tunai)
            else:
                st.session_state[tunai_key] = float(auto_tunai)
                
            pay_tunai = st.number_input("Refund via Tunai Fisik (Rp)", min_value=0.0, step=10000.0, format="%.0f", key=tunai_key)
            
        rf_notes = st.text_input("Catatan / Alasan Tambahan", placeholder="Contoh: Pengembalian sisa biaya rawat inap...", key=f"rf_notes_{cnt}")

        total_terbayar = pay_tunai + pay_transfer

        if abs(total_terbayar - grand_total_actions) > 0.01:
            st.warning(f"⚠️ Total pengembalian ({format_rupiah(total_terbayar)}) belum pas dengan tagihan refund ({format_rupiah(grand_total_actions)})")
        else:
            st.success(f"✓ Nominal pengembalian pas ({format_rupiah(total_terbayar)})")

        active_methods = []
        if pay_tunai > 0: active_methods.append(f"TUNAI ({format_rupiah(pay_tunai)})")
        if pay_transfer > 0: active_methods.append(f"TRANSFER ({format_rupiah(pay_transfer)})")
        summary_method_str = ", ".join(active_methods) if active_methods else "TUNAI"

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Simpan Pengembalian Kuitansi", use_container_width=True, type="primary", key=f"btn_save_rf_{cnt}"):
            if not no_urut_kertas.strip():
                st.error("No. Kertas / Referensi wajib diisi.")
            elif not items_data:
                st.error("Pilih minimal satu tindakan yang dikembalikan.")
            else:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS refund_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        receipt_no TEXT UNIQUE, receipt_date TEXT, input_date TEXT, shift TEXT, 
                        cashier_username TEXT, total_amount REAL, payment_method TEXT,
                        pay_tunai REAL, pay_transfer REAL, notes TEXT
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS refund_transaction_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        receipt_no TEXT, book_no TEXT, category_name TEXT, action_name TEXT,
                        price REAL, qty INTEGER, discount REAL, subtotal REAL
                    )
                """)
                
                try:
                    c.execute("""
                        INSERT INTO refund_transactions 
                        (receipt_no, receipt_date, input_date, shift, cashier_username, total_amount, payment_method, pay_tunai, pay_transfer, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (no_urut_kertas.strip(), str(tgl_kuitansi), str(datetime.today().date()), shift_val, st.session_state.user, 
                          grand_total_actions, summary_method_str, pay_tunai, pay_transfer, rf_notes))

                    for itm in items_data:
                        c.execute("""
                            INSERT INTO refund_transaction_items 
                            (receipt_no, book_no, category_name, action_name, price, qty, discount, subtotal)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (no_urut_kertas.strip(), itm['book_no'], itm['category_name'], itm['action_name'], itm['price'], itm['qty'], itm['discount'], itm['subtotal']))
                    
                    conn.commit()
                    st.success(f"✓ Pengembalian kuitansi #{no_urut_kertas} berhasil disimpan!")
                    st.session_state.rf_rows_list = [1]
                    st.session_state.rf_form_reset_cnt += 1
                    st.session_state.current_menu = "pengembalian"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Nomor Kertas/Referensi sudah digunakan. Silakan gunakan nomor unik.")

    # ==========================================
    # TAB 2: REFUND MANUAL
    # ==========================================
    with tab_manual:
        try:
            categories_df = pd.read_sql_query("SELECT id, name FROM categories ORDER BY name ASC", conn)
            cats_list_man = categories_df['name'].tolist() if not categories_df.empty else ["Umum"]
        except:
            cats_list_man = ["Umum"]

        st.markdown("##### 📄 Form Pengembalian Dana Mandiri")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            m_date = st.date_input("Tanggal Pengembalian", value=datetime.today())
        with col_d2:
            m_shift = st.selectbox("Shift *", ["Pagi", "Sore", "Malam"], key="man_shf")

        m_name = st.text_input("Nama Pasien / Penerima *", placeholder="Ketik nama...")
        m_rcpt = st.text_input("Nomor Kuitansi / Referensi", placeholder="Ketik nomor kuitansi jika ada...")
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            m_unit = st.selectbox("Unit Layanan", cats_list_man)
        with col_u2:
            m_action = st.text_input("Jenis Tindakan / Uraian", placeholder="Ketik uraian manual...")

        m_amt = st.number_input("Nominal Pengembalian (Rp)", min_value=0.0, step=10000.0, format="%.0f")
        m_method = st.selectbox("Metode Pengembalian", ["Tunai", "Transfer"])
        m_notes = st.text_area("Catatan / Alasan Refund")

        if st.button("Simpan Pengembalian Manual 💾", use_container_width=True, type="primary"):
            if not m_name.strip() or m_amt <= 0:
                st.error("⚠️ Nama penerima dan nominal wajib diisi!")
            else:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS manual_refunds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, refund_date TEXT, shift TEXT, recipient_name TEXT,
                        reference_no TEXT, unit_service TEXT, action_name TEXT, amount REAL,
                        method TEXT, notes TEXT, created_by TEXT
                    )
                """)
                c.execute("""
                    INSERT INTO manual_refunds (refund_date, shift, recipient_name, reference_no, unit_service, action_name, amount, method, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(m_date), m_shift, m_name.strip(), m_rcpt.strip(), m_unit, m_action.strip(), m_amt, m_method, m_notes.strip(), str(st.session_state.get('user', 'admin')).upper()))
                conn.commit()
                st.success("✓ Data pengembalian manual berhasil disimpan!")
                st.session_state.current_menu = "pengembalian"
                st.rerun()
                
    conn.close()