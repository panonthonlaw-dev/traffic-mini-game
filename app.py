import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re  # ใช้สำหรับตรวจสอบรูปแบบข้อความ (Regex)

# --- 1. ตั้งค่าพื้นฐาน ---
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

# --- 3. CSS ฉบับ Nuclear Option (คงเดิม) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 10px !important;
            padding: 2px !important;
        }
        input {
            color: #003366 !important;
            -webkit-text-fill-color: #003366 !important;
            text-align: left !important;
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        label { color: #003366 !important; font-weight: bold !important; }
        button[data-testid="stTextInputPasswordToggle"] { color: #1877f2 !important; }
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }
        .forgot-text {
            color: #1877f2; font-size: 13px; text-align: center;
            margin-top: -10px; margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN (คงเดิมตามมาตรฐานพี่)
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
        st.markdown('<p class="forgot-text">คุณลืมรหัสผ่านใช่ไหม</p>', unsafe_allow_html=True)
        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก (เพิ่มเงื่อนไขการตรวจสอบตามสั่ง)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            fullname = st.text_input("ชื่อ-นามสกุล (ภาษาไทยเท่านั้น)", placeholder="เช่น สมชาย ใจดี")
            username = st.text_input("ชื่อผู้ใช้ (อังกฤษ/ตัวเลข 6-12 ตัว)", placeholder="Username")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก ขึ้นต้นด้วย 06, 08, 09)", placeholder="08XXXXXXXX")
            password = st.text_input("รหัสผ่าน (อังกฤษ/ตัวเลข 6-12 ตัว)", type="password")
            confirm_pw = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password")
            
            submit = st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True)
            
            if submit:
                # --- ส่วนตรวจสอบเงื่อนไข ---
                errors = []
                
                # 1. ตรวจสอบชื่อไทย (รวมช่องว่าง)
                if not re.match(r'^[ก-ฮะ-์\s]+$', fullname):
                    errors.append("❌ ชื่อ-นามสกุล ต้องเป็นภาษาไทยเท่านั้น")
                
                # 2. ตรวจสอบชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)
                if not re.match(r'^[a-zA-Z0-9]{6,12}$', username):
                    errors.append("❌ ชื่อผู้ใช้ต้องเป็นภาษาอังกฤษหรือตัวเลข ความยาว 6-12 ตัวอักษร")
                
                # 3. ตรวจสอบเบอร์โทร (10 หลัก ขึ้นต้นด้วย 06, 08, 09)
                if not re.match(r'^0[689][0-9]{8}$', phone):
                    errors.append("❌ เบอร์โทรต้องมี 10 หลัก และขึ้นต้นด้วย 06, 08 หรือ 09 เท่านั้น")
                
                # 4. ตรวจสอบรหัสผ่าน (อังกฤษ/เลข 6-12 ตัว)
                if not re.match(r'^[a-zA-Z0-9]{6,12}$', password):
                    errors.append("❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลข ความยาว 6-12 ตัวอักษร")
                
                # 5. ตรวจสอบรหัสผ่านให้ตรงกัน
                if password != confirm_pw:
                    errors.append("❌ รหัสผ่านทั้งสองช่องไม่ตรงกัน")

                # --- ผลลัพธ์การตรวจสอบ ---
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        # บันทึกลง Supabase
                        supabase.table("users").insert({
                            "fullname": fullname,
                            "username": username,
                            "phone": phone,
                            "password": password
                        }).execute()
                        st.success("✅ สมัครสมาชิกสำเร็จ!")
                        time.sleep(1.5)
                        go_to('login')
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: ชื่อผู้ใช้นี้อาจมีคนใช้แล้ว")

        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): 
            go_to('login')

# 🎮 หน้าหลัก/ภารกิจ (คงเดิม)
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        st.markdown('<div class="mission-card"><b>ภารกิจที่ 1: ตรวจเช็คหมวกกันน็อก</b></div>', unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
            st.session_state.user = None
            go_to('login')
