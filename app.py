import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าพื้นฐาน (ห้ามลบ) ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ ---
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

# --- 3. CSS ฉบับ Nuclear Option (บังคับสีทุกจุด) ---
st.markdown("""
    <style>
        /* บังคับพื้นหลังเทาขาว */
        .stApp { background-color: #f8f9fa !important; }

        /* จัดกรอบ Input ให้ลูกตาอยู่ข้างในและตัวหนังสือชิดซ้าย */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 10px !important;
            padding: 2px !important;
        }
        input {
            color: #003366 !important;
            text-align: left !important;
            border: none !important;
            box-shadow: none !important;
        }
        label { color: #003366 !important; font-weight: bold !important; }
        button[data-testid="stTextInputPasswordToggle"] { color: #1877f2 !important; }

        /* 🔵 ปุ่มเข้าสู่ระบบ (ปุ่มในฟอร์ม) - บังคับสีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }

        /* 🟢 ฆ่าสีดำทิ้ง! บังคับปุ่มสร้างบัญชีใหม่เป็นสีเขียว */
        /* เราจะใช้ Selector ที่เจาะจงมาก ๆ เพื่อให้มันไม่เพี้ยน */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }
        
        /* สไตล์ตอนเอาเมาส์ไปชี้ปุ่มเขียว */
        div.stButton > button[kind="secondary"]:hover {
            background-color: #369622 !important;
            color: white !important;
        }
        
        /* สไตล์ Card ภารกิจ */
        .mission-card {
            background: white; padding: 15px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. การจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้")
            p = st.text_input("Password", placeholder="ระบุรหัสผ่าน", type="password")
            # ปุ่มนี้จะเป็นสีฟ้าอัตโนมัติจาก CSS Primary
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")

        st.write("---")
        
        # 🟢 ปุ่มสร้างบัญชีใหม่ (ชนิด secondary จะถูกบังคับเป็นสีเขียวด้วย CSS)
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password")
            # ใน Form เราใช้ Submit Button สีฟ้า
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("✅ สมัครสำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): 
            go_to('login')

# 🎮 หน้าหลัก/ภารกิจ (คงเดิม)
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        # โค้ดแสดงภารกิจ (แสดงแค่ชื่อพอให้เห็นภาพ)
        st.markdown('<div class="mission-card"><b>ภารกิจที่ 1: ตรวจเช็คหมวกกันน็อก</b></div>', unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
            st.session_state.user = None
            go_to('login')
