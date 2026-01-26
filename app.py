import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. เชื่อมต่อระบบ (คงเดิม) ---
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

# --- 2. CSS ขั้นเทพ (ฆ่าทุกบั๊กที่พี่เจอ) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังเทาขาว */
        .stApp { background-color: #f8f9fa !important; }

        /* 2. ช่องกรอกข้อมูล + ลูกตาในกรอบ */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 8px !important;
        }
        input {
            border: none !important;
            box-shadow: none !important;
            color: #003366 !important; /* น้ำเงินเข้ม */
            text-align: left !important; /* ชิดซ้าย */
        }
        button[data-testid="stTextInputPasswordToggle"] {
            color: #1877f2 !important; /* ลูกตาสีฟ้า */
        }

        /* 3. ปุ่มเข้าสู่ระบบ (สีฟ้า) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
            border-radius: 8px !important;
        }

        /* 4. 🛑 ปุ่มลืมรหัสผ่าน (ลบกรอบทิ้ง เหลือแต่ตัวหนังสือสีฟ้า) */
        .forgot-link-area button {
            background-color: transparent !important;
            border: none !important;
            color: #1877f2 !important;
            box-shadow: none !important;
            text-decoration: none !important;
            font-size: 14px !important;
            height: auto !important;
            padding: 0 !important;
            margin-top: -10px !important;
        }
        .forgot-link-area button:hover {
            text-decoration: underline !important;
        }

        /* 5. 🟢 ปุ่มสร้างบัญชีใหม่ (สีเขียวเข้มข้น) */
        .signup-btn-area button {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
            border-radius: 8px !important;
        }

        /* 6. จัดการตัวหนังสือชื่อช่อง (Label) */
        label { color: #003366 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. แสดงผล ---
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            p = st.text_input("รหัสผ่าน", placeholder="Password", type="password")
            st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            # (ตรวจสอบ Login ปกติ)

        # 🛑 จุดลบกรอบปุ่มลืมรหัสผ่าน
        st.markdown('<div class="forgot-link-area">', unsafe_allow_html=True)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", use_container_width=True):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        
        # 🟢 จุดสีเขียวปุ่มสร้างบัญชีใหม่
        st.markdown('<div class="signup-btn-area">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", use_container_width=True):
            go_to('signup')
        st.markdown('</div>', unsafe_allow_html=True)

# (ส่วนหน้าอื่นๆ Signup / Game คงเดิม)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล")
            user = st.text_input("ชื่อผู้ใช้")
            phone = st.text_input("เบอร์โทร")
            pw = st.text_input("รหัสผ่าน", type="password")
            st.markdown('<div class="signup-btn-area">', unsafe_allow_html=True)
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อนี้มีคนใช้แล้ว")
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
    # (โค้ดดึงภารกิจเหมือนเดิม)
    if st.button("ออกจากระบบ", use_container_width=True):
        st.session_state.user = None
        go_to('login')
