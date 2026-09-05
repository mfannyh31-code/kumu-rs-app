import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header
from sqlalchemy import text

# =========================================================
# MODAL KONFIRMASI HAPUS PIUTANG
# =========================================================
@st.dialog("⚠️ Konfirmasi Hapus Data Piutang", width="small")
def confirm_delete_piutang_dialog(debt_id, receipt_no, patient_name):
    st.markdown(f"""
        <div style="text-align:center; padding: 5px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🗑️</div>
            <div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                Yakin ingin menghapus piutang <b>{patient_name}</b> (No. Ref: #{receipt_no})?
            </div>
            <div style="font-size: 12px; color: #EF4444; font-weight: 600;">
                Seluruh rincian tagihan dan riwayat akan dihapus permanen.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Batal", use_container_width=True, key=f"cancel_del_piu_{debt_id}"):
            st.rerun()
    with c2:
        if st.button("Ya, Hapus", use_container_width=True, type="primary", key=f"confirm_del_piu_{debt_id}"):
            with get_db() as conn_del:
                with conn_del.begin():
                    conn_del.execute(text("DELETE FROM receivables WHERE id = :did"), {"did": debt_id})
                    conn_del.execute(text("DELETE FROM receivables_items WHERE debt_id = :did"), {"did": debt_id})
                    conn_del.execute(text("DELETE FROM receivables_payments WHERE debt_id = :did"), {"did": debt_id})
            st.success("Piutang berhasil dihapus!")
            st.rerun()

# =========================================================
# MODAL PEMBAYARAN & RIWAYAT PIUTANG (PARSIAL)
# =========================================================
@st.dialog("💳 Pembayaran Piutang Pasien", width="large")
def bayar_piutang_dialog(debt_id, patient_name):
    with get_db() as conn:
        with conn.begin():
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS receivables_payments (
                    id SERIAL PRIMARY KEY,
                    debt_id INTEGER,
                    pay_date TEXT,
                    shift TEXT,
                    amount REAL,
                    method TEXT,
                    notes TEXT,
                    input_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

        res_debt = conn.execute(text("SELECT * FROM receivables WHERE id = :did"), {"did": debt_id})
        debt_row = res_debt.fetchone()
        debt_cols = list(res_debt.keys())
        debt_info = dict(zip(debt_cols, debt_row)) if debt_row else {}
        
        # Hanya ambil item yang belum lunas (paid_status != 'Lunas')
        res_items = conn.execute(text("SELECT * FROM receivables_items WHERE debt_id = :did AND paid_status != 'Lunas'"), {"did": debt_id})
        item_rows = res_items.fetchall()
        item_cols = list(res_items.keys())
        items = [dict(zip(item_cols, r)) for r in item_rows]

    st.markdown(f"Pasien: **{patient_name}** | No. Ref: **{debt_info.get('receipt_no', '')}**")
    st.markdown(f"Sisa Total Piutang: <strong style='color:#EF4444;'>{format_rupiah(debt_info.get('remaining_debt', 0))}</strong>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    selected_items_to_pay = []
    total_selected_tagihan = 0.0

    if items:
        st.markdown("##### ☑️ Centang Item Tindakan yang Ingin Dibayarkan:")
        for itm in items:
            col_chk, col_desc, col_val = st.columns([0.5, 3, 1.5])
            with col_chk:
                is_checked = st.checkbox("Pilih", key=f"pay_chk_item_{itm['id']}", label_visibility="collapsed")
            with col_desc:
                st.markdown(f"<strong>[{itm['category_name']}]</strong> {itm['action_name']}", unsafe_allow_html=True)
            with col_val:
                st.markdown(f"<div style='text-align:right; font-weight:800;'>{format_rupiah(itm['amount'])}</div>", unsafe_allow_html=True)
            
            if is_checked:
                selected_items_to_pay.append(itm)
                total_selected_tagihan += float(itm['amount'])
    else:
        st.success("🎉 Semua item tindakan pada piutang ini sudah lunas!")

    if items and total_selected_tagihan > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Total Tagihan Terpilih:** <span style='color:#028090; font-weight:800;'>{format_rupiah(total_selected_tagihan)}</span>", unsafe_allow_html=True)
        
        bp1, bp2 = st.columns(2)
        with bp1:
            pay_date = st.date_input("Tanggal Pembayaran", value=datetime.today(), key=f"pay_dt_{debt_id}")
            pay_shift = st.selectbox("Shift", ["Pagi", "Sore", "Malam"], key=f"pay_shf_{debt_id}")
        with bp2:
            pay_method = st.selectbox("Metode Pembayaran", ["Tunai", "Transfer Bank", "EDC Kartu", "QRIS", "Virtual Account"], key=f"pay_mth_{debt_id}")
            pay_notes = st.text_input("Catatan", value="Pelunasan Piutang", key=f"pay_not_{debt_id}")

        actual_pay_amount = st.number_input("Nominal Dibayar Kasir (Rp)", min_value=0.0, max_value=float(total_selected_tagihan), value=float(total_selected_tagihan), step=10000.0, format="%.0f", key=f"act_pay_{debt_id}")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Proses Pembayaran 💸", type="primary", use_container_width=True, key=f"btn_proc_pay_{debt_id}"):
            if actual_pay_amount <= 0:
                st.warning("Masukkan nominal pembayaran yang valid!")
            else:
                try:
                    current_user = str(st.session_state.get('user', 'ADMIN')).upper()
                    
                    with get_db() as conn:
                        with conn.begin():
                            conn.execute(text("""
                                INSERT INTO receivables_payments (debt_id, pay_date, shift, amount, method, notes, input_by)
                                VALUES (:did, :pdate, :shf, :amt, :meth, :notes, :usr)
                            """), {
                                "did": debt_id,
                                "pdate": str(pay_date),
                                "shf": pay_shift,
                                "amt": actual_pay_amount,
                                "meth": pay_method,
                                "notes": pay_notes,
                                "usr": current_user
                            })

                            sisa_bayar = actual_pay_amount
                            for itm in selected_items_to_pay:
                                itm_id = itm['id']
                                itm_amt = float(itm['amount'])
                                
                                if sisa_bayar >= itm_amt:
                                    conn.execute(text("UPDATE receivables_items SET paid_status = 'Lunas' WHERE id = :iid"), {"iid": itm_id})
                                    sisa_bayar -= itm_amt
                                elif sisa_bayar > 0:
                                    sisa_item_baru = itm_amt - sisa_bayar
                                    conn.execute(text("UPDATE receivables_items SET amount = :sisa, paid_status = 'Belum Lunas' WHERE id = :iid"), {"sisa": sisa_item_baru, "iid": itm_id})
                                    sisa_bayar = 0.0
                                    break
                                else:
                                    break

                            res_sisa = conn.execute(text("SELECT SUM(amount) FROM receivables_items WHERE debt_id = :did AND paid_status = 'Belum Lunas'"), {"did": debt_id}).fetchone()
                            sisa_db_baru = float(res_sisa[0] or 0.0) if res_sisa else 0.0
                            
                            new_paid_total = float(debt_info.get('paid_amount', 0) or 0.0) + actual_pay_amount
                            new_status = "Lunas" if sisa_db_baru <= 0 else "Belum Lunas"

                            conn.execute(text("""
                                UPDATE receivables 
                                SET paid_amount = :pamt, remaining_debt = :remdb, status = :st
                                WHERE id = :did
                            """), {
                                "pamt": new_paid_total,
                                "remdb": sisa_db_baru,
                                "st": new_status,
                                "did": debt_id
                            })

                    st.success("✓ Pembayaran piutang berhasil dicatat dan masuk ke laporan kasir!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memproses pembayaran: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Tutup Jendela", key=f"close_pay_{debt_id}", use_container_width=True):
        st.rerun()

# =========================================================
# MODAL DETAIL PIUTANG (DENGAN RIWAYAT PEMBAYARAN)
# =========================================================
@st.dialog("🔍 Detail Rincian Piutang & Riwayat", width="large")
def detail_piutang_dialog(debt_id, patient_name):
    with get_db() as conn:
        res_debt = conn.execute(text("SELECT * FROM receivables WHERE id = :did"), {"did": debt_id})
        d_row = res_debt.fetchone()
        debt = dict(zip(list(res_debt.keys()), d_row)) if d_row else {}

        res_items = conn.execute(text("SELECT * FROM receivables_items WHERE debt_id = :did"), {"did": debt_id})
        i_rows = res_items.fetchall()
        items = [dict(zip(list(res_items.keys()), r)) for r in i_rows]
        
        res_pay = conn.execute(text("SELECT * FROM receivables_payments WHERE debt_id = :did ORDER BY id DESC"), {"did": debt_id})
        p_rows = res_pay.fetchall()
        history_pay = [dict(zip(list(res_pay.keys()), r)) for r in p_rows]

    st.markdown(f"#### Rincian Tagihan Pasien: **{patient_name}**")
    st.markdown(f"No. Ref: **{debt.get('receipt_no', '')}** | Jatuh Tempo: **{debt.get('due_date', '')}** | Status: **{debt.get('status', '')}**")
    st.markdown(f"Total Tagihan: **{format_rupiah(debt.get('total_bill', 0))}** | Sisa: <strong style='color:#EF4444;'>{format_rupiah(debt.get('remaining_debt', 0))}</strong>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    if items:
        for idx, itm in enumerate(items, 1):
            badge = "<span style='background:#10B981; color:#fff; font-size:10px; padding:2px 5px; border-radius:3px;'>LUNAS</span>" if itm['paid_status'] == 'Lunas' else "<span style='background:#EF4444; color:#fff; font-size:10px; padding:2px 5px; border-radius:3px;'>BELUM LUNAS</span>"
            st.markdown(f"**{idx}. [{itm['category_name']}] {itm['action_name']}** — {format_rupiah(itm['amount'])} {badge}", unsafe_allow_html=True)
    else:
        st.info("Tidak ada rincian item.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📜 Riwayat Pembayaran Sebelumnya")
    
    if history_pay:
        for idx, hp in enumerate(history_pay, 1):
            hp_shift = hp['shift'] if hp.get('shift') else 'Pagi'
            st.markdown(f"""
                <div style="background:#F8FAFC; border:1px solid #CBD5E1; padding:8px 12px; border-radius:6px; margin-bottom:5px; font-size:12.5px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{idx}. Tgl: {hp['pay_date']} (Shift: {hp_shift})</strong>
                        <span style="color:#10B981; font-weight:800;">{format_rupiah(hp['amount'])}</span>
                    </div>
                    <div style="color:#475569; margin-top:2px;">
                        Metode: <b>{hp['method']}</b> | Kasir: <strong style="color:#028090;">{str(hp['input_by']).upper()}</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Belum ada riwayat pembayaran.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Tutup Detail", key=f"cls_det_{debt_id}", use_container_width=True):
        st.rerun()

# =========================================================
# MODAL EDIT HISTORY PEMBAYARAN PIUTANG (DENGAN SHIFT)
# =========================================================
@st.dialog("✏️ Edit & Koreksi Riwayat Pembayaran", width="large")
def edit_piutang_dialog(debt_id):
    with get_db() as conn:
        res_row = conn.execute(text("SELECT * FROM receivables WHERE id = :did"), {"did": debt_id})
        r_fetch = res_row.fetchone()
        row = dict(zip(list(res_row.keys()), r_fetch)) if r_fetch else {}

        res_pay = conn.execute(text("SELECT * FROM receivables_payments WHERE debt_id = :did ORDER BY id ASC"), {"did": debt_id})
        p_fetches = res_pay.fetchall()
        p_cols = list(res_pay.keys())
        payments = [dict(zip(p_cols, p)) for p in p_fetches]

    st.markdown(f"Pasien: **{row.get('patient_name', '')}** | No. Ref: **{row.get('receipt_no', '')}**")
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    if payments:
        for idx, p in enumerate(payments, 1):
            pid = p['id']
            p_shift = p['shift'] if p.get('shift') else 'Pagi'
            with st.expander(f"Histori #{idx} | Tgl: {p['pay_date']} | Shift: {p_shift} | Nominal: {format_rupiah(p['amount'])}"):
                with st.form(f"form_edit_pay_{pid}"):
                    ed_pdate = st.date_input("Tanggal", value=datetime.strptime(p['pay_date'], "%Y-%m-%d").date(), key=f"ed_pdt_{pid}")
                    
                    shift_options = ["Pagi", "Sore", "Malam"]
                    shift_idx = shift_options.index(p_shift) if p_shift in shift_options else 0
                    ed_pshift = st.selectbox("Shift", shift_options, index=shift_idx, key=f"ed_pshf_{pid}")

                    ed_pamt = st.number_input("Nominal (Rp)", value=float(p['amount']), step=10000.0, format="%.0f", key=f"ed_pamt_{pid}")
                    
                    if st.form_submit_button("Simpan Koreksi 💾", use_container_width=True):
                        with get_db() as conn_h:
                            with conn_h.begin():
                                conn_h.execute(text("""
                                    UPDATE receivables_payments 
                                    SET pay_date = :pdate, shift = :shf, amount = :amt 
                                    WHERE id = :pid
                                """), {
                                    "pdate": str(ed_pdate),
                                    "shf": ed_pshift,
                                    "amt": ed_pamt,
                                    "pid": pid
                                })
                                
                                res_sum = conn_h.execute(text("SELECT SUM(amount) FROM receivables_payments WHERE debt_id = :did"), {"did": debt_id}).fetchone()
                                tot_paid_real = float(res_sum[0] or 0.0) if res_sum else 0.0
                                
                                res_bill = conn_h.execute(text("SELECT total_bill FROM receivables WHERE id = :did"), {"did": debt_id}).fetchone()
                                tot_bill_val = float(res_bill[0] or 0.0) if res_bill else 0.0
                                
                                new_rem = max(0.0, tot_bill_val - tot_paid_real)
                                new_st = "Lunas" if new_rem <= 0 else "Belum Lunas"
                                
                                conn_h.execute(text("""
                                    UPDATE receivables 
                                    SET paid_amount = :pamt, remaining_debt = :remdb, status = :st 
                                    WHERE id = :did
                                """), {
                                    "pamt": tot_paid_real,
                                    "remdb": new_rem,
                                    "st": new_st,
                                    "did": debt_id
                                })
                        
                        st.success("Histori pembayaran dan shift berhasil dikoreksi!")
                        st.rerun()
    else:
        st.info("Belum ada riwayat pembayaran.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Tutup Jendela Edit", key=f"close_edit_{debt_id}", use_container_width=True):
        st.rerun()

# =========================================================
# HALAMAN UTAMA MANAJEMEN PIUTANG (COMPACT VIEW)
# =========================================================
def render_page():
    render_header("📑 Manajemen Piutang Pasien", "Pantau tagihan, pilih item tindakan spesifik untuk dibayar, dan kelola laporan.")

    with get_db() as conn:
        with conn.begin():
            conn.execute(text("""CREATE TABLE IF NOT EXISTS receivables (
                id SERIAL PRIMARY KEY, receipt_no TEXT, patient_id TEXT, patient_name TEXT, 
                total_bill REAL, paid_amount REAL, remaining_debt REAL, due_date TEXT, status TEXT, notes TEXT, input_by TEXT
            )"""))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS receivables_items (
                id SERIAL PRIMARY KEY, debt_id INTEGER, category_name TEXT, action_name TEXT, 
                amount REAL, paid_status TEXT, notes TEXT
            )"""))

    # CSS Kompak untuk Halaman Piutang
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
        .debt-row-card {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            margin-bottom: 6px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            align-items: center !important;
        }
        .debt-row-card:hover {
            background-color: #F8FAFC !important;
        }
        .debt-row-card div[data-testid="column"] {
            display: flex;
            align-items: center;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
        .debt-row-card div[data-testid="column"] div.stButton {
            margin-bottom: 0px !important;
        }
        .debt-row-card div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            height: 26px !important;
            min-height: 26px !important;
            font-size: 11.5px !important;
            border-radius: 4px !important;
            padding: 0px !important;
            border: none !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        .btn-piu-det button { background-color: #3B82F6 !important; }
        .btn-piu-pay button { background-color: #10B981 !important; }
        .btn-piu-edit button { background-color: #F59E0B !important; }
        .btn-piu-del button { background-color: #EF4444 !important; }
        </style>
    """, unsafe_allow_html=True)

    h1, h2, h3 = st.columns([1.5, 1.5, 1.2])
    with h1:
        if st.button("➕ Tambah Piutang Baru", use_container_width=True, type="primary"):
            st.session_state.current_menu = "input_piutang"
            st.rerun()
    with h3:
        if st.button("📊 Laporan Piutang", use_container_width=True):
            st.session_state.current_menu = "laporan_piutang"
            st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # --- KONTROL FILTER WAKTU (COMPACT) ---
    st.markdown('<div class="compact-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
    with c1:
        tipe_filter = st.selectbox("Jenis Periode", ["Harian", "Bulanan", "Tahunan"], key="piu_tipe_f", label_visibility="collapsed")
    
    months_dict = {
        "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12",
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04", "Mei": "05", "Juni": "06", "Juli": "07"
    }
    years_list = [str(y) for y in range(2024, 2032)]
    current_year_str = str(datetime.today().year)

    if tipe_filter == "Harian":
        with c2:
            sel_date = st.date_input("Pilih Tanggal", datetime.today(), key="piu_date_f", label_visibility="collapsed")
        date_mask = f"{str(sel_date)}%"
    elif tipe_filter == "Bulanan":
        with c2:
            sel_m_name = st.selectbox("Pilih Bulan", list(months_dict.keys()), key="piu_m_f", label_visibility="collapsed")
        with c3:
            sel_y_m = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="piu_my_f", label_visibility="collapsed")
        date_mask = f"{sel_y_m}-{months_dict[sel_m_name]}%"
    else:
        with c2:
            sel_y = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="piu_y_f", label_visibility="collapsed")
        date_mask = f"{sel_y}%"
    st.markdown('</div>', unsafe_allow_html=True)

    # --- FILTER PENCARIAN & STATUS (COMPACT) ---
    st.markdown('<div class="compact-box">', unsafe_allow_html=True)
    f1, f2 = st.columns([2.5, 1.5])
    with f1: search_kw = st.text_input("🔍 Cari RM / Nama / No. Ref", placeholder="Ketik kata kunci...", key="piu_search", label_visibility="collapsed")
    with f2: status_filter = st.selectbox("Status Piutang", ["Semua", "Belum Lunas", "Lunas"], key="piu_status_filter", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    query = "SELECT * FROM receivables WHERE due_date LIKE :dmask"
    params = {"dmask": date_mask}
    
    if search_kw.strip():
        query += " AND (patient_name LIKE :kw OR patient_id LIKE :kw OR receipt_no LIKE :kw)"
        params["kw"] = f"%{search_kw.strip()}%"
    if status_filter != "Semua":
        query += " AND status = :st"
        params["st"] = status_filter
        
    query += " ORDER BY id DESC"
    
    with get_db() as conn:
        df_debt = pd.read_sql_query(text(query), conn, params=params)

    if not df_debt.empty:
        # Header Tabel Kompak
        st.markdown("""
            <div style="background:#028090; color:white; padding:8px 12px; border-radius:6px; font-weight:700; font-size:12.5px; margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="width:25%;">Nama Pasien / RM</span>
                    <span style="width:15%;">No. Ref / Tempo</span>
                    <span style="width:18%;">Total Tagihan</span>
                    <span style="width:18%;">Sisa Piutang</span>
                    <span style="width:24%; text-align:center;">Aksi</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        for idx, r in df_debt.iterrows():
            status_badge = "<span style='background:#EF4444; color:#fff; font-size:9.5px; padding:1px 5px; border-radius:3px;'>BELUM LUNAS</span>" if r['status'] == 'Belum Lunas' else "<span style='background:#10B981; color:#fff; font-size:9.5px; padding:1px 5px; border-radius:3px;'>LUNAS</span>"
            
            st.markdown('<div class="debt-row-card">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2.2, 1.5, 1.8, 1.8, 0.6, 0.6, 0.6, 0.6])
            
            with col1:
                st.markdown(f"<b>{r['patient_name']}</b><br><span style='font-size:11px; color:#64748B;'>RM: {r['patient_id'] or '-'}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<b>#{r['receipt_no']}</b><br><span style='font-size:11px; color:#64748B;'>{r['due_date']}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"{format_rupiah(r['total_bill'])}", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<span style='color:#EF4444; font-weight:700;'>{format_rupiah(r['remaining_debt'])}</span><br>{status_badge}", unsafe_allow_html=True)
            
            with col5:
                st.markdown('<div class="btn-piu-det">', unsafe_allow_html=True)
                if st.button("🔍", key=f"det_piu_{r['id']}", help="Detail", use_container_width=True):
                    detail_piutang_dialog(r['id'], r['patient_name'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col6:
                st.markdown('<div class="btn-piu-pay">', unsafe_allow_html=True)
                if r['status'] == 'Belum Lunas':
                    if st.button("💳", key=f"pay_piu_{r['id']}", help="Bayar", use_container_width=True):
                        bayar_piutang_dialog(r['id'], r['patient_name'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col7:
                st.markdown('<div class="btn-piu-edit">', unsafe_allow_html=True)
                if st.button("✏️", key=f"edit_piu_{r['id']}", help="Edit", use_container_width=True):
                    edit_piutang_dialog(r['id'])
                st.markdown('</div>', unsafe_allow_html=True)
            with col8:
                st.markdown('<div class="btn-piu-del">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_piu_{r['id']}", help="Hapus", use_container_width=True):
                    confirm_delete_piutang_dialog(r['id'], r['receipt_no'], r['patient_name'])
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Tidak ada data piutang yang ditemukan pada periode tersebut.")