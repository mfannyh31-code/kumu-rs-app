import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_db, format_rupiah, render_header, get_base64_image

def render_page():
    # --- CSS FINISHING & PERBAIKAN TATA LETAK DASHBOARD ---
    st.markdown("""
        <style>
        .dash-banner {
            background: linear-gradient(135deg, #028090 0%, #005F73 100%);
            padding: 24px 28px;
            border-radius: 14px;
            color: white;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(2, 128, 144, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .dash-banner-left h1 {
            font-size: 22px;
            font-weight: 800;
            margin: 0;
            color: #FFFFFF;
            letter-spacing: 0.5px;
        }
        .dash-banner-left p {
            font-size: 13.5px;
            margin: 6px 0 0 0;
            color: #E2E8F0;
            font-weight: 500;
        }
        .dash-card { 
            background: #FFFFFF; 
            padding: 20px 16px; 
            border-radius: 12px; 
            border: 1px solid #CBD5E1; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.02); 
            text-align: center; 
            height: 100%;
        }
        .dash-card h3 { margin: 0; font-size: 12.5px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .dash-card p { margin: 10px 0 0 0; font-size: 20px; font-weight: 800; color: #0F172A; }
        
        .tbl-dash { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; background: #FFFFFF; border-radius: 8px; overflow: hidden; border: 1px solid #CBD5E1; }
        .tbl-dash th { background: #028090; color: #FFFFFF; padding: 10px 12px; border: 1px solid #026b78; text-align: left; font-weight: 700; }
        .tbl-dash td { padding: 9px 12px; border: 1px solid #E2E8F0; color: #334155; }
        .tbl-dash tr:nth-child(even) { background-color: #F8FAFC; }
        
        .insight-box {
            background-color: #F0FDF4;
            border-left: 5px solid #10B981;
            padding: 16px 20px;
            border-radius: 10px;
            margin-bottom: 24px;
            font-size: 13.5px;
            color: #166534;
            border-top: 1px solid #BBF7D0;
            border-right: 1px solid #BBF7D0;
            border-bottom: 1px solid #BBF7D0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01);
        }
        
        .section-title {
            font-size: 16px;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 12px;
            letter-spacing: 0.3px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Memuat logo lokal kimu.png menggunakan fungsi get_base64_image
    logo_base64 = get_base64_image("kimu.png")
    logo_markup = f'<img src="data:image/png;base64,{logo_base64}" width="70" style="background:white; padding:5px; border-radius:8px;" onerror="this.style.display=\'none\'">' if logo_base64 else ''

    # Banner Utama Dashboard dengan Identitas Instansi & Logo Lokal kimu.png
    st.markdown(f"""
        <div class="dash-banner">
            <div class="dash-banner-left">
                <h1>🏥 KIMU - RS JIWA DR. SOEHARTO HEERDJAN</h1>
                <p>Sistem Informasi Manajemen Keuangan, Kasir, dan Rekonsiliasi Terpadu</p>
            </div>
            <div>
                {logo_markup}
            </div>
        </div>
    """, unsafe_allow_html=True)

    today_str = datetime.today().strftime("%Y-%m-%d")
    current_hour = datetime.now().hour
    
    # Ucapan Dinamis Berdasarkan Waktu
    if current_hour < 11:
        salam = "Selamat Pagi"
    elif current_hour < 15:
        salam = "Selamat Siang"
    elif current_hour < 18:
        salam = "Selamat Sore"
    else:
        salam = "Selamat Malam"

    active_user = str(st.session_state.get('user', 'OPERATOR')).upper()
    active_role = str(st.session_state.get('role', 'Kasir')).strip()
    
    st.markdown(f"👋 **{salam}, {active_user} ({active_role})!** Berikut adalah ringkasan performa dan pemantauan keuangan Anda hari ini.")
    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    conn = get_db()

    # --- AMBIL DATA METRIK HARI INI (DIFILTER BERDASARKAN ROLE) ---
    try:
        if active_role == "Kasir":
            # Kasir hanya melihat data miliknya sendiri
            q_rev = """
                SELECT SUM(i.subtotal) 
                FROM transaction_items i 
                JOIN transactions t ON i.receipt_no = t.receipt_no 
                WHERE t.receipt_date LIKE ? AND UPPER(TRIM(t.cashier_username)) = UPPER(TRIM(?))
            """
            res_rev = pd.read_sql_query(q_rev, conn, params=[f"{today_str}%", active_user])
            total_pendapatan_hari_ini = float(res_rev.iloc[0, 0] or 0.0)

            q_piu = "SELECT SUM(remaining_debt) FROM receivables WHERE status = 'Belum Lunas'"
            res_piu = pd.read_sql_query(q_piu, conn)
            total_sisa_piutang = float(res_piu.iloc[0, 0] or 0.0)

            q_tx_count = "SELECT COUNT(*) FROM transactions WHERE receipt_date LIKE ? AND UPPER(TRIM(cashier_username)) = UPPER(TRIM(?))"
            res_tx_count = pd.read_sql_query(q_tx_count, conn, params=[f"{today_str}%", active_user])
            total_transaksi_count = int(res_tx_count.iloc[0, 0] or 0)

            q_kanal = """
                SELECT SUM(pay_tunai) as tunai, SUM(pay_transfer) as transfer, SUM(pay_edc) as edc, SUM(pay_qris) as qris, SUM(pay_va) as va 
                FROM transactions 
                WHERE receipt_date LIKE ? AND UPPER(TRIM(cashier_username)) = UPPER(TRIM(?))
            """
            df_kanal = pd.read_sql_query(q_kanal, conn, params=[f"{today_str}%", active_user])
            
            df_latest_tx = pd.read_sql_query(
                "SELECT receipt_no, receipt_date, cashier_username, final_amount, payment_method FROM transactions WHERE receipt_date LIKE ? AND UPPER(TRIM(cashier_username)) = UPPER(TRIM(?)) ORDER BY id DESC LIMIT 5", 
                conn, params=[f"{today_str}%", active_user]
            )
        else:
            # Bendahara & Super Admin melihat keseluruhan data instansi
            q_rev = "SELECT SUM(subtotal) FROM transaction_items i JOIN transactions t ON i.receipt_no = t.receipt_no WHERE t.receipt_date LIKE ?"
            res_rev = pd.read_sql_query(q_rev, conn, params=[f"{today_str}%"])
            total_pendapatan_hari_ini = float(res_rev.iloc[0, 0] or 0.0)

            q_piu = "SELECT SUM(remaining_debt) FROM receivables WHERE status = 'Belum Lunas'"
            res_piu = pd.read_sql_query(q_piu, conn)
            total_sisa_piutang = float(res_piu.iloc[0, 0] or 0.0)

            q_tx_count = "SELECT COUNT(*) FROM transactions WHERE receipt_date LIKE ?"
            res_tx_count = pd.read_sql_query(q_tx_count, conn, params=[f"{today_str}%"])
            total_transaksi_count = int(res_tx_count.iloc[0, 0] or 0)

            q_kanal = "SELECT SUM(pay_tunai) as tunai, SUM(pay_transfer) as transfer, SUM(pay_edc) as edc, SUM(pay_qris) as qris, SUM(pay_va) as va FROM transactions WHERE receipt_date LIKE ?"
            df_kanal = pd.read_sql_query(q_kanal, conn, params=[f"{today_str}%"])
            
            df_latest_tx = pd.read_sql_query("SELECT receipt_no, receipt_date, cashier_username, final_amount, payment_method FROM transactions WHERE receipt_date LIKE ? ORDER BY id DESC LIMIT 5", conn, params=[f"{today_str}%"])

        t_tunai = float(df_kanal.iloc[0]['tunai'] or 0) if not df_kanal.empty else 0
        t_transfer = float(df_kanal.iloc[0]['transfer'] or 0) if not df_kanal.empty else 0
        t_edc = float(df_kanal.iloc[0]['edc'] or 0) if not df_kanal.empty else 0
        t_qris = float(df_kanal.iloc[0]['qris'] or 0) if not df_kanal.empty else 0
        t_va = float(df_kanal.iloc[0]['va'] or 0) if not df_kanal.empty else 0
        
        grand_total_kanal = t_tunai + t_transfer + t_edc + t_qris + t_va
    except:
        total_pendapatan_hari_ini = 0.0
        total_sisa_piutang = 0.0
        total_transaksi_count = 0
        t_tunai, t_transfer, t_edc, t_qris, t_va, grand_total_kanal = 0, 0, 0, 0, 0, 0
        df_latest_tx = pd.DataFrame()

    conn.close()

    # --- KARTU METRIK UTAMA (KPI) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        label_rev = "Pendapatan Anda Hari Ini" if active_role == "Kasir" else "Pendapatan Netto Hari Ini"
        st.markdown(f"<div class='dash-card'><h3>{label_rev}</h3><p style='color:#028090;'>{format_rupiah(total_pendapatan_hari_ini)}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='dash-card'><h3>Total Sisa Piutang</h3><p style='color:#EF4444;'>{format_rupiah(total_sisa_piutang)}</p></div>", unsafe_allow_html=True)
    with c3:
        label_masuk = "Pembayaran Masuk Anda" if active_role == "Kasir" else "Total Pembayaran Masuk"
        st.markdown(f"<div class='dash-card'><h3>{label_masuk}</h3><p style='color:#10B981;'>{format_rupiah(grand_total_kanal)}</p></div>", unsafe_allow_html=True)
    with c4:
        label_nota = "Nota Anda Hari Ini" if active_role == "Kasir" else "Jumlah Kuitansi Hari Ini"
        st.markdown(f"<div class='dash-card'><h3>{label_nota}</h3><p style='color:#3B82F6;'>{total_transaksi_count:,} Nota</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- FITUR SMART INSIGHTS / ANALISIS OTOMATIS ---
    if total_pendapatan_hari_ini > 0:
        insight_text = f"Berdasarkan input Anda hari ini, tercatat total <b>{total_transaksi_count} transaksi</b> dengan perolehan sebesar <b>{format_rupiah(grand_total_kanal)}</b>." if active_role == "Kasir" else f"Sistem mencatat aktivitas instansi berjalan lancar dengan total <b>{total_transaksi_count} transaksi</b> dan perolehan <b>{format_rupiah(grand_total_kanal)}</b>."
        st.markdown(f"""
            <div class="insight-box">
                💡 <b>Smart Financial Insight:</b> {insight_text} Tetap teliti dalam menginput data kuitansi dan metode pembayaran.
            </div>
        """, unsafe_allow_html=True)

    # --- PINTASAN MENU CEPAT (QUICK ACTIONS - DISESUAIKAN DENGAN ROLE) ---
    st.markdown("<div class='section-title'>⚡ Pintasan Menu Cepat</div>", unsafe_allow_html=True)
    
    if active_role in ["Bendahara", "Super Admin"]:
        qc1, qc2, qc3, qc4 = st.columns(4)
        with qc1:
            if st.button("📑 Laporan Kasir", use_container_width=True):
                st.session_state.current_menu = "laporan"
                st.rerun()
        with qc2:
            if st.button("💳 Manajemen Piutang", use_container_width=True):
                st.session_state.current_menu = "piutang"
                st.rerun()
        with qc3:
            if st.button("📑 Rekon Bendahara", use_container_width=True):
                st.session_state.current_menu = "rekon"
                st.rerun()
        with qc4:
            if st.button("➕ Daftar Kuitansi", use_container_width=True):
                st.session_state.current_menu = "daftar_kuitansi"
                st.rerun()
    else:
        # Tampilan pintasan untuk Kasir (tanpa tombol rekon bendahara)
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("📑 Laporan Kasir Saya", use_container_width=True):
                st.session_state.current_menu = "laporan"
                st.rerun()
        with qc2:
            if st.button("💳 Manajemen Piutang", use_container_width=True):
                st.session_state.current_menu = "piutang"
                st.rerun()
        with qc3:
            if st.button("➕ Daftar Kuitansi", use_container_width=True):
                st.session_state.current_menu = "daftar_kuitansi"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRAFIK & TABEL TRANSAKSI TERBARU ---
    col_left, col_right = st.columns([1.2, 1.8])

    with col_left:
        title_chart = "💳 Kanal Pembayaran Anda" if active_role == "Kasir" else "💳 Komposisi Kanal Pembayaran"
        st.markdown(f"<div class='section-title'>{title_chart}</div>", unsafe_allow_html=True)
        df_chart_kanal = pd.DataFrame({
            "Kanal": ["Tunai", "Transfer", "EDC", "QRIS", "VA"],
            "Nominal": [t_tunai, t_transfer, t_edc, t_qris, t_va]
        }).set_index("Kanal")
        st.bar_chart(df_chart_kanal)

    with col_right:
        title_table = "📝 Transaksi Kuitansi Anda Terbaru" if active_role == "Kasir" else "📝 Transaksi Kuitansi Terbaru"
        st.markdown(f"<div class='section-title'>{title_table}</div>", unsafe_allow_html=True)
        if not df_latest_tx.empty:
            html_tx = "<table class='tbl-dash'>"
            html_tx += "<tr><th>No. Kertas</th><th>Waktu</th><th>Kasir</th><th>Metode</th><th style='text-align:right;'>Nominal (Rp)</th></tr>"
            for _, row in df_latest_tx.iterrows():
                html_tx += f"<tr><td><b>#{row['receipt_no']}</b></td><td>{str(row['receipt_date'])[11:16]}</td><td>{str(row['cashier_username']).upper()}</td><td>{row['payment_method']}</td><td style='text-align:right; font-weight:700;'>{format_rupiah(row['final_amount'])}</td></tr>"
            html_tx += "</table>"
            st.markdown(html_tx, unsafe_allow_html=True)
        else:
            msg_empty = "Belum ada transaksi yang Anda input pada hari ini." if active_role == "Kasir" else "Belum ada transaksi tercatat pada hari ini."
            st.info(msg_empty)