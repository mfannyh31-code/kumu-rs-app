import streamlit as st
import sqlite3
from datetime import datetime
from db import get_db, format_rupiah, render_header

def render_page():
    render_header("💰 Input Uang Muka / Deposit Pasien", "Catat setoran deposit baru atau top-up saldo pasien dengan mudah")

    if 'deposit_reset_cnt' not in st.session_state:
        st.session_state.deposit_reset_cnt = 0
    cnt = st.session_state.deposit_reset_cnt

    # Tangkap request Top Up dari menu daftar
    auto_rm = st.session_state.get('auto_fill_rm', "")
    if 'auto_fill_rm' in st.session_state: 
        del st.session_state.auto_fill_rm

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown("##### ➕ Form Setoran Deposit Baru")
    st.markdown("<hr style='margin:10px 0 16px 0; border:none; border-top:1.5px solid #CBD5E1;'>", unsafe_allow_html=True)

    # Inisialisasi state key untuk widget
    rm_key = f"dep_rm_{cnt}"
    name_key = f"dep_name_{cnt}"

    if rm_key not in st.session_state:
        st.session_state[rm_key] = auto_rm
    if name_key not in st.session_state:
        st.session_state[name_key] = ""

    # Jika auto_rm terisi dari tombol top-up, cari namanya langsung dari database
    if auto_rm and not st.session_state[name_key]:
        conn_auto = get_db()
        res_auto = conn_auto.cursor().execute("SELECT patient_name FROM deposits WHERE patient_id = ? LIMIT 1", (auto_rm,)).fetchone()
        if res_auto:
            st.session_state[name_key] = res_auto[0]
        conn_auto.close()

    # Callback reaktif saat No. RM diubah
    def update_name_from_db():
        rm_val = st.session_state.get(rm_key, "").strip()
        if rm_val:
            db_conn = get_db()
            cursor = db_conn.cursor()
            cursor.execute("SELECT patient_name FROM deposits WHERE patient_id = ? LIMIT 1", (rm_val,))
            res = cursor.fetchone()
            if res:
                st.session_state[name_key] = res[0]
            db_conn.close()

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        patient_rm = st.text_input(
            "No. Rekam Medis (No. RM) *", 
            placeholder="Contoh: RM-98214", 
            key=rm_key, 
            on_change=update_name_from_db
        )
        
        patient_name = st.text_input(
            "Nama Lengkap Pasien *", 
            placeholder="Ketik atau otomatis terisi...", 
            key=name_key
        )
        
        # Cek sisa saldo aktif secara instan berdasarkan No. RM yang aktif diketik/dipilih
        current_rm_val = patient_rm.strip()
        if current_rm_val:
            conn_s = get_db()
            all_dep = conn_s.cursor().execute("SELECT amount FROM deposits WHERE patient_id = ?", (current_rm_val,)).fetchall()
            conn_s.close()
            if all_dep:
                total_setor = sum([row[0] for row in all_dep if row[0] > 0])
                total_pakai = sum([abs(row[0]) for row in all_dep if row[0] < 0])
                sisa_cek = total_setor - total_pakai
                st.info(f"ℹ️ Sisa Saldo Aktif Pasien: **{format_rupiah(sisa_cek)}**")

        deposit_amount = st.number_input("Nominal Setoran (Rp) *", min_value=0.0, value=0.0, step=50000.0, format="%.0f", key=f"dep_amt_{cnt}")

    with col_i2:
        deposit_date = st.date_input("Tanggal Setor *", value=datetime.today(), key=f"dep_date_{cnt}")
        dep_shift = st.selectbox("Shift *", ["Pagi", "Sore", "Malam"], key=f"dep_shift_{cnt}")
        payment_method = st.selectbox("Metode Pembayaran *", ["Tunai", "Transfer", "EDC"], key=f"dep_method_{cnt}")
        notes = st.text_area("Keterangan / Catatan", placeholder="Contoh: Setoran awal rawat inap kelas 2", key=f"dep_notes_{cnt}")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🔄 Reset Form", use_container_width=True, key=f"btn_reset_dep_{cnt}"):
            st.session_state.deposit_reset_cnt += 1
            st.rerun()
    with col_b2:
        if st.button("💾 Simpan Setoran", use_container_width=True, type="primary", key=f"btn_save_dep_{cnt}"):
            final_rm = patient_rm.strip()
            final_name = st.session_state.get(name_key, "").strip()

            if not final_rm or not final_name:
                st.error("No. RM dan Nama Pasien wajib diisi.")
            elif deposit_amount <= 0:
                st.error("Nominal setoran harus lebih besar dari 0.")
            else:
                conn = get_db()
                c = conn.cursor()
                
                # Pastikan tabel & kolom shift lengkap
                c.execute("""CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    patient_id TEXT, 
                    patient_name TEXT, 
                    amount REAL, 
                    deposit_date TEXT, 
                    shift TEXT,
                    payment_method TEXT, 
                    notes TEXT, 
                    status TEXT, 
                    input_by TEXT
                )""")
                
                c.execute("PRAGMA table_info(deposits)")
                cols = [row[1] for row in c.fetchall()]
                if "shift" not in cols:
                    c.execute("ALTER TABLE deposits ADD COLUMN shift TEXT DEFAULT 'Pagi'")
                
                current_user = str(st.session_state.get('user', 'admin')).upper()

                # Masukkan nilai positif untuk setoran/topup baru beserta shift dan user
                c.execute("""
                    INSERT INTO deposits (patient_id, patient_name, amount, deposit_date, shift, payment_method, notes, status, input_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """, (final_rm, final_name, float(deposit_amount), str(deposit_date), dep_shift, payment_method, notes.strip(), current_user))
                
                conn.commit()
                conn.close()
                st.success(f"✓ Setoran deposit sebesar {format_rupiah(deposit_amount)} (Shift: {dep_shift}) berhasil disimpan untuk **{final_name}** oleh {current_user}!")
                st.session_state.deposit_reset_cnt += 1
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)