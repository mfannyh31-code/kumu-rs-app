import streamlit as st
import os
from db import init_db, get_base64_image, get_db
from sqlalchemy import text

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="KEUANGAN KIMU - RS Soeharto Heerdjan",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi Database
init_db()

# --- CSS TEMA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    p, h1, h2, h3, h4, h5, h6, label, input, select, textarea, .stMarkdown {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    div[data-testid="InputInstructions"] { display: none !important; }
    .stApp { background-color: #F1F5F9 !important; }
    
    div[data-testid="stWidgetLabel"] label, div[data-testid="stWidgetLabel"] p,
    .stTextInput label, .stNumberInput label, .stDateInput label, .stSelectbox label {
        color: #000000 !important; font-size: 14px !important; font-weight: 800 !important;
        margin-bottom: 4px !important; text-align: left !important;
    }

    .stTextInput input, .stNumberInput input {
        background-color: #FFFFFF !important; border: 2px solid #94A3B8 !important; border-radius: 10px !important;
        color: #000000 !important; font-size: 14.5px !important; font-weight: 700 !important; padding: 10px 14px !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #028090 0%, #00A896 100%) !important;
        color: #FFFFFF !important; border-radius: 10px !important; border: none !important;
        padding: 12px 20px !important; font-weight: 800 !important; font-size: 15px !important;
        box-shadow: 0 4px 14px rgba(0, 168, 150, 0.3) !important; margin-top: 10px !important;
    }

    .login-container-card {
        background: #FFFFFF !important; padding: 36px 32px; border-radius: 20px;
        border: 2px solid #CBD5E1; box-shadow: 0 20px 45px rgba(15, 23, 42, 0.1);
        max-width: 440px; margin: 20px auto 0 auto;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important; border-right: 2px solid #CBD5E1;
    }
    
    .profile-card-lux {
        background: linear-gradient(135deg, #0F172A 0%, #028090 100%);
        padding: 18px 14px; border-radius: 14px; text-align: center; color: white;
        margin-bottom: 16px; box-shadow: 0 4px 12px rgba(2, 128, 144, 0.2); border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .profile-avatar-lux {
        width: 64px; height: 64px; border-radius: 50%; border: 3px solid #FFFFFF;
        object-fit: cover; margin: 0 auto 8px auto; box-shadow: 0 2px 8px rgba(0,0,0,0.2); background: #FFFFFF;
    }
    
    .sidebar-divider { height: 2px; background: #CBD5E1; margin: 14px 0; }
    .sidebar-logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Import Modul-modul Sistem
from modules import dashboard
from modules import daftar_kuitansi
from modules import input_kuitansi
from modules import input_deposit
from modules import daftar_deposit
from modules import laporan_kasir
from modules import rekon_otomatis
from modules import master_data
from modules import pengembalian_transaksi
from modules import input_pengembalian
from modules import pengaturan_user
from modules import piutang
from modules import input_piutang
from modules import laporan_piutang

if 'user' not in st.session_state: st.session_state.user = None
if 'role' not in st.session_state: st.session_state.role = None
if 'current_menu' not in st.session_state: st.session_state.current_menu = "dashboard"

# =========================================================
# HALAMAN LOGIN
# =========================================================
if not st.session_state.user:
    col_l1, col_l2, col_l3 = st.columns([1, 1.3, 1])
    with col_l2:
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        logo_base64 = get_base64_image("logo_rs.png")
        logo_markup = f'<img src="data:image/png;base64,{logo_base64}" style="max-height: 90px; width: auto; margin-bottom: 12px;">' if logo_base64 else '<div style="font-size:42px; margin-bottom:8px;">🏥</div>'
        
        st.markdown(f"""
            <div class="login-container-card">
                <div style="text-align: center;">{logo_markup}</div>
                <div style="text-align: center; font-size: 24px; font-weight: 800; color: #000000; margin-top: 4px;">KEUANGAN KIMU</div>
                <div style="text-align: center; font-size: 14.5px; color: #475569; font-weight: 700; margin-bottom: 24px;">RS Soeharto Heerdjan</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_login_kimu"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk ke Sistem ➜", use_container_width=True):
                with get_db() as conn_log:
                    logged_in = conn_log.execute(
                        text("SELECT * FROM users WHERE username = :un AND password = :pw"), 
                        {"un": login_user.strip(), "pw": login_pass.strip()}
                    ).mappings().fetchone()

                if logged_in:
                    st.session_state.user = login_user
                    st.session_state.role = logged_in['role']
                    st.session_state.current_menu = "dashboard"
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.stop()

# =========================================================
# SIDEBAR DENGAN KONTROL AKSES MENU BERDASARKAN ROLE
# =========================================================
with st.sidebar:
    logo_base64 = get_base64_image("logo_rs.png")
    if logo_base64:
        st.markdown(f"""
            <div class="sidebar-logo-container">
                <img src="data:image/png;base64,{logo_base64}" style="max-height: 75px; width: auto; background: white; padding: 4px 8px; border-radius: 8px; border: 1.5px solid #CBD5E1;">
            </div>
        """, unsafe_allow_html=True)
        
    current_un = st.session_state.user
    current_rl = st.session_state.role
    
    with get_db() as conn_sb:
        sb_row = conn_sb.execute(
            text("SELECT full_name, photo_path FROM users WHERE username = :un"), 
            {"un": current_un}
        ).mappings().fetchone()
    
    display_name = sb_row['full_name'] if (sb_row and sb_row['full_name']) else current_un
    
    profile_img_markup = f"https://ui-avatars.com/api/?name={display_name}&background=028090&color=fff&size=128&bold=true"
    
    if sb_row and sb_row['photo_path'] and os.path.exists(sb_row['photo_path']):
        b64_profile = get_base64_image(sb_row['photo_path'])
        if b64_profile:
            profile_img_markup = f"data:image/png;base64,{b64_profile}"

    st.markdown(f"""
        <div class="profile-card-lux">
            <img src="{profile_img_markup}" class="profile-avatar-lux">
            <div style="font-size: 15px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 2px;">{str(display_name).upper()}</div>
            <div style="font-size: 11px; font-weight: 700; background: rgba(255,255,255,0.2); display: inline-block; padding: 2px 10px; border-radius: 20px; color: #E2E8F0;">{current_rl}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📌 **MENU NAVIGASI**")
    
    menu_configs = [
        ("dashboard", "📊 0. Dashboard Utama"),
        ("daftar_kuitansi", "📋 1. Daftar Kuitansi"),
        ("pengembalian", "💸 2. Pengembalian (Refund)"),
        ("daftar_deposit", "📜 3. Daftar Uang Muka"),
        ("piutang", "📑 4. Manajemen Piutang"),
        ("laporan", "📊 5. Detail Laporan Kasir")
    ]
    
    if current_rl in ["Bendahara", "Super Admin"]:
        menu_configs.append(("rekon", "📑 6. Rekon Otomatis"))
        menu_configs.append(("master", "⚙️ 7. Kelola Master Data"))
        
    if current_rl == "Super Admin":
        menu_configs.append(("pengaturan_user", "👤 8. Kelola Akun User"))
        
    for menu_key, menu_label in menu_configs:
        if st.button(menu_label, key=f"nav_{menu_key}", use_container_width=True):
            st.session_state.current_menu = menu_key
            st.rerun()
            
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    if st.button("🚪 KELUAR (LOGOUT)", use_container_width=True):
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.current_menu = "dashboard"
        st.rerun()

routes = {
    "dashboard": dashboard.render_page,
    "daftar_kuitansi": daftar_kuitansi.render_page,
    "input_kuitansi": input_kuitansi.render_page,
    "pengembalian": pengembalian_transaksi.render_page,
    "input_pengembalian": input_pengembalian.render_page,
    "input_deposit": input_deposit.render_page,
    "daftar_deposit": daftar_deposit.render_page,
    "piutang": piutang.render_page,          
    "input_piutang": input_piutang.render_page,  
    "laporan_piutang": laporan_piutang.render_page, 
    "laporan": laporan_kasir.render_page,
    "rekon": rekon_otomatis.render_page,
    "master": master_data.render_page,
    "pengaturan_user": pengaturan_user.render_page
}

current_selected_menu = st.session_state.current_menu
if current_selected_menu == "rekon" and current_rl == "Kasir":
    st.session_state.current_menu = "dashboard"
    st.rerun()
elif current_selected_menu == "pengaturan_user" and current_rl != "Super Admin":
    st.session_state.current_menu = "dashboard"
    st.rerun()

if st.session_state.current_menu in routes:
    routes[st.session_state.current_menu]()