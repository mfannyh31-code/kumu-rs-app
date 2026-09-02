import sqlite3
import streamlit as st
import base64
import os

DB_FILE = "hospital_billing.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Buat Tabel Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            password TEXT,
            role TEXT,
            photo_path TEXT
        )
    """)
    
    # Masukkan akun default (mfh, santy, fanny) ke database jika belum ada
    default_users = [
        ("mfh", "Super Admin (MFH)", "111", "Super Admin"),
        ("santy", "Santy", "111", "Bendahara"),
        ("fanny", "Fanny Hidayatullah", "111", "Kasir")
    ]
    
    for un, fn, pw, rl in default_users:
        c.execute("SELECT id FROM users WHERE username = ?", (un,))
        if not c.fetchone():
            c.execute("INSERT INTO users (username, full_name, password, role, photo_path) VALUES (?, ?, ?, ?, ?)", (un, fn, pw, rl, ""))

    # 2. Tabel Master Kategori Layanan (Kepala / Parent)
    c.execute("""
        CREATE TABLE IF NOT EXISTS service_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # 3. Tabel Kategori Unit (Menengah, dengan relasi ke service_categories)
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_category_id INTEGER,
            name TEXT UNIQUE,
            FOREIGN KEY (service_category_id) REFERENCES service_categories(id)
        )
    """)

    # 4. Tabel Actions (Tindakan & Tarif)
    c.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            price REAL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT,
            book_no TEXT,
            category_name TEXT,
            action_name TEXT,
            price REAL,
            qty INTEGER,
            discount REAL,
            subtotal REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
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
        )
    """)

    # --- MIGRASI OTOMATIS: Jaga-jaga jika tabel sudah ada tapi kurang kolom ---
    c.execute("PRAGMA table_info(transactions)")
    existing_columns_trx = [col[1] for col in c.fetchall()]
    columns_to_check_trx = {
        "pay_tunai": "REAL DEFAULT 0",
        "pay_transfer": "REAL DEFAULT 0",
        "pay_edc": "REAL DEFAULT 0",
        "pay_qris": "REAL DEFAULT 0",
        "pay_va": "REAL DEFAULT 0",
        "pay_deposit": "REAL DEFAULT 0",
        "pay_pengembalian": "REAL DEFAULT 0",
        "pay_pengakuan_bendahara": "REAL DEFAULT 0",
        "pay_pengembalian_notes": "TEXT"
    }

    for col_name, col_type in columns_to_check_trx.items():
        if col_name not in existing_columns_trx:
            try:
                c.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass

    # Migrasi otomatis untuk tabel categories agar memiliki kolom service_category_id
    c.execute("PRAGMA table_info(categories)")
    existing_columns_cat = [col[1] for col in c.fetchall()]
    if "service_category_id" not in existing_columns_cat:
        try:
            c.execute("ALTER TABLE categories ADD COLUMN service_category_id INTEGER")
        except Exception:
            pass
    
    conn.commit()
    conn.close()

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