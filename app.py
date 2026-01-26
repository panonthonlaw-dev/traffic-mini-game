import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเวป ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ (คงเดิม) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n").strip()
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
except Exception as e:
    st.error(f"❌ ระบบเชื่อมต่อไม่ได้: {e}")
    st.stop()

# --- 3. รวมศูนย์ CSS (ฉบับถอดรูปปุ่มให้เป็นตัวอักษร) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }

        /* 🔵 ช่องกรอกข้อมูล + ลูกตาในกรอบ */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 8px !important;
            padding: 2px !important;
        }
        input { color: #003366 !important; text-align: left !important; border: none !important; }
        label { color: #003366 !important; font-weight: bold !important; }
        button[data-testid="stTextInputPasswordToggle"] { color: #1877f2 !important; }

        /* 🔵 ปุ่มเข้าสู่ระบบ (สีฟ้ามาตรฐาน) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
        }

        /* 🛑 แก้ไข: ปุ่มลืมรหัสผ่าน ให้เป็น "ตัวอักษรเพียว ๆ" */
        .forgot-text-link button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #1877f2 !important;
            text-decoration: none !important;
            box-shadow: none !important;
            display: inline !important;
            height: auto !important;
            min-height: unset !important;
            font-size: 14px !important;
        }
        .forgot-text-link button:hover {
            text-decoration: underline !important;
            background: none !important;
        }

        /* 🟢 แก้ไข: ปุ่มสร้างบัญชีใหม่ (สีเขียว) */
        .green-button-style button {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. แสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; margin-top: 0; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            p = st.text_input("รหัสผ่าน", placeholder="Password", type="password")
            st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            # ตรวจสอบ Login... (เหมือนเดิม)

        # 🛑 จุดที่ทำให้เป็น "ตัวอักษรเพียว ๆ"
        st.markdown('<div style="text-align: center;" class="forgot-text-link">', unsafe_allow_html=True)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", use_container_width=True):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        
        # 🟢 จุดที่ทำให้เป็น "ปุ่มสีเขียว"
        st.markdown('<div class="green-button-style">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", use_container_width=True):
            go_to('signup')
        st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล")
            user = st.text_input("ชื่อผู้ใช้")
            phone = st.text_input("เบอร์โทร")
            pw = st.text_input("รหัสผ่าน", type="password")
            
            st.markdown('<div class="green-button-style">', unsafe_allow_html=True)
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("❌ ชื่อนี้มีคนใช้แล้ว")
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าหลัก/ภารกิจ
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 6, 1])
    with col:
        # โค้ดแสดงภารกิจ (คงเดิม)
        # ...
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center; color: #003366;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("forgot_form"):
            ut = st.text_input("ระบุ Username")
            if st.form_submit_button("ค้นหารหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("password").eq("username", ut).execute()
                if res.data: st.success(f"🔑 รหัสคือ: {res.data[0]['password']}")
                else: st.error("ไม่พบข้อมูล")
        if st.button("กลับหน้าหลัก", use_container_width=True): go_to('login')
