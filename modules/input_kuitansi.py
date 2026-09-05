import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header
from sqlalchemy import text

def render_page():
    render_header("💳 Input Kuitansi Kasir", "Entri multi-tindakan per kuitansi dengan pemilihan hierarki layanan (Layanan ➔ Unit ➔ Tindakan)")

    # Inisialisasi Counter Reset Form
    if 'form_reset_counter' not in st.session_state:
        st.session_state.form_reset_counter = 0
    cnt = st.session_state.form_reset_counter

    if 'rows_list' not in st.session_state:
        st.session_state.rows_list = [1, 2]
    if 'next_row_id' not in st.session_state:
        st.session_state.next_row_id = 3

    # Ambil data master hirarki dari database
    with get_db() as conn:
        service_cats_df = pd.read_sql_query(text("SELECT id, name FROM service_categories ORDER BY name ASC"), conn)
        scats_list = ["Select"] + service_cats_df['name'].tolist() if not service_cats_df.empty else ["Select"]

        categories_df = pd.read_sql_query(text("SELECT id, service_category_id, name FROM categories ORDER BY name ASC"), conn)
        actions_df = pd.read_sql_query(text("SELECT id, category_id, name, price FROM actions ORDER BY name ASC"), conn)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    # 1. Informasi Dokumen Kuitansi
    st.markdown("##### 📄 Informasi Dokumen Kuitansi")
    h1, h2, h3 = st.columns([1.5, 1.5, 1.5])
    with h1:
        no_urut_kertas = st.text_input("No. Urut Kertas / Kuitansi *", placeholder="Contoh: 308678", key=f"main_rcpt_{cnt}")
    with h2:
        tgl_kuitansi = st.date_input("Tanggal Kuitansi *", value=datetime.today(), key=f"main_date_{cnt}")
    with h3:
        shift_val = st.selectbox("Shift *", ["Pagi", "Sore", "Malam"], key=f"main_shift_{cnt}")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 2. Rincian Tindakan & Layanan (Berdasarkan Hierarki Baru)
    st.markdown("##### 💉 Rincian Tindakan & Layanan")

    gh1, gh2 = st.columns([5, 1.2])
    with gh1:
        st.caption("Pilih Kategori Layanan Utama, Unit, dan Tindakan. Tarif terisi otomatis.")
    with gh2:
        if st.button("➕ Tambah Baris", use_container_width=True, key=f"add_row_{cnt}"):
            st.session_state.rows_list.append(st.session_state.next_row_id)
            st.session_state.next_row_id += 1
            st.rerun()

    items_data = []
    grand_total_actions = 0.0

    for row_id in list(st.session_state.rows_list):
        st.markdown("<div style='background:#F8FAFC; border:1.5px solid #CBD5E1; padding:14px 18px; border-radius:10px; margin-bottom:12px;'>", unsafe_allow_html=True)

        # Baris Input Atas: No. Bukti, Layanan Utama, Unit, Tindakan, Tombol Hapus
        f_top1, f_top2, f_top3, f_top4, f_top5 = st.columns([1.1, 1.8, 1.8, 2.3, 0.4])
        
        with f_top1:
            bk_val = st.text_input("No. Bukti", placeholder="BK-01", key=f"bk_{row_id}_{cnt}")
        
        with f_top2:
            scat_val = st.selectbox("Kategori Layanan", scats_list, key=f"scat_{row_id}_{cnt}")

        # Filter Unit berdasarkan Kategori Layanan yang dipilih
        sub_units = ["Select"]
        selected_scat_id = None
        if scat_val != "Select" and not service_cats_df.empty:
            match_scat = service_cats_df[service_cats_df['name'] == scat_val]
            if not match_scat.empty:
                selected_scat_id = match_scat['id'].values[0]
                filtered_cats = categories_df[categories_df['service_category_id'] == selected_scat_id]
                sub_units += filtered_cats['name'].tolist()

        with f_top3:
            cat_val = st.selectbox("Unit Layanan", sub_units, key=f"cat_{row_id}_{cnt}")

        # Filter Tindakan berdasarkan Unit yang dipilih
        sub_acts = ["Select"]
        selected_cat_id = None
        if cat_val != "Select" and not categories_df.empty:
            match_cat = categories_df[categories_df['name'] == cat_val]
            if not match_cat.empty:
                selected_cat_id = match_cat['id'].values[0]
                filtered_acts = actions_df[actions_df['category_id'] == selected_cat_id]
                sub_acts += filtered_acts['name'].tolist()

        with f_top4:
            act_val = st.selectbox("Jenis Tindakan", sub_acts, key=f"act_{row_id}_{cnt}")

        with f_top5:
            st.write("")
            st.write("")
            if st.button("❌", key=f"del_{row_id}_{cnt}", help="Hapus Baris Ini"):
                if len(st.session_state.rows_list) > 1:
                    st.session_state.rows_list.remove(row_id)
                    st.rerun()

        default_price = 0.0
        if act_val != "Select" and selected_cat_id is not None:
            match_act = actions_df[(actions_df['category_id'] == selected_cat_id) & (actions_df['name'] == act_val)]
            if not match_act.empty:
                default_price = float(match_act['price'].values[0])

        price_state_key = f"price_{row_id}_{cnt}"
        prev_act_key = f"prev_act_{row_id}_{cnt}"

        if prev_act_key not in st.session_state or st.session_state[prev_act_key] != act_val:
            st.session_state[prev_act_key] = act_val
            st.session_state[price_state_key] = default_price

        f_btm1, f_btm2, f_btm3, f_btm4 = st.columns([1.5, 1, 1.5, 1.5])

        with f_btm1:
            price_val = st.number_input("Tarif Satuan (Rp) *", min_value=0.0, value=float(st.session_state.get(price_state_key, default_price)), step=10000.0, format="%.0f", key=price_state_key)
        with f_btm2:
            qty_i = st.number_input("Jumlah (Qty)", min_value=1, value=1, step=1, key=f"qty_{row_id}_{cnt}")
        with f_btm3:
            disc_i = st.number_input("Pengurangan (Rp)", min_value=0.0, value=0.0, step=5000.0, format="%.0f", key=f"disc_{row_id}_{cnt}")

        subtot_i = (price_val * qty_i) - disc_i if act_val != "Select" else 0.0
        grand_total_actions += subtot_i

        with f_btm4:
            st.write("")
            st.markdown(f"""
                <div style='margin-top:2px;'>
                    <div style='font-size:12px; color:#64748B; font-weight:600;'>Subtotal:</div>
                    <div style='color:#028090; font-size:17px; font-weight:800;'>{format_rupiah(subtot_i)}</div>
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

    # Grand Total Semua Tindakan
    st.markdown(f"""
        <div style="text-align: right; margin: 15px 0; font-size: 16px; font-weight: 800; color: #0F172A;">
            Grand Total Semua Tindakan: <span style="font-size: 22px; font-weight: 800; color: #028090;">{format_rupiah(grand_total_actions)}</span>
        </div>
    """, unsafe_allow_html=True)

    # 3. Sub-card: Pencatatan Kasir & Split Pembayaran
    st.markdown('<div class="sub-card">', unsafe_allow_html=True)
    st.markdown("#### **Pencatatan Kasir & Split Pembayaran (Live Auto-Balance)**")

    use_deposit = st.checkbox("Gunakan Uang Muka / Deposit Pasien Rawat Inap", key=f"chk_dep_{cnt}")
    patient_rm = ""
    dep_avail = 0.0
    selected_dep = "-- Pilih Pasien --"
    dep_mapping = {}

    if use_deposit:
        with get_db() as conn:
            try:
                active_deps_df = pd.read_sql_query(text("""
                    SELECT patient_id, patient_name, SUM(amount) as total_amount 
                    FROM deposits 
                    GROUP BY patient_id, patient_name
                """), conn)
                if not active_deps_df.empty:
                    active_deps_df = active_deps_df[active_deps_df['total_amount'] > 0]
            except Exception:
                active_deps_df = pd.DataFrame()

        if not active_deps_df.empty:
            dep_options = ["-- Pilih Pasien --"]
            for _, r in active_deps_df.iterrows():
                rm = str(r['patient_id']).strip()
                name = str(r['patient_name']).strip()
                amt = float(r['total_amount'])
                label = f"{rm} - {name} (Saldo: {format_rupiah(amt)})"
                dep_options.append(label)
                dep_mapping[label] = {'rm': rm, 'name': name, 'amount': amt}
            
            selected_dep = st.selectbox("Pilih Pasien dengan Saldo Uang Muka", dep_options, key=f"in_rm_sel_{cnt}")
            
            if selected_dep != "-- Pilih Pasien --":
                patient_rm = dep_mapping[selected_dep]['rm']
                dep_avail = dep_mapping[selected_dep]['amount']
                st.info(f"👤 **{dep_mapping[selected_dep]['name']}** | 💰 Saldo Uang Muka: **{format_rupiah(dep_avail)}**")
                st.markdown("<div style='font-size:12.5px; color:#64748B; margin-top:-10px;'>ℹ️ Masukkan nominal yang ingin digunakan pada kolom <b>Pengakuan Bendahara</b> di bawah.</div>", unsafe_allow_html=True)
        else:
            st.warning("Saat ini tidak ada data pasien dengan saldo uang muka aktif.")

    sisa_tagihan = grand_total_actions

    st.markdown(f"""
        <div style="margin: 8px 0 16px 0; font-size: 15px; font-weight: 800; color: #0F172A;">
            Total Tagihan Dibayar: <span style="color: #028090; font-size: 20px; font-weight: 800;">{format_rupiah(sisa_tagihan)}</span>
        </div>
    """, unsafe_allow_html=True)

    def refresh_balance():
        pass

    col_p_left, col_p_right = st.columns(2)

    with col_p_right:
        st.markdown("**Metode Non-Tunai / Digital:**")
        pay_transfer = st.number_input("Transfer Bank (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_tf_{cnt}", on_change=refresh_balance)
        pay_va = st.number_input("Virtual Account (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_va_{cnt}", on_change=refresh_balance)
        pay_qris = st.number_input("QRIS (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_qris_{cnt}", on_change=refresh_balance)
        pay_edc = st.number_input("EDC Kartu (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_edc_{cnt}", on_change=refresh_balance)

    non_tunai_total = pay_transfer + pay_va + pay_qris + pay_edc

    with col_p_left:
        st.markdown("**Metode Tunai & Penyesuaian:**")
        pay_pengembalian = st.number_input("Pengembalian / Refund (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_kembali_{cnt}", on_change=refresh_balance)
        pay_pengakuan = st.number_input("Pengakuan Bendahara / Potong Uang Muka (Rp)", min_value=0.0, value=0.0, step=10000.0, format="%.0f", key=f"in_pengakuan_{cnt}", on_change=refresh_balance)

        auto_tunai = max(0.0, sisa_tagihan - non_tunai_total + pay_pengembalian - pay_pengakuan)

        tunai_key = f"in_tunai_{cnt}"

        if tunai_key not in st.session_state:
            st.session_state[tunai_key] = float(auto_tunai)
        else:
            st.session_state[tunai_key] = float(auto_tunai)

        pay_tunai = st.number_input(
            "Uang Tunai Fisik (Rp - Auto Balance)", 
            min_value=0.0, 
            step=10000.0, 
            format="%.0f", 
            key=tunai_key
        )

    total_terbayar = pay_tunai + non_tunai_total + pay_pengakuan - pay_pengembalian

    if abs(total_terbayar - sisa_tagihan) > 0.01:
        st.warning(f"⚠️ Total pembayaran ({format_rupiah(total_terbayar)}) belum pas dengan tagihan ({format_rupiah(sisa_tagihan)})")
    else:
        st.success(f"✓ Split pembayaran seimbang dan pas ({format_rupiah(total_terbayar)})")

    st.markdown('</div>', unsafe_allow_html=True)

    active_methods = []
    if pay_tunai > 0: active_methods.append(f"TUNAI ({format_rupiah(pay_tunai)})")
    if pay_transfer > 0: active_methods.append(f"TRANSFER ({format_rupiah(pay_transfer)})")
    if pay_edc > 0: active_methods.append(f"EDC ({format_rupiah(pay_edc)})")
    if pay_qris > 0: active_methods.append(f"QRIS ({format_rupiah(pay_qris)})")
    if pay_va > 0: active_methods.append(f"VA ({format_rupiah(pay_va)})")
    if pay_pengakuan > 0:
        if use_deposit and patient_rm:
            active_methods.append(f"UANG MUKA ({format_rupiah(pay_pengakuan)})")
        else:
            active_methods.append(f"PENGAKUAN BENDAHARA ({format_rupiah(pay_pengakuan)})")

    summary_method_str = ", ".join(active_methods) if active_methods else "TUNAI"

    st.markdown("<br>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("🔄 Reset Form", use_container_width=True, key=f"btn_reset_{cnt}"):
            st.session_state.rows_list = [1, 2]
            st.session_state.form_reset_counter += 1
            st.rerun()
    with b_col2:
        if st.button("💾 Simpan Kuitansi & Input Baru", use_container_width=True, key=f"btn_save_{cnt}"):
            
            deposit_claimed = pay_pengakuan if (use_deposit and patient_rm) else 0.0

            if not no_urut_kertas.strip():
                st.error("No. Urut Kertas / Kuitansi wajib diisi.")
            elif not items_data:
                st.error("Pilih minimal satu tindakan pada baris input di atas.")
            elif use_deposit and patient_rm and deposit_claimed > dep_avail:
                st.error(f"Gagal: Nominal yang diisikan ke Pengakuan Bendahara ({format_rupiah(pay_pengakuan)}) melebihi saldo Uang Muka yang tersedia ({format_rupiah(dep_avail)}).")
            else:
                try:
                    with get_db() as conn:
                        with conn.begin():
                            conn.execute(text("""
                                INSERT INTO transactions 
                                (receipt_no, receipt_date, input_date, shift, cashier_username, 
                                 total_actions_amount, final_amount, payment_method,
                                 pay_tunai, pay_transfer, pay_edc, pay_qris, pay_va, pay_deposit, pay_pengembalian, pay_pengakuan_bendahara)
                                VALUES (:rno, :rdate, :idate, :shf, :cuser, :totact, :finamt, :pmeth, :ptun, :ptf, :pedc, :pqris, :pva, :pdep, :pkemb, :ppeng)
                            """), {
                                "rno": no_urut_kertas.strip(),
                                "rdate": str(tgl_kuitansi),
                                "idate": str(datetime.today().date()),
                                "shf": shift_val,
                                "cuser": st.session_state.get('user', 'admin'),
                                "totact": grand_total_actions,
                                "finamt": sisa_tagihan,
                                "pmeth": summary_method_str,
                                "ptun": pay_tunai,
                                "ptf": pay_transfer,
                                "pedc": pay_edc,
                                "pqris": pay_qris,
                                "pva": pay_va,
                                "pdep": deposit_claimed,
                                "pkemb": pay_pengembalian,
                                "ppeng": pay_pengakuan
                            })

                            for itm in items_data:
                                conn.execute(text("""
                                    INSERT INTO transaction_items 
                                    (receipt_no, book_no, category_name, action_name, price, qty, discount, subtotal)
                                    VALUES (:rno, :bk, :cname, :aname, :prc, :qty, :disc, :sub)
                                """), {
                                    "rno": no_urut_kertas.strip(),
                                    "bk": itm['book_no'],
                                    "cname": itm['category_name'],
                                    "aname": itm['action_name'],
                                    "prc": itm['price'],
                                    "qty": itm['qty'],
                                    "disc": itm['discount'],
                                    "sub": itm['subtotal']
                                })

                            if deposit_claimed > 0 and patient_rm:
                                conn.execute(text("""
                                    INSERT INTO deposits (patient_id, patient_name, amount, deposit_date, shift, payment_method, notes, status, input_by)
                                    VALUES (:pid, :pname, :amt, :ddate, :shf, :pmeth, :notes, 'USED', :usr)
                                """), {
                                    "pid": str(patient_rm).strip(),
                                    "pname": str(dep_mapping[selected_dep]['name']).strip(),
                                    "amt": -float(deposit_claimed),
                                    "ddate": str(tgl_kuitansi),
                                    "shf": shift_val,
                                    "pmeth": 'Kuitansi',
                                    "notes": f"Pemotongan Uang Muka Kuitansi #{no_urut_kertas.strip()}",
                                    "usr": str(st.session_state.get('user', 'admin')).upper()
                                })

                    st.success(f"✓ Kuitansi #{no_urut_kertas} berhasil disimpan dan saldo deposit berhasil terpotong!")

                    st.session_state.rows_list = [1, 2]
                    st.session_state.form_reset_counter += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan kuitansi. Kemungkinan No. Urut Kertas sudah terdaftar. (Error: {e})")

    st.markdown('</div>', unsafe_allow_html=True)