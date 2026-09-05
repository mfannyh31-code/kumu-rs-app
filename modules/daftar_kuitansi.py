import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah
from sqlalchemy import text

def format_angka(val):
    if val is None or pd.isna(val):
        return "0"
    try:
        return f"{int(float(val)):,}".replace(",", ".")
    except Exception:
        return "0"

# =========================================================
# MODAL KONFIRMASI HAPUS TRANSAKSI
# =========================================================
@st.dialog("Konfirmasi Hapus Data")
def confirm_delete_dialog(receipt_no):
    st.markdown(f"""
        <div style="text-align:center; padding: 10px 0;">
            <div style="font-size: 36px; margin-bottom: 6px;">⚠️</div>
            <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">
                Yakin ingin menghapus kuitansi #{receipt_no}?
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin:10px 0; border:none; border-top:1px solid #94A3B8;'>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_{receipt_no}"):
            st.rerun()
    with c2:
        if st.button("🗑️ Ya, Hapus", use_container_width=True, key=f"confirm_del_{receipt_no}"):
            with get_db() as conn:
                with conn.begin():
                    conn.execute(text("DELETE FROM transaction_items WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
                    conn.execute(text("DELETE FROM transactions WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
            st.success(f"Kuitansi #{receipt_no} dihapus!")
            st.rerun()

# =========================================================
# MODAL DETAIL TRANSAKSI
# =========================================================
@st.dialog("Transaksi", width="large")
def show_transaction_detail(receipt_no):
    with get_db() as conn:
        res_tx = conn.execute(text("SELECT * FROM transactions WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
        row = res_tx.fetchone()
        col_names = list(res_tx.keys()) if row else []
        
        if row:
            tx = dict(zip(col_names, row))
            
            st.markdown(f"<div style='font-size:20px; font-weight:800; color:#0F172A; margin-bottom:14px;'>No. Kertas #{tx.get('receipt_no', '')}</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"""
                    <div style='font-size:12px; color:#64748B;'>Tanggal Kuitansi:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A; margin-bottom:8px;'>{tx.get('receipt_date', '')}</div>
                    <div style='font-size:12px; color:#64748B;'>Shift:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A;'>{tx.get('shift', '')}</div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div style='font-size:12px; color:#64748B;'>Input:</div>
                    <div style='font-size:14px; font-weight:700; color:#0F172A;'>{str(tx.get('cashier_username', '')).upper()}</div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            
            th1, th2, th3, th4, th5 = st.columns([2.6, 1.2, 1.2, 0.8, 1.4])
            th1.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Tindakan</div>", unsafe_allow_html=True)
            th2.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>No. Bukti</div>", unsafe_allow_html=True)
            th3.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Tarif</div>", unsafe_allow_html=True)
            th4.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px;'>Jumlah</div>", unsafe_allow_html=True)
            th5.markdown("<div style='font-size:13px; font-weight:700; color:#64748B; border-bottom:1.5px solid #F1F5F9; padding-bottom:6px; text-align:right;'>Total</div>", unsafe_allow_html=True)
            
            items = conn.execute(
                text("SELECT action_name, book_no, price, qty, subtotal FROM transaction_items WHERE receipt_no = :rno"), 
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
            
            tot_act = float(tx.get('total_actions_amount') or 0)
            tunai_v = float(tx.get('pay_tunai') or 0)
            qris_v = float(tx.get('pay_qris') or 0)
            edc_v = float(tx.get('pay_edc') or 0)
            tf_v = float(tx.get('pay_transfer') or 0)
            va_v = float(tx.get('pay_va') or 0)
            pengakuan_v = float(tx.get('pay_pengakuan_bendahara') or 0)
            
            s_col1, s_col2 = st.columns([1.5, 1])
            with s_col2:
                st.markdown(f"""
                    <div style="font-size:13px; color:#64748B; text-align:right;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <span>Grand Total</span><strong style="color:#0F172A; font-size:14px;">{format_angka(tot_act)}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Tunai</span><span style="color:#0F172A; font-weight:600;">{format_angka(tunai_v)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Pengakuan Bendahara</span><span style="color:#0F172A; font-weight:600;">{format_angka(pengakuan_v)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Qris</span><span style="color:#0F172A; font-weight:600;">{format_angka(qris_v)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>EDC</span><span style="color:#0F172A; font-weight:600;">{format_angka(edc_v)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Transfer</span><span style="color:#0F172A; font-weight:600;">{format_angka(tf_v)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Virtual Account</span><span style="color:#0F172A; font-weight:600;">{format_angka(va_v)}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            c_btn1, c_btn2 = st.columns([3, 1])
            with c_btn2:
                if st.button("Close", key="btn_close_dialog", use_container_width=True):
                    st.rerun()

# =========================================================
# MODAL EDIT TRANSAKSI
# =========================================================
@st.dialog("Edit Kuitansi Transaksi", width="large")
def show_edit_dialog(receipt_no):
    with get_db() as conn:
        res_tx = conn.execute(text("SELECT * FROM transactions WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
        row = res_tx.fetchone()
        col_names = list(res_tx.keys()) if row else []
        
        if not row:
            conn.close()
            return
            
        tx = dict(zip(col_names, row))
        
        st.markdown(f"<h4 style='color:#0F172A;'>Edit Kuitansi #{receipt_no}</h4>", unsafe_allow_html=True)
        
        service_cats_df = pd.read_sql_query(text("SELECT id, name FROM service_categories ORDER BY name ASC"), conn)
        scats_list = ["Select"] + service_cats_df['name'].tolist() if not service_cats_df.empty else ["Select"]

        categories_df = pd.read_sql_query(text("SELECT id, service_category_id, name FROM categories ORDER BY name ASC"), conn)
        actions_df = pd.read_sql_query(text("SELECT id, category_id, name, price FROM actions ORDER BY name ASC"), conn)

        edit_rows_key = f"edit_rows_{receipt_no}"
        if edit_rows_key not in st.session_state:
            saved_db_items = conn.execute(
                text("SELECT action_name, category_name, book_no, price, qty, subtotal FROM transaction_items WHERE receipt_no = :rno"), 
                {"rno": str(receipt_no)}
            ).fetchall()
            st.session_state[edit_rows_key] = []
            for idx, itm in enumerate(saved_db_items):
                cat_row = categories_df[categories_df['name'] == itm[1]]
                scat_name = "Select"
                if not cat_row.empty:
                    s_id = cat_row['service_category_id'].values[0]
                    s_row = service_cats_df[service_cats_df['id'] == s_id]
                    if not s_row.empty:
                        scat_name = s_row['name'].values[0]

                st.session_state[edit_rows_key].append({
                    "id": idx + 1,
                    "book_no": itm[2] or "",
                    "scat_name": scat_name if scat_name in scats_list else "Select",
                    "category_name": itm[1] if not categories_df[categories_df['name'] == itm[1]].empty else "Select",
                    "action_name": itm[0],
                    "price": float(itm[3] or 0),
                    "qty": int(itm[4] or 1),
                    "subtotal": float(itm[5] or 0)
                })
            if not st.session_state[edit_rows_key]:
                st.session_state[edit_rows_key].append({"id": 1, "book_no": "", "scat_name": "Select", "category_name": "Select", "action_name": "Select", "price": 0.0, "qty": 1, "subtotal": 0.0})

        st.markdown("##### 📄 Informasi Dokumen Kuitansi")
        h1, h2, h3 = st.columns([1.5, 1.5, 1.5])
        with h1:
            st.text_input("No. Kertas / Kuitansi", value=str(tx.get('receipt_no', '')), disabled=True, key=f"ed_rcpt_{receipt_no}")
        with h2:
            try:
                curr_date = datetime.strptime(str(tx.get('receipt_date', '')), '%Y-%m-%d').date()
            except Exception:
                curr_date = datetime.today().date()
            tgl_kuitansi = st.date_input("Tanggal Kuitansi *", value=curr_date, key=f"ed_date_{receipt_no}")
        with h3:
            shift_list = ["Pagi", "Sore", "Malam"]
            curr_shf = tx.get('shift', 'Pagi')
            shf_idx = shift_list.index(curr_shf) if curr_shf in shift_list else 0
            shift_val = st.selectbox("Shift *", shift_list, index=shf_idx, key=f"ed_shift_{receipt_no}")

        st.markdown("<hr style='margin:12px 0; border:none; border-top:1.5px solid #CBD5E1;'>", unsafe_allow_html=True)

        st.markdown("##### 💉 Rincian Tindakan & Layanan")
        if st.button("➕ Tambah Baris Tindakan", key=f"btn_add_ed_row_{receipt_no}"):
            new_id = max([r['id'] for r in st.session_state[edit_rows_key]], default=0) + 1
            st.session_state[edit_rows_key].append({"id": new_id, "book_no": "", "scat_name": "Select", "category_name": "Select", "action_name": "Select", "price": 0.0, "qty": 1, "subtotal": 0.0})
            st.rerun()

        grand_total_actions = 0.0
        updated_items_data = []

        for row_item in list(st.session_state[edit_rows_key]):
            r_id = row_item['id']
            st.markdown("<div style='background:#F8FAFC; border:1.5px solid #CBD5E1; padding:12px; border-radius:8px; margin-bottom:10px;'>", unsafe_allow_html=True)
            
            rt1, rt2, rt3, rt4, rt5 = st.columns([1.1, 1.8, 1.8, 2.3, 0.4])
            with rt1:
                b_val = st.text_input("No. Bukti", value=row_item['book_no'], key=f"ed_bk_{receipt_no}_{r_id}")
            with rt2:
                curr_scat = row_item.get('scat_name', 'Select')
                scat_idx = scats_list.index(curr_scat) if curr_scat in scats_list else 0
                selected_scat = st.selectbox("Kategori Layanan", scats_list, index=scat_idx, key=f"ed_scat_{receipt_no}_{r_id}")

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
                selected_cat = st.selectbox("Unit Layanan", sub_units, index=cat_idx, key=f"ed_cat_{receipt_no}_{r_id}")

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
                selected_act = st.selectbox("Jenis Tindakan", sub_acts, index=act_idx, key=f"ed_act_{receipt_no}_{r_id}")

            with rt5:
                st.write("")
                st.write("")
                if st.button("❌", key=f"ed_del_{receipt_no}_{r_id}"):
                    if len(st.session_state[edit_rows_key]) > 1:
                        st.session_state[edit_rows_key] = [r for r in st.session_state[edit_rows_key] if r['id'] != r_id]
                        st.rerun()

            def_prc = row_item['price']
            if selected_act != "Select" and (selected_act != curr_act or def_prc == 0.0):
                match_a = actions_df[(actions_df['category_id'] == selected_cat_id) & (actions_df['name'] == selected_act)]
                if not match_a.empty:
                    def_prc = float(match_a['price'].values[0])

            rb1, rb2, rb3 = st.columns([2, 1, 1.5])
            with rb1:
                prc_val = st.number_input("Tarif Satuan (Rp)", min_value=0.0, value=float(def_prc), step=10000.0, format="%.0f", key=f"ed_prc_{receipt_no}_{r_id}")
            with rb2:
                qty_val = st.number_input("Qty", min_value=1, value=int(row_item['qty']), step=1, key=f"ed_qty_{receipt_no}_{r_id}")
            with rb3:
                sub_val = prc_val * qty_val if selected_act != "Select" else 0.0
                grand_total_actions += sub_val
                st.write("")
                st.markdown(f"<div style='font-size:13px; color:#64748B;'>Subtotal:</div><strong style='color:#028090;'>{format_angka(sub_val)}</strong>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if selected_act != "Select":
                updated_items_data.append({
                    "book_no": b_val,
                    "scat_name": selected_scat,
                    "category_name": selected_cat,
                    "action_name": selected_act,
                    "price": prc_val,
                    "qty": qty_val,
                    "subtotal": sub_val
                })

        st.markdown(f"""
            <div style="text-align: right; margin: 10px 0; font-size: 16px; font-weight: 800; color: #0F172A;">
                Grand Total Tindakan: <span style="font-size: 20px; color: #028090;">{format_rupiah(grand_total_actions)}</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin:12px 0; border:none; border-top:1.5px solid #CBD5E1;'>", unsafe_allow_html=True)
        st.markdown("##### 💰 Rincian Nominal Pembayaran Kasir", unsafe_allow_html=True)

        col_p_left, col_p_right = st.columns(2)
        with col_p_right:
            st.markdown("**Metode Non-Tunai / Digital:**")
            pay_transfer = st.number_input("Transfer Bank (Rp)", min_value=0.0, value=float(tx.get('pay_transfer', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_tf_{receipt_no}")
            pay_va = st.number_input("Virtual Account (Rp)", min_value=0.0, value=float(tx.get('pay_va', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_va_{receipt_no}")
            pay_qris = st.number_input("QRIS (Rp)", min_value=0.0, value=float(tx.get('pay_qris', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_qris_{receipt_no}")
            pay_edc = st.number_input("EDC Kartu (Rp)", min_value=0.0, value=float(tx.get('pay_edc', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_edc_{receipt_no}")

        non_tunai_total = pay_transfer + pay_va + pay_qris + pay_edc

        with col_p_left:
            st.markdown("**Metode Tunai & Penyesuaian:**")
            pay_deposit = st.number_input("Potong Uang Muka / Deposit (Rp)", min_value=0.0, value=float(tx.get('pay_deposit', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_dep_{receipt_no}")
            pay_pengakuan = st.number_input("Pengakuan Bendahara (Rp)", min_value=0.0, value=float(tx.get('pay_pengakuan_bendahara', 0) or 0.0), step=10000.0, format="%.0f", key=f"ed_pengakuan_{receipt_no}")
            
            default_tunai = max(0.0, grand_total_actions - non_tunai_total - pay_deposit - pay_pengakuan)
            pay_tunai = st.number_input("Uang Tunai Fisik (Rp)", min_value=0.0, value=float(tx.get('pay_tunai', 0) or default_tunai), step=10000.0, format="%.0f", key=f"ed_tunai_{receipt_no}")

        total_terbayar = pay_tunai + non_tunai_total + pay_deposit + pay_pengakuan

        if abs(total_terbayar - grand_total_actions) > 0.01:
            st.warning(f"⚠️ Total pembayaran ({format_rupiah(total_terbayar)}) belum pas dengan tagihan ({format_rupiah(grand_total_actions)})")
        else:
            st.success(f"✓ Split pembayaran seimbang dan pas ({format_rupiah(total_terbayar)})")

        active_methods = []
        if pay_tunai > 0: active_methods.append(f"TUNAI ({format_rupiah(pay_tunai)})")
        if pay_deposit > 0: active_methods.append(f"DEPOSIT ({format_rupiah(pay_deposit)})")
        if pay_transfer > 0: active_methods.append(f"TRANSFER ({format_rupiah(pay_transfer)})")
        if pay_edc > 0: active_methods.append(f"EDC ({format_rupiah(pay_edc)})")
        if pay_qris > 0: active_methods.append(f"QRIS ({format_rupiah(pay_qris)})")
        if pay_va > 0: active_methods.append(f"VA ({format_rupiah(pay_va)})")
        summary_method_str = ", ".join(active_methods) if active_methods else "TUNAI"

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Simpan Perubahan Kuitansi 💾", key=f"btn_save_edit_all_{receipt_no}", use_container_width=True):
            if not updated_items_data:
                st.error("Pilih minimal satu tindakan.")
            else:
                with conn.begin():
                    conn.execute(text("""
                        UPDATE transactions 
                        SET receipt_date = :rdate, shift = :shf, 
                            total_actions_amount = :totamt, final_amount = :finamt, payment_method = :pmeth,
                            pay_tunai = :ptun, pay_transfer = :ptf, pay_edc = :pedc, pay_qris = :pqris, pay_va = :pva, pay_deposit = :pdep,
                            pay_pengakuan_bendahara = :ppeng
                        WHERE receipt_no = :rno
                    """), {
                        "rdate": str(tgl_kuitansi),
                        "shf": shift_val,
                        "totamt": grand_total_actions,
                        "finamt": grand_total_actions,
                        "pmeth": summary_method_str,
                        "ptun": pay_tunai,
                        "ptf": pay_transfer,
                        "pedc": pay_edc,
                        "pqris": pay_qris,
                        "pva": pay_va,
                        "pdep": pay_deposit,
                        "ppeng": pay_pengakuan,
                        "rno": str(receipt_no)
                    })
                    
                    conn.execute(text("DELETE FROM transaction_items WHERE receipt_no = :rno"), {"rno": str(receipt_no)})
                    for itm in updated_items_data:
                        conn.execute(text("""
                            INSERT INTO transaction_items (receipt_no, book_no, category_name, action_name, price, qty, discount, subtotal)
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
                
                if edit_rows_key in st.session_state:
                    del st.session_state[edit_rows_key]
                st.success("Perubahan data kuitansi dan tindakan berhasil disimpan!")
                st.rerun()

# =========================================================
# HALAMAN UTAMA DAFTAR KUITANSI (CACHED STATE & FAST SORT)
# =========================================================
def render_page():
    if 'page_offset' not in st.session_state:
        st.session_state.page_offset = 0
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'id'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'DESC'

    current_logged_user = str(st.session_state.get('user', '')).upper()
    current_role = str(st.session_state.get('role', '')).strip()

    c_top1, c_top2 = st.columns([3, 1])
    with c_top1:
        st.markdown("""
            <div>
                <h2 style="color:#0F172A; margin:0; font-size:22px; font-weight:800;">Data Penerimaan</h2>
                <p style="color:#64748B; margin:2px 0 0 0; font-size:13.5px; font-weight:600;">Kasir — Monitoring Kuitansi Cepat</p>
            </div>
        """, unsafe_allow_html=True)
    with c_top2:
        st.write("")
        if st.button("➕ Tambah Data", use_container_width=True):
            st.session_state.current_menu = "input_kuitansi"
            st.rerun()

    st.markdown("""
        <style>
        .compact-box {
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .kwt-row-card {
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 6px !important;
            padding: 4px 10px !important;
            margin-bottom: 4px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            align-items: center !important;
        }
        .kwt-row-card:hover {
            background-color: #F8FAFC !important;
        }
        .kwt-row-card div[data-testid="column"] {
            display: flex;
            align-items: center;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
        
        .kwt-data-cell {
            font-size: 20px !important;
            color: #0F172A !important;
            font-weight: 500;
        }
        .kwt-data-cell-bold {
            font-size: 20px !important;
            color: #0F172A !important;
            font-weight: 800 !important;
        }
        .kwt-data-cell-price {
            font-size: 20px !important;
            color: #028090 !important;
            font-weight: 800 !important;
        }

        .action-stack {
            display: flex;
            flex-direction: column;
            gap: 0px !important;
            width: 100%;
        }
        .kwt-row-card div[data-testid="column"] div.stButton {
            margin-bottom: 0px !important;
        }
        .kwt-row-card div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            height: 22px !important;
            min-height: 22px !important;
            font-size: 11px !important;
            border-radius: 2px !important;
            padding: 0px !important;
            border: none !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        .btn-kwt-det button { background-color: #3B82F6 !important; }
        .btn-kwt-ed button { background-color: #F59E0B !important; }
        .btn-kwt-del button { background-color: #EF4444 !important; }

        .sort-header-row div[data-testid="column"] div.stButton > button {
            background-color: #028090 !important;
            border: none !important;
            color: #FFFFFF !important;
            font-size: 12.5px !important;
            font-weight: 800 !important;
            height: 38px !important;
            min-height: 38px !important;
            padding: 2px 4px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .sort-header-row div[data-testid="column"] div.stButton > button:hover {
            background-color: #026b78 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- KONTROL FILTER PERIODE (COMPACT) ---
    st.markdown('<div class="compact-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
    with c1:
        tipe_filter = st.selectbox("Jenis Periode", ["Harian", "Bulanan", "Tahunan"], key="kwt_tipe_f", label_visibility="collapsed")
    
    months_dict = {
        "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12",
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04", "Mei": "05", "Juni": "06", "Juli": "07"
    }
    years_list = [str(y) for y in range(2024, 2032)]
    current_year_str = str(datetime.today().year)

    if tipe_filter == "Harian":
        with c2:
            sel_date = st.date_input("Pilih Tanggal Kuitansi", datetime.today(), key="kwt_date_f", label_visibility="collapsed")
        date_mask = f"{str(sel_date)}%"
    elif tipe_filter == "Bulanan":
        with c2:
            sel_m_name = st.selectbox("Pilih Bulan", list(months_dict.keys()), key="kwt_m_f", label_visibility="collapsed")
        with c3:
            sel_y_m = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="kwt_my_f", label_visibility="collapsed")
        date_mask = f"{sel_y_m}-{months_dict[sel_m_name]}%"
    else:
        with c2:
            sel_y = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="kwt_y_f", label_visibility="collapsed")
        date_mask = f"{sel_y}%"
    st.markdown('</div>', unsafe_allow_html=True)

    # --- PENCARIAN & FILTER KASIR (COMPACT) ---
    st.markdown('<div class="compact-box">', unsafe_allow_html=True)
    f_crit, f_shift, f_limit, f_entries = st.columns([1.5, 1.0, 0.8, 1.5])
    with f_crit: ksr = st.text_input("Cari Kasir", placeholder="Nama kasir...", key="sc_ksr", label_visibility="collapsed")
    with f_shift: shf_opt = st.selectbox("Shift", ["Semua Shift", "Pagi", "Sore", "Malam"], key="sc_shift_split", label_visibility="collapsed")
    with f_limit: show_limit = st.selectbox("Show", [10, 25, 50, 100], key="sc_limit", label_visibility="collapsed")
    with f_entries: kw = st.text_input("Cari No Kertas", placeholder="🔍 No. Kertas...", key="sc_kw", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    query_str = "SELECT id, shift, input_date, receipt_date, receipt_no, final_amount, cashier_username FROM transactions WHERE receipt_date LIKE :dmask"
    params = {"dmask": date_mask}
    
    if current_role not in ["Super Admin", "Bendahara"]:
        query_str += " AND UPPER(cashier_username) = :cuser"
        params["cuser"] = current_logged_user

    if ksr.strip():
        query_str += " AND cashier_username LIKE :ksr"
        params["ksr"] = f"%{ksr.strip()}%"

    if shf_opt != "Semua Shift":
        query_str += " AND shift = :shf"
        params["shf"] = shf_opt

    if kw.strip():
        query_str += " AND receipt_no LIKE :kw"
        params["kw"] = f"%{kw.strip()}%"

    with get_db() as conn:
        count_query = query_str.replace("SELECT id, shift, input_date, receipt_date, receipt_no, final_amount, cashier_username", "SELECT COUNT(*)")
        total_data = conn.execute(text(count_query), params).fetchone()[0]

        sort_col_map = {
            "No": "id",
            "Shift": "shift",
            "Input": "input_date",
            "Tgl Kuitansi": "receipt_date",
            "No Kertas": "receipt_no",
            "Transaksi": "final_amount",
            "Kasir": "cashier_username"
        }
        db_sort_col = sort_col_map.get(st.session_state.sort_column, "id")
        
        final_query = query_str + f" ORDER BY {db_sort_col} {st.session_state.sort_order} LIMIT {int(show_limit)} OFFSET {st.session_state.page_offset}"
        
        tx_list = pd.read_sql_query(text(final_query), conn, params=params)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    if not tx_list.empty:
        def render_sort_header(col_name, label):
            curr_col = st.session_state.sort_column
            curr_ord = st.session_state.sort_order
            arrow = ""
            if curr_col == col_name:
                arrow = " ▾" if curr_ord == "DESC" else " ▴"
            
            if st.button(f"{label}{arrow}", key=f"sort_btn_{col_name}", use_container_width=True):
                if curr_col == col_name:
                    st.session_state.sort_order = "ASC" if curr_ord == "DESC" else "DESC"
                else:
                    st.session_state.sort_column = col_name
                    st.session_state.sort_order = "ASC"
                st.rerun()

        col_widths = [0.6, 0.7, 1.0, 1.2, 1.1, 1.2, 0.9, 1.2]
        st.markdown('<div class="sort-header-row">', unsafe_allow_html=True)
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_widths)
        with h1: render_sort_header("No", "No")
        with h2: render_sort_header("Shift", "Shift")
        with h3: render_sort_header("Input", "Input")
        with h4: render_sort_header("Tgl Kuitansi", "Tgl Kuitansi")
        with h5: render_sort_header("No Kertas", "No Kertas")
        with h6: render_sort_header("Transaksi", "Transaksi")
        with h7: render_sort_header("Kasir", "Kasir")
        h8.markdown("<div style='text-align:center; font-size:12.5px; font-weight:800; color:#FFFFFF; background:#028090; height:38px; display:flex; align-items:center; justify-content:center; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>AKSI</div>", unsafe_allow_html=True)
        st.markdown('</div><div style="height:6px;"></div>', unsafe_allow_html=True)

        for idx, row in tx_list.iterrows():
            st.markdown('<div class="kwt-row-card">', unsafe_allow_html=True)
            r1, r2, r3, r4, r5, r6, r7, r8 = st.columns(col_widths)
            
            r1.markdown(f"<div class='kwt-data-cell-bold'>{st.session_state.page_offset + idx + 1}</div>", unsafe_allow_html=True)
            r2.markdown(f"<div class='kwt-data-cell'>{row['shift']}</div>", unsafe_allow_html=True)
            r3.markdown(f"<div class='kwt-data-cell'>{row['input_date']}</div>", unsafe_allow_html=True)
            r4.markdown(f"<div class='kwt-data-cell'>{row['receipt_date']}</div>", unsafe_allow_html=True)
            r5.markdown(f"<div class='kwt-data-cell-bold'>#{row['receipt_no']}</div>", unsafe_allow_html=True)
            r6.markdown(f"<div class='kwt-data-cell-price'>{format_rupiah(row['final_amount'])}</div>", unsafe_allow_html=True)
            r7.markdown(f"<div class='kwt-data-cell'>{str(row['cashier_username']).upper()}</div>", unsafe_allow_html=True)
            
            with r8:
                st.markdown('<div class="action-stack">', unsafe_allow_html=True)
                
                st.markdown('<div class="btn-kwt-det">', unsafe_allow_html=True)
                if st.button("Detail", key=f"d_{row['receipt_no']}", use_container_width=True):
                    show_transaction_detail(row['receipt_no'])
                st.markdown('</div>', unsafe_allow_html=True)
                
                row_cashier = str(row['cashier_username']).upper()
                can_modify = False
                if current_role == "Super Admin":
                    can_modify = True
                elif current_role == "Bendahara" and row_cashier == current_logged_user:
                    can_modify = True
                elif current_role == "Kasir" and row_cashier == current_logged_user:
                    can_modify = True

                if can_modify:
                    st.markdown('<div class="btn-kwt-ed">', unsafe_allow_html=True)
                    if st.button("Edit", key=f"e_{row['receipt_no']}", use_container_width=True):
                        show_edit_dialog(row['receipt_no'])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="btn-kwt-del">', unsafe_allow_html=True)
                    if st.button("Hapus", key=f"h_{row['receipt_no']}", use_container_width=True):
                        confirm_delete_dialog(row['receipt_no'])
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:center; font-size:10px; color:#94A3B8; font-weight:700; height:44px; display:flex; align-items:center; justify-content:center;'>Read-Only</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        max_page = max(1, (total_data + int(show_limit) - 1) // int(show_limit))
        current_page = (st.session_state.page_offset // int(show_limit)) + 1

        p_col1, p_col2 = st.columns([2, 3])
        with p_col1:
            start_entry = st.session_state.page_offset + 1
            end_entry = min(st.session_state.page_offset + int(show_limit), total_data)
            st.markdown(f"<div style='color:#64748B; font-size:12.5px; font-weight:600; padding-top:4px;'>Showing {start_entry} to {end_entry} of {total_data} entries</div>", unsafe_allow_html=True)
            
        with p_col2:
            p_cols = st.columns(min(max_page + 2, 7))
            with p_cols[0]:
                if st.button("Previous", key="pagination_prev", disabled=(current_page == 1)):
                    st.session_state.page_offset = max(0, st.session_state.page_offset - int(show_limit))
                    st.rerun()
            for page_num in range(1, min(max_page + 1, 6)):
                with p_cols[page_num]:
                    is_current = (page_num == current_page)
                    btn_label = f"[{page_num}]" if is_current else str(page_num)
                    if st.button(btn_label, key=f"page_num_{page_num}", use_container_width=True):
                        st.session_state.page_offset = (page_num - 1) * int(show_limit)
                        st.rerun()
            with p_cols[-1]:
                if st.button("Next", key="pagination_next", disabled=(current_page >= max_page)):
                    st.session_state.page_offset += int(show_limit)
                    st.rerun()

    else:
        st.info("Tidak ada data kuitansi yang ditemukan untuk periode tersebut.")