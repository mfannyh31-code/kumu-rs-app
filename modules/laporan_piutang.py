import streamlit as st
import pandas as pd
import io
from datetime import datetime
from db import get_db, format_rupiah, render_header

def format_angka(val):
    try: return f"{int(float(val)):,}".replace(",", ".")
    except: return "0"

def render_page():
    render_header("📊 Laporan & Rekapitulasi Piutang", "Analisis data tagihan piutang berdasarkan filter Harian, Bulanan, dan Tahunan dengan rincian unit layanan hirarki baru.")

    if st.button("⬅️ Kembali ke Menu Piutang"):
        st.session_state.current_menu = "piutang"
        st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # --- CSS KHUSUS TABEL LAPORAN PROFESIONAL ---
    st.markdown("""
        <style>
        .metric-report-card {
            background: #FFFFFF;
            padding: 16px;
            border-radius: 10px;
            border: 1px solid #CBD5E1;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .tbl-report-lux {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13.5px;
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            overflow: hidden;
        }
        .tbl-report-lux th {
            background: #028090;
            color: white;
            padding: 11px 12px;
            border: 1px solid #026b78;
            text-align: left;
            font-weight: 700;
        }
        .tbl-report-lux td {
            padding: 10px 12px;
            border: 1px solid #E2E8F0;
            color: #0F172A;
        }
        .tbl-report-lux tr:nth-child(even) {
            background-color: #F8FAFC;
        }
        .total-row-lux {
            font-weight: 800;
            background: #E2E8F0 !important;
            border-top: 2px solid #94A3B8;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- FILTER PERIODE LAPORAN ---
    st.markdown('<div style="background:#FFFFFF; padding:20px; border-radius:10px; border:1px solid #CBD5E1; margin-bottom:20px;">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
    with c1:
        tipe_laporan = st.selectbox("Jenis Periode Laporan", ["Harian", "Bulanan", "Tahunan"])
    
    months_dict = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04", 
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08", 
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    years_list = [str(y) for y in range(2024, 2032)]
    current_year_str = str(datetime.today().year)

    if tipe_laporan == "Harian":
        with c2:
            filter_val = st.date_input("Pilih Tanggal Piutang", datetime.today())
        date_mask = f"{str(filter_val)}%"
    elif tipe_laporan == "Bulanan":
        with c2:
            sel_month_name = st.selectbox("Pilih Bulan", list(months_dict.keys()), index=datetime.today().month - 1)
        with c3:
            sel_year_m = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0)
        m_num = months_dict[sel_month_name]
        date_mask = f"{sel_year_m}-{m_num}%"
    else:
        with c2:
            sel_year = st.selectbox("Pilih Tahun", years_list, index=years_list.index(current_year_str) if current_year_str in years_list else 0)
        date_mask = f"{sel_year}%"
    
    st.markdown('</div>', unsafe_allow_html=True)

    conn = get_db()
    # Query utama tabel receivables digabungkan dengan rincian item piutang (receivables_items)
    query_rep = """
        SELECT r.*, i.category_name as unit_layanan, i.action_name as jenis_tindakan, i.amount as item_amount, i.paid_status as item_status
        FROM receivables r
        LEFT JOIN receivables_items i ON r.id = i.debt_id
        WHERE r.due_date LIKE ?
        ORDER BY r.id DESC
    """
    df_all = pd.read_sql_query(query_rep, conn, params=[date_mask])
    conn.close()

    if not df_all.empty:
        # Menghitung metrik berdasarkan ID unik piutang agar tidak terduplikasi akibat join item
        df_unique_receivables = df_all.drop_duplicates(subset=['id'])
        total_piutang_all = df_unique_receivables['total_bill'].sum()
        total_dibayar = df_unique_receivables['paid_amount'].sum()
        total_sisa = df_unique_receivables['remaining_debt'].sum()
        
        # Ringkasan Kartu Metrik
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-report-card'><div style='font-size:12px; color:#64748B;'>Total Seluruh Tagihan</div><div style='font-size:18px; font-weight:800; color:#0F172A; margin-top:4px;'>{format_rupiah(total_piutang_all)}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-report-card'><div style='font-size:12px; color:#64748B;'>Total Sudah Dibayar</div><div style='font-size:18px; font-weight:800; color:#10B981; margin-top:4px;'>{format_rupiah(total_dibayar)}</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-report-card'><div style='font-size:12px; color:#64748B;'>Sisa Piutang (Belum Lunas)</div><div style='font-size:18px; font-weight:800; color:#EF4444; margin-top:4px;'>{format_rupiah(total_sisa)}</div></div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filter Status di dalam tabel
        col_f1, col_f2 = st.columns([1.5, 3])
        with col_f1:
            f_stat = st.selectbox("Filter Status Piutang", ["Semua", "Belum Lunas", "Lunas"])
        
        if f_stat != "Semua":
            filtered_ids = df_unique_receivables[df_unique_receivables['status'] == f_stat]['id'].tolist()
            df_filtered = df_all[df_all['id'].isin(filtered_ids)]
            df_unique_filtered = df_unique_receivables[df_unique_receivables['status'] == f_stat]
        else:
            df_filtered = df_all
            df_unique_filtered = df_unique_receivables

        st.markdown("##### 📋 Tabel Rincian Data Piutang & Unit Layanan Periode Ini")

        if not df_filtered.empty:
            html_table = "<table class='tbl-report-lux'>"
            html_table += "<tr>"
            html_table += "<th>No</th>"
            html_table += "<th>No. Ref / RM</th>"
            html_table += "<th>Nama Pasien</th>"
            html_table += "<th>Unit & Tindakan Layanan</th>"
            html_table += "<th style='text-align:right;'>Total Tagihan (Rp)</th>"
            html_table += "<th style='text-align:right;'>Sudah Dibayar (Rp)</th>"
            html_table += "<th style='text-align:right;'>Sisa Piutang (Rp)</th>"
            html_table += "<th style='text-align:center;'>Status</th>"
            html_table += "<th style='text-align:center;'>Jatuh Tempo</th>"
            html_table += "<th>Kasir / User</th>"
            html_table += "</tr>"

            sub_tot_bill = 0.0
            sub_paid_amt = 0.0
            sub_rem_debt = 0.0

            # Kelompokkan berdasarkan ID piutang untuk menampilkan rincian item dengan rapi
            grouped = df_filtered.groupby('id')
            row_no = 1

            for debt_id, group in grouped:
                first_row = group.iloc[0]
                sub_tot_bill += float(first_row['total_bill'] or 0)
                sub_paid_amt += float(first_row['paid_amount'] or 0)
                sub_rem_debt += float(first_row['remaining_debt'] or 0)

                status_badge = "<span style='background:#EF4444; color:#fff; font-size:10px; padding:2px 8px; border-radius:4px; font-weight:700;'>BELUM LUNAS</span>" if first_row['status'] == 'Belum Lunas' else "<span style='background:#10B981; color:#fff; font-size:10px; padding:2px 8px; border-radius:4px; font-weight:700;'>LUNAS</span>"

                # Gabungkan rincian item layanan/tindakan dalam satu sel tabel
                items_str_list = []
                for _, itm in group.iterrows():
                    if pd.notna(itm['jenis_tindakan']):
                        itm_badge = f"<span style='color:#10B981; font-size:10px;'>({itm['item_status']})</span>" if itm['item_status'] == 'Lunas' else f"<span style='color:#EF4444; font-size:10px;'>({itm['item_status']})</span>"
                        items_str_list.append(f"• <b>[{itm['unit_layanan']}]</b> {itm['jenis_tindakan']} - {format_angka(itm['item_amount'])} {itm_badge}")
                
                items_html = "<br>".join(items_str_list) if items_str_list else "-"

                html_table += f"<tr>"
                html_table += f"<td>{row_no}</td>"
                html_table += f"<td><b>#{first_row['receipt_no']}</b><br><span style='font-size:11.5px; color:#64748B;'>RM: {first_row['patient_id'] or '-'}</span></td>"
                html_table += f"<td><b>{first_row['patient_name']}</b></td>"
                html_table += f"<td style='font-size:12px;'>{items_html}</td>"
                html_table += f"<td style='text-align:right;'>{format_angka(first_row['total_bill'])}</td>"
                html_table += f"<td style='text-align:right; color:#10B981;'>{format_angka(first_row['paid_amount'])}</td>"
                html_table += f"<td style='text-align:right; color:#EF4444; font-weight:700;'>{format_angka(first_row['remaining_debt'])}</td>"
                html_table += f"<td style='text-align:center;'>{status_badge}</td>"
                html_table += f"<td style='text-align:center;'>{first_row['due_date']}</td>"
                html_table += f"<td>{str(first_row['input_by']).upper()}</td>"
                html_table += f"</tr>"
                row_no += 1

            # Baris Total Keseluruhan di Bawah Tabel
            html_table += f"<tr class='total-row-lux'>"
            html_table += f"<td colspan='4' style='text-align:right;'>TOTAL KESELURUHAN:</td>"
            html_table += f"<td style='text-align:right;'>{format_angka(sub_tot_bill)}</td>"
            html_table += f"<td style='text-align:right; color:#10B981;'>{format_angka(sub_paid_amt)}</td>"
            html_table += f"<td style='text-align:right; color:#EF4444;'>{format_angka(sub_rem_debt)}</td>"
            html_table += f"<td colspan='3'></td>"
            html_table += f"</tr>"

            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("Tidak ada data piutang dengan status filter tersebut.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Tombol Unduh Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_unique_filtered.to_excel(writer, sheet_name='Laporan Piutang', index=False)
            
        st.download_button(
            label="📥 Unduh Laporan Piutang Lengkap (Excel)",
            data=output.getvalue(),
            file_name=f"Laporan_Piutang_{tipe_laporan}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Tidak ada data piutang yang ditemukan pada periode tersebut.")