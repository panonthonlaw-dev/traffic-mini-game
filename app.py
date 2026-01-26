import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re

# --- 1. ตั้งค่าหน้าเว็บ ---
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

# --- 3. CSS (คุมโทนเดิมของพี่เป๊ะๆ) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 10px !important;
        }
        input { color: #003366 !important; text-align: left !important; border: none !important; }
        label { color: #003366 !important; font-weight: bold !important; }
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; font-weight: bold !important;
            height: 50px !important; width: 100% !important; border-radius: 10px !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important; font-weight: bold !important;
            height: 50px !important; width: 100% !important; border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN (พร้อมระบบแยกสิทธิ์)
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="Username")
            p = st.text_input("Password", placeholder="Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    user_data = res.data[0]
                    st.session_state.user = user_data
                    
                    # ✨ จุดแยกสิทธิ์: เช็คว่าใครเป็น Admin หรือ Player
                    if user_data.get('role') == 'admin':
                        go_to('admin_dashboard')
                    else:
                        go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        st.markdown('<div style="text-align: center; margin-top: -10px; margin-bottom: 15px;"><a href="./?page=forgot" target="_self" style="color: #1877f2; text-decoration: none; font-size: 14px;">คุณลืมรหัสผ่านใช่ไหม</a></div>', unsafe_allow_html=True)
        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก (ตั้งค่าเริ่มต้นให้เป็น player เสมอ)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลขเท่านั้น)")
            fullname = st.text_input("ชื่อ-นามสกุล (ภาษาไทย)")
            username = st.text_input("ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
            password = st.text_input("รหัสผ่าน (อังกฤษ/เลข 6-12 ตัว)", type="password")
            confirm_pw = st.text_input("ยืนยันรหัสผ่าน", type="password")
            
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                # ... (ตรวจสอบ Regex เหมือนเดิม) ...
                if password == confirm_pw:
                    try:
                        # สมัครสมาชิกใหม่จะได้สิทธิ์ 'player' โดยอัตโนมัติ
                        supabase.table("users").insert({
                            "student_id": sid, "fullname": fullname, "username": username,
                            "phone": phone, "password": password, "role": "player"
                        }).execute()
                        st.success("✅ สำเร็จ!"); time.sleep(1.5); go_to('login')
                    except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")

# 🎮 หน้ากิจกรรม (สำหรับผู้เล่น)
elif st.session_state.page == 'game':
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>ยินดีต้อนรับคุณ {st.session_state.user['fullname']} 👋</h3>", unsafe_allow_html=True)
    # แสดงหน้าจอกิจกรรมตามเดิม...
    if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
        st.session_state.user = None
        go_to('login')

# 🛠️ หน้าระบบหลังบ้าน (สำหรับแอดมิน)
elif st.session_state.page == 'admin_dashboard':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>Back-End Admin</h2>", unsafe_allow_html=True)
    st.info(f"ผู้ดูแลระบบ: {st.session_state.user['fullname']}")
    
    # ดึงข้อมูลนักเรียนทั้งหมดมาโชว์ (ตัวอย่าง)
    users_res = supabase.table("users").select("student_id, fullname, phone, role").execute()
    st.write("### รายชื่อนักเรียนในระบบ")
    st.table(users_res.data)
    
    if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
        st.session_state.user = None
        go_to('login')
