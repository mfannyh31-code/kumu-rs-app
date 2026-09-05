import os
import base64
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mengambil connection string dari st.secrets atau environment variable
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL"))

if not DATABASE_URL:
    st.error("DATABASE_URL belum dikonfigurasi! Harap masukkan connection string Supabase ke Streamlit Secrets.")
    st.stop()

# Membuat koneksi engine ke PostgreSQL Supabase
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Mengembalikan koneksi database SQLAlchemy untuk digunakan dalam context manager 'with'.
    """
    return engine.connect()

def init_db():
    """
    Membuat tabel-tabel yang diperlukan di Supabase PostgreSQL 
    jika belum ada, serta memasukkan akun default.
    """
    with engine.begin() as conn:
        # 1. Buat Tabel Users
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                full_name TEXT,
                password TEXT,
                role TEXT,
                photo_path TEXT
            )
        """))
        
        # Masukkan akun default (mfh, santy, fanny) ke database jika belum ada
        default_users = [
            ("mfh", "Super Admin (MFH)", "111", "Super Admin"),
            ("santy", "Santy", "111", "Bendahara"),
            ("fanny", "Fanny Hidayatullah", "111", "Kasir")
        ]
        
        for un, fn, pw, rl in default_users:
            res = conn.execute(text("SELECT id FROM users WHERE username = :un"), {"un": un}).fetchone()
            if not res:
                conn.execute(text("""
                    INSERT INTO users (username, full_name, password, role, photo_path) 
                    VALUES (:un, :fn, :pw, :rl, '')
                """), {"un": un, "fn": fn, "pw": pw, "rl": rl})

        # 2. Tabel Master Kategori Layanan (Kepala / Parent)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS service_categories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE
            )
        """))

        # 3. Tabel Kategori Unit (Menengah, dengan relasi ke service_categories)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                service_category_id INTEGER,
                name TEXT UNIQUE,
                FOREIGN KEY (service_category_id) REFERENCES service_categories(id)
            )
        """))

        # 4. Tabel Actions (Tindakan & Tarif)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS actions (
                id SERIAL PRIMARY KEY,
                category_id INTEGER,
                name TEXT,
                price REAL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """))

        # 5. Tabel Transactions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                receipt_no TEXT UNIQUE,
                receipt_date TEXT,
                input_date TEXT,
                shift TEXT,
                cashier_username TEXT,
                total_actions_amount REAL,
                final_amount REAL,
                payment_method TEXT,
                pay_tunai REAL DEFAULT 0,
                pay_transfer REAL DEFAULT 0,
                pay_edc REAL DEFAULT 0,
                pay_qris REAL DEFAULT 0,
                pay_va REAL DEFAULT 0,
                pay_deposit REAL DEFAULT 0,
                pay_pengembalian REAL DEFAULT 0,
                pay_pengakuan_bendahara REAL DEFAULT 0,
                pay_pengembalian_notes TEXT
            )
        """))

        # 6. Tabel Transaction Items
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transaction_items (
                id SERIAL PRIMARY KEY,
                receipt_no TEXT,
                book_no TEXT,
                category_name TEXT,
                action_name TEXT,
                price REAL,
                qty INTEGER,
                discount REAL,
                subtotal REAL
            )
        """))

        # 7. Tabel Deposits
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deposits (
                id SERIAL PRIMARY KEY,
                patient_id TEXT,
                patient_name TEXT,
                amount REAL,
                deposit_date TEXT,
                shift TEXT,
                payment_method TEXT,
                notes TEXT,
                status TEXT,
                input_by TEXT
            )
        """))

def format_rupiah(value):
    try:
        val = float(value)
        return f"Rp {val:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"

def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def render_header(title, subtitle):
    st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <h2 style="color: #0F172A; margin: 0; font-size: 24px; font-weight: 800;">{title}</h2>
            <p style="color: #64748B; margin: 4px 0 0 0; font-size: 14px; font-weight: 600;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)