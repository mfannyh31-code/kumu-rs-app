import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header
from sqlalchemy import text

def format_angka(val):
    if val is None or pd.isna(val): return "0"
    try: return f"{int(float(val)):,}".replace(",", ".")
    except: return "0"

# =========================================================
# MODAL DETAIL KUITANSI REFUND
# =========================================================
@st.dialog("📋 Detail Kuitansi Pengembalian", width="large")
def show_refund_kuitansi_detail_dialog(receipt_no):
    with get_db() as conn:
        res_tx = conn.execute(text("SELECT * FROM refund_transactions WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
        row = res_tx.fetchone()
        col_names = list(res_tx.keys()) if row else []
        
        if row:
            tx = dict(zip(col_names, row))
            
            st.markdown(f"<div style='font-size:20px; font-weight:800; color:#EF4444; margin-bottom:14px;'>No. Refund #{tx.get('receipt_no', '')}</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"""
                    <div style='font-size:12px; color:#64748B;'>Tanggal Refund:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A; margin-bottom:8px;'>{tx.get('receipt_date', '')}</div>
                    <div style='font-size:12px; color:#64748B;'>Shift:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A;'>{tx.get('shift', '')}</div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style='font-size:12px; color:#64748B;'>Input Oleh:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A;'>{str(tx.get('cashier_username', '')).upper()}</div>
                    <div style='font-size:12px; color:#64748B; margin-top:8px;'>Catatan Tambahan:</div>
                    <div style='font-size:14px; font-weight:500; color:#475569;'>{tx.get('notes', '-') or '-'}</div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            
            th1, th2, th3, th4, th5 = st.columns([2.6, 1.2, 1.2, 0.8, 1.4])
            th1.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Tindakan Direfund</div>", unsafe_allow_html=True)
            th2.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>No. Bukti</div>", unsafe_allow_html=True)
            th3.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Tarif</div>", unsafe_allow_html=True)
            th4.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Jumlah</div>", unsafe_allow_html=True)
            th5.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px; text-align:right;'>Subtotal</div>", unsafe_allow_html=True)
            
            items = conn.execute(
                text("SELECT action_name, book_no, price, qty, subtotal FROM refund_transaction_items WHERE receipt_no = :rno"), 
                {"rno": str(receipt_no)}
            ).fetchall()
            
            for itm in items:
                tr1, tr2, tr3, tr4, tr5 = st.columns([2.6, 1.2, 1.2, 0.8, 1.4])
                tr1.markdown(f"<div style='font-size:13.5px; color:#0F172A; padding:4px 0;'><span style='color:#EF4444;'>⭕</span> {itm[0]}</div>", unsafe_allow_html=True)
                tr2.markdown(f"<div style='font-size:13.5px; color:#0F172A; padding:4px 0;'>{itm[1] or '-'}</div>", unsafe_allow_html=True)
                tr3.markdown(f"<div style='font-size:13.5px; color:#0F172A; padding:4px 0;'>{format_angka(itm[2])}</div>", unsafe_allow_html=True)
                tr4.markdown(f"<div style='font-size:13.5px; color:#0F172A; padding:4px 0;'>{itm[3]}</div>", unsafe_allow_html=True)
                tr5.markdown(f"<div style='font-size:13.5px; font-weight:800; color:#0F172A; text-align:right; padding:4px 0;'>{format_angka(itm[4])}</div>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin:16px 0; border:none; border-top:1px solid #F1F5F9;'>", unsafe_allow_html=True)
            
            s_col1, s_col2 = st.columns([1.5, 1])
            with s_col2:
                st.markdown(f"""
                    <div style="font-size:13px; color:#64748B; text-align:right;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <span>Total Dikembalikan</span><strong style="color:#EF4444; font-size:14px;">{format_angka(tx.get('total_amount'))}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Metode Tunai</span><span style="color:#0F172A; font-weight:600;">{format_angka(tx.get('pay_tunai'))}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Metode Transfer</span><span style="color:#0F172A; font-weight:600;">{format_angka(tx.get('pay_transfer'))}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Close", key="btn_close_rf_dialog", use_container_width=True):
                st.rerun()

# =========================================================
# MODAL EDIT REFUND
# =========================================================
@st.dialog("✏️ Edit Kuitansi Pengembalian", width="large")
def show_edit_refund_kuitansi_dialog(receipt_no):
    with get_db() as conn:
        res_tx = conn.execute(text("SELECT * FROM refund_transactions WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
        row = res_tx.fetchone()
        col_names = list(res_tx.keys()) if row else []
        
        if not row:
            return
            
        tx = dict(zip(col_names, row))
        
        st.markdown(f"<h4 style='color:#0F172A;'>Edit Pengembalian #{receipt_no}</h4>", unsafe_allow_html=True)
        
        # Ambil data master hirarki untuk pilihan edit tindakan
        service_cats_df = pd.read_sql_query(text("SELECT id, name FROM service_categories ORDER BY name ASC"), conn)
        scats_list = ["Select"] + service_cats_df['name'].tolist() if not service_cats_df.empty else ["Select"]
        categories_df = pd.read_sql_query(text("SELECT id, service_category_id, name FROM categories ORDER BY name ASC"), conn)
        actions_df = pd.read_sql_query(text("SELECT id, category_id, name, price FROM actions ORDER BY name ASC"), conn)

        edit_rf_rows_key = f"edit_rf_rows_{receipt_no}"
        if edit_rf_rows_key not in st.session_state:
            saved_db_items = conn.execute(
                text("SELECT action_name, category_name, book_no, price, qty, subtotal FROM refund_transaction_items WHERE receipt_no = :rno"), 
                {"rno": str(receipt_no)}
            ).fetchall()
            st.session_state[edit_rf_rows_key] = []
            for idx, itm in enumerate(saved_db_items):
                cat_row = categories_df[categories_df['name'] == itm[1]]
                scat_name = "Select"
                if not cat_row.empty:
                    s_id = cat_row['service_category_id'].values[0]
                    s_row = service_cats_df[service_cats_df['id'] == s_id]
                    if not s_row.empty:
                        scat_name = s_row['name'].values[0]

                st.session_state[edit_rf_rows_key].append({
                    "id": idx + 1,
                    "book_no": itm[2] or "",
                    "scat_name": scat_name if scat_name in scats_list else "Select",
                    "category_name": itm[1] if not categories_df[categories_df['name'] == itm[1]].empty else "Select",
                    "action_name": itm[0],
                    "price": float(itm[3] or 0),
                    "qty": int(itm[4] or 1),
                    "subtotal": float(itm[5] or 0)
                })
            if not st.session_state[edit_rf_rows_key]:
                st.session_state[edit_rf_rows_key].append({"id": 1, "book_no": "", "scat_name": "Select", "category_name": "Select", "action_name": "Select", "price": 0.0, "qty": 1, "subtotal": 0.0})

        try:
            curr_date = datetime.strptime(str(tx.get('receipt_date', '')), '%Y-%m-%d').date()
        except:
            curr_date = datetime.today().date()
            
        c1, c2 = st.columns(2)
        with c1:
            new_date = st.date_input("Tanggal Pengembalian", value=curr_date, key=f"rfe_dt_{receipt_no}")
        with c2:
            shf_opts = ["Pagi", "Sore", "Malam"]
            curr_shf = tx.get('shift', 'Pagi')
            new_shf = st.selectbox("Shift", shf_opts, index=shf_opts.index(curr_shf) if curr_shf in shf_opts else 0, key=f"rfe_shf_{receipt_no}")
        
        new_note = st.text_input("Catatan Tambahan", value=tx.get('notes', ''), key=f"rfe_not_{receipt_no}")
        
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        st.markdown("##### 💉 Rincian Tindakan & Layanan yang Direfund")

        if st.button("➕ Tambah Baris Tindakan", key=f"btn_add_ed_rf_row_{receipt_no}"):
            new_id = max([r['id'] for r in st.session_state[edit_rf_rows_key]], default=0) + 1
            st.session_state[edit_rf_rows_key].append({"id": new_id, "book_no": "", "scat_name": "Select", "category_name": "Select", "action_name": "Select", "price": 0.0, "qty": 1, "subtotal": 0.0})
            st.rerun()

        grand_total_actions = 0.0
        updated_rf_items_data = []

        for row_item in list(st.session_state[edit_rf_rows_key]):
            r_id = row_item['id']
            st.markdown("<div style='background:#F8FAFC; border:1.5px solid #CBD5E1; padding:12px; border-radius:8px; margin-bottom:10px;'>", unsafe_allow_html=True)
            
            rt1, rt2, rt3, rt4, rt5 = st.columns([1.1, 1.8, 1.8, 2.3, 0.4])
            with rt1:
                b_val = st.text_input("No. Bukti", value=row_item['book_no'], key=f"rfe_bk_{receipt_no}_{r_id}")
            with rt2:
                curr_scat = row_item.get('scat_name', 'Select')
                scat_idx = scats_list.index(curr_scat) if curr_scat in scats_list else 0
                selected_scat = st.selectbox("Kategori Layanan", scats_list, index=scat_idx, key=f"rfe_scat_{receipt_no}_{r_id}")

            sub_units = ["Select"]
            selected_scat_id = None
            if selected_scat != "Select" and not service_cats_df.empty:
                m_scat = service_cats_df[service_cats_df['name'] == selected_scat]
                if not m_scat.empty:
                    selected_scat_id = m_scat['id'].values[0]
                    sub_units += categories_df[categories_df['service_category_id'] == selected_scat_id]['name'].tolist()

            with rt3:
                curr_cat = row_item['category_name']
                cat_idx = sub_units.index(curr_cat) if curr_cat in sub_units else 0
                selected_cat = st.selectbox("Unit Layanan", sub_units, index=cat_idx, key=f"rfe_cat_{receipt_no}_{r_id}")

            sub_acts = ["Select"]
            selected_cat_id = None
            if selected_cat != "Select" and not categories_df.empty:
                m_cat = categories_df[categories_df['name'] == selected_cat]
                if not m_cat.empty:
                    selected_cat_id = m_cat['id'].values[0]
                    sub_acts += actions_df[actions_df['category_id'] == selected_cat_id]['name'].tolist()

            with rt4:
                curr_act = row_item['action_name']
                act_idx = sub_acts.index(curr_act) if curr_act in sub_acts else 0
                selected_act = st.selectbox("Jenis Tindakan", sub_acts, index=act_idx, key=f"rfe_act_{receipt_no}_{r_id}")

            with rt5:
                st.write("")
                st.write("")
                if st.button("❌", key=f"rfe_del_{receipt_no}_{r_id}"):
                    if len(st.session_state[edit_rf_rows_key]) > 1:
                        st.session_state[edit_rf_rows_key] = [r for r in st.session_state[edit_rf_rows_key] if r['id'] != r_id]
                        st.rerun()

            def_prc = row_item['price']
            if selected_act != "Select" and (selected_act != curr_act or def_prc == 0.0):
                match_a = actions_df[(actions_df['category_id'] == selected_cat_id) & (actions_df['name'] == selected_act)]
                if not match_a.empty:
                    def_prc = float(match_a['price'].values[0])

            rb1, rb2, rb3 = st.columns([2, 1, 1.5])
            with rb1:
                prc_val = st.number_input("Tarif Satuan (Rp)", min_value=0.0, value=float(def_prc), step=10000.0, format="%.0f", key=f"rfe_prc_{receipt_no}_{r_id}")
            with rb2:
                qty_val = st.number_input("Qty", min_value=1, value=int(row_item['qty']), step=1, key=f"rfe_qty_{receipt_no}_{r_id}")
            with rb3:
                sub_val = prc_val * qty_val if selected_act != "Select" else 0.0
                grand_total_actions += sub_val
                st.write("")
                st.markdown(f"<div style='font-size:13px; color:#64748B;'>Subtotal:</div><strong style='color:#EF4444;'>{format_angka(sub_val)}</strong>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if selected_act != "Select":
                updated_rf_items_data.append({
                    "book_no": b_val,
                    "category_name": selected_cat,
                    "action_name": selected_act,
                    "price": prc_val,
                    "qty": qty_val,
                    "subtotal": sub_val
                })

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        st.markdown("##### Nominal Pengembalian")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            new_tunai = st.number_input("Tunai (Rp)", min_value=0.0, value=float(tx.get('pay_tunai') or 0), step=10000.0, key=f"rfe_tn_{receipt_no}")
        with col_t2:
            new_trans = st.number_input("Transfer (Rp)", min_value=0.0, value=float(tx.get('pay_transfer') or 0), step=10000.0, key=f"rfe_tr_{receipt_no}")
            
        new_total = new_tunai + new_trans
        st.markdown(f"**Total Keseluruhan:** <span style='color:#EF4444;'>{format_rupiah(new_total)}</span>", unsafe_allow_html=True)
        
        active_methods = []
        if new_tunai > 0: active_methods.append(f"TUNAI ({format_rupiah(new_tunai)})")
        if new_trans > 0: active_methods.append(f"TRANSFER ({format_rupiah(new_trans)})")
        new_method = ", ".join(active_methods) if active_methods else "TUNAI"

        if st.button("Simpan Perubahan Data Utama 💾", type="primary", use_container_width=True):
            if not updated_rf_items_data:
                st.error("Pilih minimal satu tindakan.")
            else:
                with conn.begin():
                    conn.execute(text("""
                        UPDATE refund_transactions 
                        SET receipt_date = :rdate, shift = :shf, total_amount = :totamt, pay_tunai = :ptun, pay_transfer = :ptf, payment_method = :pmeth, notes = :notes
                        WHERE receipt_no = :rno
                    """), {
                        "rdate": str(new_date),
                        "shf": new_shf,
                        "totamt": grand_total_actions,
                        "ptun": new_tunai,
                        "ptf": new_trans,
                        "pmeth": new_method,
                        "notes": new_note,
                        "rno": receipt_no
                    })
                    
                    conn.execute(text("DELETE FROM refund_transaction_items WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
                    for itm in updated_rf_items_data:
                        conn.execute(text("""
                            INSERT INTO refund_transaction_items (receipt_no, book_no, category_name, action_name, price, qty, discount, subtotal)
                            VALUES (:rno, :bk, :cname, :aname, :prc, :qty, 0.0, :sub)
                        """), {
                            "rno": str(receipt_no),
                            "bk": itm['book_no'],
                            "cname": itm['category_name'],
                            "aname": itm['action_name'],
                            "prc": itm['price'],
                            "qty": itm['qty'],
                            "sub": itm['subtotal']
                        })

                if edit_rf_rows_key in st.session_state:
                    del st.session_state[edit_rf_rows_key]
                st.success("Data pengembalian berhasil diupdate!")
                st.rerun()

# =========================================================
# MODAL HAPUS REFUND
# =========================================================
@st.dialog("🗑️ Konfirmasi Hapus Refund")
def confirm_delete_refund_kuitansi_dialog(receipt_no):
    st.warning(f"Yakin ingin menghapus dokumen pengembalian **#{receipt_no}** beserta seluruh rincian tindakannya?")
    c1, c2 = st.columns(2)
    if c1.button("Batal", use_container_width=True): st.rerun()
    if c2.button("Ya, Hapus", use_container_width=True, type="primary"):
        with get_db() as conn:
            with conn.begin():
                conn.execute(text("DELETE FROM refund_transactions WHERE receipt_no = :rno"), {"rno": receipt_no})
                conn.execute(text("DELETE FROM refund_transaction_items WHERE receipt_no = :rno"), {"rno": receipt_no})
        st.success("Data pengembalian berhasil dihapus!")
        st.rerun()

# =========================================================
# HALAMAN UTAMA DAFTAR PENGEMBALIAN
# =========================================================
def render_page():
    st.markdown("""
        <style>
        .table-row-card {
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            margin-bottom: 8px !important;
        }
        .action-stack { display: flex; flex-direction: column; gap: 4px !important; width: 100%; }
        div[data-testid="column"] div.stButton > button {
            width: 100% !important; border: none !important; color: #FFFFFF !important;
            font-weight: 700 !important; font-size: 11px !important; height: 24px !important;
            min-height: 24px !important; border-radius: 4px !important; padding: 0 !important;
        }
        .btn-dtl button { background-color: #3B82F6 !important; }
        .btn-ed button { background-color: #F59E0B !important; }
        .btn-del button { background-color: #EF4444 !important; }
        </style>
    """, unsafe_allow_html=True)

    render_header("💸 Daftar Laporan Pengembalian", "Kelola dan pantau pengembalian dana transaksi kuitansi maupun manual secara rapi.")

    c_top1, c_top2 = st.columns([3, 1])
    with c_top2:
        if st.button("➕ Input Pengembalian Baru", use_container_width=True, type="primary"):
            st.session_state.current_menu = "input_pengembalian"
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    
    st.markdown('<div style="background:#FFFFFF; padding:20px; border-radius:10px; border:1px solid #CBD5E1; margin-bottom:20px;">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
    with c1:
        tipe_filter = st.selectbox("Jenis Periode", ["Harian", "Bulanan", "Tahunan"], key="ref_list_tipe_f")
    
    months_dict = {
        "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12",
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04", "Mei": "05", "Juni": "06", "Juli": "07"
    }
    years_list = [str(y) for y in range(2024, 2032)]
    current_year_str = str(datetime.today().year)

    if tipe_filter == "Harian":
        with c2:
            sel_date = st.date_input("Pilih Tanggal Refund", datetime.today(), key="ref_list_date_f")
        date_mask = f"{str(sel_date)}%"
    elif tipe_filter == "Bulanan":
        with c2:
            sel_m_name = st.selectbox("Pilih Bulan", list(months_dict.keys()), key="ref_list_m_f")
        with c3:
            sel_y_m = st.selectbox("Pilih Tahun (Bulan)", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="ref_list_my_f")
        date_mask = f"{sel_y_m}-{months_dict[sel_m_name]}%"
    else:
        with c2:
            sel_y = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="ref_list_y_f")
        date_mask = f"{sel_y}%"
    st.markdown('</div>', unsafe_allow_html=True)

    f_srch, f_shift = st.columns([2, 1])
    with f_srch:
        keyword = st.text_input("🔍 Cari No. Kertas / Nama / Referensi", placeholder="Ketik kata kunci...")
    with f_shift:
        filter_shift = st.selectbox("Filter Shift", ["Semua Shift", "Pagi", "Sore", "Malam"])

    tab1, tab2 = st.tabs(["📄 Laporan Pengembalian Kuitansi", "📑 Pengembalian Manual"])
    
    with tab1:
        with get_db() as conn:
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS refund_transactions (
                        id SERIAL PRIMARY KEY,
                        receipt_no TEXT UNIQUE, receipt_date TEXT, input_date TEXT, shift TEXT, 
                        cashier_username TEXT, total_amount REAL, payment_method TEXT,
                        pay_tunai REAL, pay_transfer REAL, notes TEXT
                    )
                """))
                conn.commit()

                query_rf = "SELECT * FROM refund_transactions WHERE receipt_date LIKE :dmask"
                params_rf = {"dmask": date_mask}
                if filter_shift != "Semua Shift":
                    query_rf += " AND shift = :shf"
                    params_rf["shf"] = filter_shift
                if keyword.strip():
                    query_rf += " AND (receipt_no LIKE :kw OR cashier_username LIKE :kw)"
                    params_rf["kw"] = f"%{keyword.strip()}%"
                df_rf = pd.read_sql_query(text(query_rf), conn, params=params_rf)
            except:
                df_rf = pd.DataFrame()

        if not df_rf.empty:
            h1, h2, h3, h4, h5 = st.columns([1.2, 1.2, 1.2, 1.5, 1.0])
            h1.markdown("**Waktu Refund**")
            h2.markdown("**No. Referensi**")
            h3.markdown("**Metode & Kasir**")
            h4.markdown("**Nominal Refund**")
            h5.markdown("<div style='text-align:center;'>**Aksi**</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 10px 0; border:none; border-top:2px solid #334155;'>", unsafe_allow_html=True)

            for idx, row in df_rf.iterrows():
                rcpt = row['receipt_no']
                amt = float(row['total_amount'] or 0)
                
                st.markdown('<div class="table-row-card">', unsafe_allow_html=True)
                r1, r2, r3, r4, r5 = st.columns([1.2, 1.2, 1.2, 1.5, 1.0])
                
                r1.markdown(f"{row['receipt_date']}<br><span style='font-size:12px; color:#475569;'>Shift: {row['shift']}</span>", unsafe_allow_html=True)
                r2.markdown(f"**#{rcpt}**", unsafe_allow_html=True)
                r3.markdown(f"<span style='font-size:11px;'>{row['payment_method']}</span><br><span style='font-size:12px; color:#475569;'>User: <b>{str(row['cashier_username']).upper()}</b></span>", unsafe_allow_html=True)
                r4.markdown(f"<strong style='color:#EF4444; font-size:15px;'>{format_rupiah(amt)}</strong>", unsafe_allow_html=True)
                
                with r5:
                    st.markdown('<div class="action-stack">', unsafe_allow_html=True)
                    
                    st.markdown('<div class="btn-dtl">', unsafe_allow_html=True)
                    if st.button("Detail", key=f"tx_dtl_{rcpt}", use_container_width=True): 
                        show_refund_kuitansi_detail_dialog(rcpt)
                        
                    st.markdown('</div><div class="btn-ed">', unsafe_allow_html=True)
                    if st.button("Edit", key=f"tx_ed_{rcpt}", use_container_width=True):
                        show_edit_refund_kuitansi_dialog(rcpt)
                            
                    st.markdown('</div><div class="btn-del">', unsafe_allow_html=True)
                    if st.button("Hapus", key=f"tx_del_{rcpt}", use_container_width=True):
                        confirm_delete_refund_kuitansi_dialog(rcpt)
                        
                    st.markdown('</div></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Tidak ada laporan pengembalian kuitansi pada periode tersebut.")

    with tab2:
        with get_db() as conn:
            try:
                query_man = "SELECT * FROM manual_refunds WHERE refund_date LIKE :dmask"
                params_man = {"dmask": date_mask}
                if filter_shift != "Semua Shift":
                    query_man += " AND shift = :shf"
                    params_man["shf"] = filter_shift
                df_manual = pd.read_sql_query(text(query_man), conn, params=params_man)
            except:
                df_manual = pd.DataFrame()

        if not df_manual.empty:
            for _, mrow in df_manual.iterrows():
                mid = mrow['id']
                st.write(f"- **{mrow['recipient_name']}** ({format_rupiah(mrow['amount'])})")
        else:
            st.info("Tidak ada pengembalian manual ditemukan pada periode tersebut.")

    st.markdown('</div>', unsafe_allow_html=True)