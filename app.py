import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเวป ---
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

# --- 3. CSS ฉบับ Nuclear Option (ปรับปรุงจากตัวที่พี่ใช้ได้) ---
st.markdown("""
    <style>
        /* พื้นหลังเทาขาว */
        .stApp { background-color: #f8f9fa !important; }

        /* ✅ จัดกรอบขาว: ครอบทั้งช่อง Input และ ลูกตา */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 10px !important;
            padding: 2px !important;
        }

        /* ✅ ตัวหนังสือ: น้ำเงินเข้ม (#003366) และ ชิดซ้าย */
        input {
            color: #003366 !important;
            -webkit-text-fill-color: #003366 !important;
            text-align: left !important;
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        
        /* ชื่อหัวข้อช่องกรอก */
        label { color: #003366 !important; font-weight: bold !important; }

        /* ✅ ลูกตา: บังคับให้อยู่ในกรอบขาว และเป็นสีฟ้า */
        button[data-testid="stTextInputPasswordToggle"] {
            color: #1877f2 !important;
            background-color: transparent !important;
        }

        /* 🔵 ปุ่มเข้าสู่ระบบ: บังคับสีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสร้างบัญชีใหม่: ใช้ kind="secondary" ตามที่พี่คอนเฟิร์มว่าเวิร์ก */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }
        
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
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")

        st.write("---")
        
        # 🟢 ปุ่มสร้างบัญชีใหม่ (ใช้ type="secondary" เพื่อให้แมตช์กับ CSS kind="secondary")
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
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("✅ สมัครสำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): 
            go_to('login')

# 🎮 หน้าหลัก/ภารกิจ
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h4 style='text-align: center; color: #003366;'>ยินดีต้อนรับคุณ {u['fullname']} 👋</h4>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        # แสดงภารกิจแบบการ์ด
        st.markdown('<div class="mission-card"><b>ภารกิจที่ 1: ตรวจเช็คหมวกกันน็อก</b></div>', unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
            st.session_state.user = None
            go_to('login')
