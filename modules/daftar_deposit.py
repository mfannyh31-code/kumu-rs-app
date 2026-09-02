import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header

# =========================================================
# MODAL DETAIL RIWAYAT TRANSAKSI PASIEN
# =========================================================
@st.dialog("🔍 Detail Riwayat Saldo & Transaksi", width="large")
def show_detail_dialog(patient_id, patient_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deposits WHERE patient_id = ? ORDER BY id DESC", (patient_id,))
    rows = cursor.fetchall()
    
    if rows:
        col_names = [desc[0].lower() for desc in cursor.description]
        st.markdown(f"<h4 style='color:#0F172A;'>Riwayat Pasien: {patient_name} (RM: {patient_id})</h4>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        
        for r in rows:
            d = dict(zip(col_names, r))
            amt = float(d.get('amount', 0) or 0)
            is_masuk = amt > 0
            badge_color = "#10B981" if is_masuk else "#EF4444"
            badge_label = "SETORAN / TOPUP" if is_masuk else "PEMAKAIAN / REFUND"
            shf = d.get('shift', 'Pagi') or 'Pagi'
            
            st.markdown(f"""
                <div style="background:#F8FAFC; border:1px solid #CBD5E1; padding:10px 14px; border-radius:8px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>Tanggal: {d.get('deposit_date', '-')} | Shift: {shf}</strong>
                        <span style="background:{badge_color}; color:#fff; font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px;">{badge_label}</span>
                    </div>
                    <div style="font-size:14px; margin-top:4px;">Nominal: <span style="color:{badge_color}; font-weight:800;">{format_rupiah(amt)}</span></div>
                    <span style="font-size:12px; color:#64748B;">Metode: {d.get('payment_method', '-')} | User: <strong>{str(d.get('input_by', '-')).upper()}</strong></span><br>
                    <span style="font-size:12px; font-style:italic; color:#475569;">Catatan: {d.get('notes', '-') or '-'}</span>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Tutup", key=f"close_det_{patient_id}", use_container_width=True):
            st.rerun()
    conn.close()

# =========================================================
# MODAL REFUND / PENGEMBALIAN SISA SALDO
# =========================================================
@st.dialog("💸 Pengembalian (Refund) Sisa Saldo Pasien", width="small")
def refund_dialog(patient_id, patient_name, sisa_saldo):
    st.markdown(f"Pasien: **{patient_name}**<br>Sisa Saldo Aktif: **{format_rupiah(sisa_saldo)}**", unsafe_allow_html=True)
    
    rf_date = st.date_input("Tanggal Refund", value=datetime.today())
    rf_shift = st.selectbox("Shift Refund", ["Pagi", "Sore", "Malam"])
    rf_method = st.selectbox("Metode Pengembalian", ["Tunai", "Transfer"])
    
    refund_amt = st.number_input("Nominal Pengembalian (Rp)", min_value=0.0, max_value=float(sisa_saldo), value=float(sisa_saldo), format="%.0f")
    rf_notes = st.text_input("Catatan", value="REFUND SISA SALDO")
    
    if st.button("Proses Refund Sekarang 💸", use_container_width=True, type="primary"):
        conn = get_db()
        c = conn.cursor()
        
        c.execute("PRAGMA table_info(deposits)")
        cols = [row[1] for row in c.fetchall()]
        if "shift" not in cols:
            c.execute("ALTER TABLE deposits ADD COLUMN shift TEXT DEFAULT 'Pagi'")

        c.execute("""
            INSERT INTO deposits (patient_id, patient_name, amount, deposit_date, shift, payment_method, notes, status, input_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'USED', ?)
        """, (patient_id, patient_name, -refund_amt, str(rf_date), rf_shift, rf_method, rf_notes, str(st.session_state.get('user', 'admin')).upper()))
        
        conn.commit()
        conn.close()
        st.success(f"Refund {rf_method} berhasil diproses dan tercatat di laporan kasir!")
        st.rerun()

# =========================================================
# MODAL EDIT / KOREKSI SEMUA RIWAYAT PASIEN
# =========================================================
@st.dialog("✏️ Koreksi Riwayat Deposit Pasien", width="large")
def show_edit_dialog(patient_id, patient_name):
    conn = get_db()
    df_riwayat = pd.read_sql_query("SELECT * FROM deposits WHERE patient_id = ? ORDER BY id DESC", conn, params=[patient_id])
    
    st.markdown(f"Pilih transaksi dari riwayat pasien **{patient_name}** (RM: {patient_id}) yang ingin dikoreksi:")
    
    if not df_riwayat.empty:
        for _, row in df_riwayat.iterrows():
            dep_id = row['id']
            amt = float(row['amount'] or 0)
            dt = row['deposit_date']
            shf = row.get('shift', 'Pagi') or 'Pagi'
            meth = row['payment_method']
            notes = row['notes'] or ''
            usr = str(row.get('input_by', 'ADMIN')).upper()
            
            with st.expander(f"ID: #{dep_id} | Tgl: {dt} ({shf}) | Nominal: {format_rupiah(amt)} | User: {usr}"):
                with st.form(f"form_edit_item_{dep_id}"):
                    d_val = datetime.strptime(dt, "%Y-%m-%d") if dt else datetime.today()
                    new_date = st.date_input("Tanggal", value=d_val, key=f"dt_{dep_id}")
                    
                    shift_opts = ["Pagi", "Sore", "Malam"]
                    curr_shf = shf if shf in shift_opts else "Pagi"
                    new_shift = st.selectbox("Shift", shift_opts, index=shift_opts.index(curr_shf), key=f"shf_{dep_id}")
                    
                    new_amt = st.number_input("Nominal (Rp)", value=float(amt), step=10000.0, format="%.0f", key=f"amt_{dep_id}")
                    
                    meth_opts = ["Tunai", "Transfer", "EDC"]
                    curr_meth = meth if meth in meth_opts else "Tunai"
                    new_meth = st.selectbox("Metode", meth_opts, index=meth_opts.index(curr_meth), key=f"meth_{dep_id}")
                    
                    new_notes = st.text_area("Catatan", value=str(notes), key=f"not_{dep_id}")
                    
                    if st.form_submit_button(f"Simpan Perubahan #{dep_id} 💾", use_container_width=True):
                        c = conn.cursor()
                        c.execute("""
                            UPDATE deposits 
                            SET amount = ?, deposit_date = ?, shift = ?, payment_method = ?, notes = ?, input_by = ? 
                            WHERE id = ?
                        """, (new_amt, str(new_date), new_shift, new_meth, new_notes, str(st.session_state.get('user', 'admin')).upper(), dep_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Transaksi ID #{dep_id} berhasil dikoreksi!")
                        st.rerun()
    else:
        st.info("Tidak ada riwayat transaksi ditemukan untuk pasien ini.")
    conn.close()

# =========================================================
# MODAL HAPUS PER RIWAYAT / TRANSAKSI
# =========================================================
@st.dialog("🗑️ Hapus Riwayat Deposit", width="large")
def confirm_delete(patient_id, patient_name):
    conn = get_db()
    df_riwayat = pd.read_sql_query("SELECT * FROM deposits WHERE patient_id = ? ORDER BY id DESC", conn, params=[patient_id])
    
    st.markdown(f"Pilih transaksi dari riwayat pasien **{patient_name}** (RM: {patient_id}) yang ingin dihapus:")
    
    if not df_riwayat.empty:
        for _, row in df_riwayat.iterrows():
            dep_id = row['id']
            amt = float(row['amount'] or 0)
            dt = row['deposit_date']
            shf = row.get('shift', 'Pagi') or 'Pagi'
            meth = row['payment_method']
            notes = row['notes'] or '-'
            usr = str(row.get('input_by', '-')).upper()
            
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #CBD5E1; padding:8px; border-radius:6px; margin-bottom:6px; font-size:13px;">
                        <strong>ID: #{dep_id}</strong> | Tgl: {dt} | Shift: {shf} | User: {usr}<br>
                        Nominal: <strong style="color:#EF4444;">{format_rupiah(amt)}</strong> via {meth} | Catatan: {notes}
                    </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                if st.button("Hapus", key=f"del_item_{dep_id}", use_container_width=True, type="primary"):
                    c = conn.cursor()
                    c.execute("DELETE FROM deposits WHERE id = ?", (dep_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Transaksi ID #{dep_id} berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Tidak ada riwayat transaksi ditemukan.")
    conn.close()

# =========================================================
# HALAMAN UTAMA DAFTAR DEPOSIT
# =========================================================
def render_page():
    conn = get_db()
    render_header("📋 Daftar & Monitoring Saldo Deposit", "Pantau saldo awal, pemakaian, sisa akhir, dan lakukan pengembalian (refund)")

    st.markdown("""
        <style>
        .deposit-card {
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 10px !important;
            padding: 14px 18px !important;
            margin-bottom: 10px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        </style>
    """, unsafe_allow_html=True)

    c_top1, c_top2 = st.columns([3, 1])
    with c_top1:
        st.markdown("<h4 style='color:#0F172A; margin:0;'>Daftar Pasien & Saldo</h4>", unsafe_allow_html=True)
    with c_top2:
        if st.button("➕ Tambah Uang Muka", use_container_width=True, type="primary"):
            st.session_state.current_menu = "input_deposit"
            if 'auto_fill_rm' in st.session_state:
                del st.session_state['auto_fill_rm']
            st.rerun()

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    
    try:
        users_df = pd.read_sql_query("SELECT DISTINCT input_by FROM deposits WHERE input_by IS NOT NULL", conn)
        list_users = ["Semua User"] + [str(u).upper() for u in users_df['input_by'].tolist() if str(u).strip() != ""]
    except:
        list_users = ["Semua User"]
    
    # --- KONTROL FILTER WAKTU (HARIAN, BULANAN, TAHUNAN) ---
    st.markdown('<div style="background:#FFFFFF; padding:20px; border-radius:10px; border:1px solid #CBD5E1; margin-bottom:20px;">', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
    with c1:
        tipe_laporan = st.selectbox("Jenis Periode", ["Harian", "Bulanan", "Tahunan"], key="dep_tipe_f")
    
    months_dict = {
        "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12",
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04", "Mei": "05", "Juni": "06", "Juli": "07"
    }
    years_list = [str(y) for y in range(2024, 2032)]
    current_year_str = str(datetime.today().year)

    if tipe_laporan == "Harian":
        with c2:
            filter_val = st.date_input("Pilih Tanggal", datetime.today(), key="dep_date_f")
        date_mask = f"{str(filter_val)}%"
    elif tipe_laporan == "Bulanan":
        with c2:
            sel_month_name = st.selectbox("Pilih Bulan", list(months_dict.keys()), key="dep_m_f")
        with c3:
            sel_year_m = st.selectbox("Pilih Tahun (Bulan)", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="dep_my_f")
        m_num = months_dict[sel_month_name]
        date_mask = f"{sel_year_m}-{m_num}%"
    else:
        with c2:
            sel_year = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0, key="dep_y_f")
        date_mask = f"{sel_year}%"

    st.markdown('</div>', unsafe_allow_html=True)

    f_search, f_status, f_user = st.columns([2.5, 1.5, 1.5])
    with f_search:
        search_kw = st.text_input("🔍 Cari RM/Nama Pasien", placeholder="Ketik nomor RM atau nama...")
    with f_status:
        status_filter = st.selectbox("Status Saldo", ["Semua", "Ada Saldo (Aktif)", "Saldo Habis (0)"])
    with f_user:
        user_filter = st.selectbox("Kasir / User", list_users)

    df_all = pd.read_sql_query("SELECT * FROM deposits WHERE deposit_date LIKE ? ORDER BY id DESC", conn, params=[date_mask])
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    if not df_all.empty:
        mask = pd.Series(True, index=df_all.index)
        
        if search_kw.strip():
            mask = mask & (df_all['patient_id'].str.contains(search_kw.strip(), case=False, na=False) | 
                           df_all['patient_name'].str.contains(search_kw.strip(), case=False, na=False))
                           
        if user_filter != "Semua User":
            mask = mask & (df_all['input_by'].str.upper() == user_filter)
            
        df_filtered = df_all[mask]
        valid_patients = df_filtered['patient_id'].unique()
        
        count_display = 0
        
        for pid in valid_patients:
            p_data = df_all[df_all['patient_id'] == pid] 
            name = p_data['patient_name'].iloc[0]
            
            total_setor = p_data[p_data['amount'] > 0]['amount'].sum()
            total_pakai = p_data[p_data['amount'] < 0]['amount'].abs().sum()
            sisa_akhir = total_setor - total_pakai
            
            if status_filter == "Ada Saldo (Aktif)" and sisa_akhir <= 0:
                continue
            if status_filter == "Saldo Habis (0)" and sisa_akhir > 0:
                continue
                
            count_display += 1
            
            st.markdown('<div class="deposit-card">', unsafe_allow_html=True)
            col_info, col_val, col_action = st.columns([2, 2.2, 1.8])
            
            with col_info:
                st.markdown(f"""
                    <div style="font-size:16px; font-weight:800; color:#0F172A;">{name}</div>
                    <div style="font-size:13px; color:#64748B; font-weight:700;">No. RM: {pid}</div>
                """, unsafe_allow_html=True)
                
            with col_val:
                status_badge = "<span style='background:#10B981; color:#fff; font-size:10px; padding:2px 6px; border-radius:4px;'>AKTIF</span>" if sisa_akhir > 0 else "<span style='background:#64748B; color:#fff; font-size:10px; padding:2px 6px; border-radius:4px;'>HABIS / 0</span>"
                st.markdown(f"""
                    <div style="font-size:12px; color:#475569;">Saldo Awal/Setor: <strong>{format_rupiah(total_setor)}</strong></div>
                    <div style="font-size:12px; color:#EF4444;">Total Pemakaian: <strong>-{format_rupiah(total_pakai)}</strong></div>
                    <div style="font-size:14px; font-weight:800; color:#028090; margin-top:2px;">Sisa Saldo: {format_rupiah(sisa_akhir)} {status_badge}</div>
                """, unsafe_allow_html=True)
                
            with col_action:
                b1, b2, b3, b4, b5 = st.columns(5)
                with b1:
                    if st.button("🔍", key=f"det_{pid}", help="Detail Riwayat"):
                        show_detail_dialog(pid, name)
                with b2:
                    if st.button("➕", key=f"top_{pid}", help="Top Up Saldo"):
                        st.session_state.current_menu = "input_deposit"
                        st.session_state.auto_fill_rm = pid
                        st.rerun()
                with b3:
                    if sisa_akhir > 0:
                        if st.button("💸", key=f"ref_{pid}", help="Refund Sisa Saldo"):
                            refund_dialog(pid, name, sisa_akhir)
                with b4:
                    if st.button("✏️", key=f"edit_{pid}", help="Edit Semua Riwayat"):
                        show_edit_dialog(pid, name)
                with b5:
                    if st.button("🗑️", key=f"del_{pid}", help="Hapus Riwayat"):
                        confirm_delete(pid, name)
                        
            st.markdown('</div>', unsafe_allow_html=True)
            
        if count_display == 0:
            st.info("Tidak ada data yang sesuai dengan filter pencarian Anda.")
    else:
        st.info("Belum ada data uang muka atau deposit yang tercatat pada periode tersebut.")

    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()