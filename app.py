import streamlit as st
from supabase import create_client
import re

# --- 1. ตั้งค่าหน้าตาแอป (Facebook Style Config) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS สำหรับล็อคดีไซน์ให้เหมือน Facebook
st.markdown("""
    <style>
        /* บังคับพื้นหลังสีเทาอ่อน */
        .stApp { background-color: #f0f2f5 !important; }

        /* ซ่อนส่วนเกินของ Streamlit */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        .block-container { max-width: 400px !important; padding-top: 3rem !important; }

        /* หัวข้อ traffic game */
        .fb-logo {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0px;
            font-family: Arial, sans-serif;
            letter-spacing: -2px;
        }
        .fb-sub {
            color: #000000;
            font-size: 20px;
            text-align: center;
            margin-bottom: 25px;
            font-weight: 500;
        }

        /* กล่องสีขาว (White Box Container) */
        .login-card {
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        /* ปรับแต่งช่องกรอกข้อมูล */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-size: 16px !important;
        }
        
        /* **ลบปุ่มดวงตาในช่องรหัสผ่าน** */
        button[aria-label="Show password"] { display: none !important; }

        /* ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            margin-top: 10px;
        }

        /* ปุ่มสร้างบัญชีใหม่ (สีเขียว) */
        .signup-btn-container button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-size: 16px !important;
            font-weight: bold !important;
            width: auto !important;
            padding: 10px 20px !important;
        }

        /* ข้อความลืมรหัสผ่าน */
        .forgot-link {
            color: #1877f2 !important;
            font-size: 14px !important;
            text-decoration: none;
            display: block;
            margin: 15px 0;
        }

        /* เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services (Supabase) ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 3. ส่วนการแสดงผล (UI) ---

# หัวข้อด้านบนสุด
st.markdown("<div class='fb-logo'>traffic game</div>", unsafe_allow_html=True)
st.markdown("<div class='fb-sub'>เล่นเปลี่ยนรอด</div>", unsafe_allow_html=True)

# เริ่มสร้างกรอบสีขาว
with st.container():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # ถ้ายังไม่ Login ให้แสดงฟอร์ม
    if 'user' not in st.session_state:
        # ช่องกรอกชื่อผู้ใช้
        l_uid = st.text_input("ชื่อผู้ใช้", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="l_uid")
        
        # ช่องกรอกรหัสผ่าน (แบบไม่มีดวงตา)
        l_pw = st.text_input("รหัสผ่าน", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="l_pw")
        
        # ปุ่มเข้าสู่ระบบ
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                email = f"{l_uid.strip().lower()}@traffic.com"
                res = supabase.auth.sign_in_with_password({"email": email, "password": l_pw})
                if res.user:
                    st.session_state.user = res.user
                    st.rerun()
            except:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        
        # ลิงก์ลืมรหัสผ่าน
        st.markdown("<a href='#' class='forgot-link'>ลืมรหัสผ่านใช่หรือไม่?</a>", unsafe_allow_html=True)
        
        # เส้นคั่น
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ปุ่มสร้างบัญชีใหม่ (สีเขียว)
        st.markdown('<div class="signup-btn-container">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", key="btn_goto_signup"):
            # ในที่นี้ใช้การเปิด Popup หรือเปลี่ยนหน้าได้ตามต้องการ
            st.info("กำลังเปิดระบบสมัครสมาชิก...")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # หน้า Dashboard เมื่อ Login แล้ว
        st.write(f"ยินดีต้อนรับคุณ {st.session_state.user.email.split('@')[0]}")
        if st.button("ออกจากระบบ"):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # ปิดกล่องขาว

# ส่วนท้าย
st.markdown("<p style='text-align:center; font-size:12px; color:#606770; margin-top:20px;'>สำหรับใช้ภายในโรงเรียนเท่านั้น</p>", unsafe_allow_html=True)
