import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re

# --- 1. ตั้งค่าหน้าเว็บและการเปลี่ยนหน้าผ่านลิงก์ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# ตรวจสอบลิงก์จาก URL (ถ้ามี ?page=... ให้เปลี่ยนหน้าตามนั้น)
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]

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

# --- 3. CSS ฉบับ Nuclear (เน้นคุมปุ่มฟ้า ปุ่มเขียว และ Input) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 10px !important;
        }
        input { color: #003366 !important; text-align: left !important; border: none !important; }
        label { color: #003366 !important; font-weight: bold !important; }
        button[data-testid="stTextInputPasswordToggle"] { color: #1877f2 !important; }

        /* 🔵 ปุ่มสีฟ้า (เข้าสู่ระบบ) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (ย้อนกลับ / สร้างบัญชี / ส่งงาน) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page_name):
    # ล้างค่าใน URL และเปลี่ยน State
    st.query_params.clear()
    st.session_state.page = page_name
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
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
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        # ✨ ลิงก์ HTML ของจริง (ไม่ใช้ปุ่ม)
        st.markdown("""
            <div style="text-align: center; margin-top: -10px; margin-bottom: 15px;">
                <a href="./?page=forgot" target="_self" style="color: #1877f2; text-decoration: none; font-size: 14px;">คุณลืมรหัสผ่านใช่ไหม</a>
            </div>
        """, unsafe_allow_html=True)

        st.write("---")
        # ปุ่มสร้างบัญชี (ใช้ชนิด secondary เพื่อให้เป็นสีเขียว)
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลขเท่านั้น)")
            fullname = st.text_input("ชื่อ-นามสกุล (ภาษาไทย)")
            user = st.text_input("ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
            pw = st.text_input("รหัสผ่าน (อังกฤษ/เลข 6-12 ตัว)", type="password")
            cpw = st.text_input("ยืนยันรหัสผ่าน", type="password")
            
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                if sid.isdigit() and re.match(r'^[ก-ฮะ-์\s]+$', fullname) and pw == cpw:
                    try:
                        supabase.table("users").insert({"student_id": sid, "fullname": fullname, "username": user, "phone": phone, "password": pw, "role": "player"}).execute()
                        st.success("✅ สำเร็จ!"); time.sleep(1.5); go_to('login')
                    except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                else: st.error("❌ ข้อมูลไม่ถูกต้องตามเงื่อนไข")
        
        # ✅ ปุ่มย้อนกลับ (ย้ายมาไว้นอก Form และเป็นสีเขียว)
        if st.button("ย้อนกลับหน้าแรก", use_container_width=True, type="secondary"):
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน (กู้คืนด้วย 3 ข้อมูลหลัก)
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            u_check = st.text_input("Username")
            s_check = st.text_input("รหัสนักเรียน")
            t_check = st.text_input("เบอร์โทรศัพท์")
            new_pw = st.text_input("รหัสผ่านใหม่", type="password")
            confirm_new_pw = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
            if st.form_submit_button("อัปเดตรหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_check).eq("student_id", s_check).eq("phone", t_check).execute()
                if res.data and new_pw == confirm_new_pw:
                    supabase.table("users").update({"password": new_pw}).eq("username", u_check).execute()
                    st.success("✅ เปลี่ยนรหัสสำเร็จ!"); time.sleep(1.5); go_to('login')
                else: st.error("❌ ข้อมูลยืนยันไม่ถูกต้อง")
        
        # ✅ ปุ่มยกเลิกสีเขียว
        if st.button("ยกเลิกและย้อนกลับ", use_container_width=True, type="secondary"):
            go_to('login')

# 🎮 หน้ากิจกรรม (สำหรับ Player)
elif st.session_state.page == 'game':
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>กิจกรรมของคุณ {st.session_state.user['fullname']}</h3>", unsafe_allow_html=True)
    if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
        st.session_state.user = None
        go_to('login')

# 🛠️ หน้าหลังบ้าน (สำหรับ Admin)
elif st.session_state.page == 'admin_dashboard':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>ระบบจัดการหลังบ้าน (Admin)</h2>", unsafe_allow_html=True)
    if st.button("ออกจากระบบ", use_container_width=True, type="secondary"):
        st.session_state.user = None
        go_to('login')
