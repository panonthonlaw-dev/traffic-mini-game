import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมของพี่) ---
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

# --- 2. CSS พื้นฐาน (คุมพื้นหลังและช่องกรอก) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล: ขาว, ชิดซ้าย, น้ำเงินเข้ม */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 8px !important;
        }
        input {
            color: #003366 !important;
            text-align: left !important;
            border: none !important;
            box-shadow: none !important;
        }
        label { color: #003366 !important; font-weight: bold !important; }
        
        /* จัดการลูกตาให้อยู่ในกรอบ */
        button[data-testid="stTextInputPasswordToggle"] {
            color: #1877f2 !important;
            margin-right: 5px !important;
        }

        /* ปุ่มเข้าสู่ระบบ (สีฟ้ามาตรฐาน) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. การแสดงผลหน้าจอ LOGIN ---
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

        st.write("---")
        
        # 🟢 5. บังคับปุ่มสร้างบัญชีใหม่เป็น "สีเขียว" (ปุ่มต่อปุ่ม)
        st.markdown("""
            <style>
                /* เจาะจงไปที่ div ที่ครอบปุ่มสร้างบัญชี */
                .custom-green-btn div[data-testid="stButton"] button {
                    background-color: #42b72a !important;
                    color: white !important;
                    border: none !important;
                    font-weight: bold !important;
                    height: 48px !important;
                    width: 100% !important;
                    border-radius: 8px !important;
                }
                .custom-green-btn div[data-testid="stButton"] button:hover {
                    background-color: #369622 !important;
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="custom-green-btn">', unsafe_allow_html=True)
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
            
            # บังคับปุ่มยืนยันให้เป็นสีเขียวด้วย (ใช้ CSS เดิม)
            st.markdown('<div class="custom-green-btn">', unsafe_allow_html=True)
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                # โค้ดบันทึก Supabase...
                pass
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าเล่นเกม (คงเดิม)
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    # ... แสดงภารกิจ ...
    if st.button("ออกจากระบบ", use_container_width=True):
        st.session_state.user = None
        go_to('login')
