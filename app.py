import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re

# --- 1. การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมของพี่) ---
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

# --- 3. CSS ฉบับ Nuclear Option (ปรับสไตล์ Link ตัวหนังสือ) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล: ขาว, ชิดซ้าย, น้ำเงินเข้ม */
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

        /* 🔵 ปุ่มสีฟ้า (เข้าสู่ระบบ) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สร้างบัญชี) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 10px !important;
        }

        /* 🔗 เปลี่ยนปุ่มลืมรหัสผ่านให้เป็น "ตัวหนังสือคลิกได้" เพียวๆ */
        .text-link-container {
            text-align: center;
            margin-top: -15px;
            margin-bottom: 15px;
        }
        .text-link-container button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #1877f2 !important;
            text-decoration: none !important;
            box-shadow: none !important;
            font-size: 14px !important;
            height: auto !important;
            min-height: unset !important;
            cursor: pointer !important;
        }
        .text-link-container button:hover {
            text-decoration: underline !important;
            background: none !important;
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
        
        # ส่วนตัวหนังสือลืมรหัสผ่าน (คลิกได้)
        st.markdown('<div class="text-link-container">', unsafe_allow_html=True)
        if st.button("คุณลืมรหัสผ่านใช่ไหม"):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก (Validation ครบทุกข้อ)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลขเท่านั้น)")
            fullname = st.text_input("ชื่อ-นามสกุล (ภาษาไทยเท่านั้น)")
            username = st.text_input("ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
            password = st.text_input("รหัสผ่าน (อังกฤษ/เลข 6-12 ตัว)", type="password")
            confirm_pw = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password")
            
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                # ตรวจสอบเงื่อนไข
                errors = []
                if not sid.isdigit(): errors.append("❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น")
                if not re.match(r'^[ก-ฮะ-์\s]+$', fullname): errors.append("❌ ชื่อต้องเป็นภาษาไทยเท่านั้น")
                if not re.match(r'^[a-zA-Z0-9]{6,12}$', username): errors.append("❌ ชื่อผู้ใช้ต้องเป็นอังกฤษ/เลข 6-12 ตัว")
                if not re.match(r'^0[689][0-9]{8}$', phone): errors.append("❌ เบอร์โทรต้องขึ้นต้นด้วย 06, 08, 09")
                if not re.match(r'^[a-zA-Z0-9]{6,12}$', password): errors.append("❌ รหัสผ่านต้องเป็นอังกฤษ/เลข 6-12 ตัว")
                if password != confirm_pw: errors.append("❌ รหัสผ่านไม่ตรงกัน")

                if errors:
                    for err in errors: st.error(err)
                else:
                    try:
                        supabase.table("users").insert({"student_id":sid, "fullname":fullname, "username":username, "phone":phone, "password":password}).execute()
                        st.success("✅ สำเร็จ!"); time.sleep(1.5); go_to('login')
                    except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): go_to('login')

# 🔑 หน้าลืมรหัสผ่าน (ยืนยัน 3 ชั้น)
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            u_check = st.text_input("Username")
            s_check = st.text_input("รหัสนักเรียน")
            t_check = st.text_input("เบอร์โทรศัพท์")
            new_pw = st.text_input("รหัสผ่านใหม่ (อังกฤษ/เลข 6-12 ตัว)", type="password")
            confirm_new_pw = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
            
            if st.form_submit_button("อัปเดตรหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_check).eq("student_id", s_check).eq("phone", t_check).execute()
                if not res.data:
                    st.error("❌ ข้อมูลไม่ถูกต้อง")
                elif not re.match(r'^[a-zA-Z0-9]{6,12}$', new_pw):
                    st.error("❌ รหัสผ่านใหม่ต้องเป็นอังกฤษ/เลข 6-12 ตัว")
                elif new_pw != confirm_new_pw:
                    st.error("❌ รหัสผ่านไม่ตรงกัน")
                else:
                    supabase.table("users").update({"password": new_pw}).eq("username", u_check).execute()
                    st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!"); time.sleep(1.5); go_to('login')
        if st.button("ยกเลิก", use_container_width=True, type="secondary"): go_to('login')

# 🎮 หน้าหลัก (คงเดิม)
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
        st.session_state.user = None
        go_to('login')
