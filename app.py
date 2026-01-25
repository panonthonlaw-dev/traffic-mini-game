import streamlit as st
from supabase import create_client
import re

# --- 1. ตั้งค่าหน้าตาแอปและการจัดวาง ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        /* 1. พื้นหลังเทาอ่อนและจัดทุกอย่างกึ่งกลางหน้าจอ */
        .stApp {
            background-color: #f0f2f5 !important;
            display: flex;
            justify-content: center;
        }

        /* 2. ซ่อน Header/Footer/Sidebar */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        
        /* 3. จัดการขนาดกล่องหลัก */
        .block-container {
            max-width: 400px !important;
            padding-top: 5rem !important;
            text-align: center;
        }

        /* 4. หัวข้อหลัก: traffic game */
        .main-logo {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            margin-bottom: -10px;
            font-family: sans-serif;
            letter-spacing: -2px;
        }
        
        /* หัวข้อรอง: เล่นเปลี่ยนรอด */
        .sub-logo {
            color: #000000;
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 30px;
        }

        /* 5. กรอบสีขาว (The White Card) */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-trigger) {
            background-color: #ffffff !important;
            padding: 25px !important;
            border-radius: 15px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
        }

        /* 6. ช่องกรอกข้อมูล (Inputs) */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 10px !important;
            padding: 14px !important;
            font-size: 16px !important;
            text-align: center; /* จัดตัวหนังสือในช่องกรอกกึ่งกลาง */
        }
        ::placeholder { color: #8d949e !important; text-align: center; }

        /* **ลบปุ่มลูกตาในช่องรหัสผ่าน** */
        button[aria-label="Show password"] { display: none !important; }
        
        /* ลบช่องว่างเหนือ Input */
        div[data-testid="stWidgetLabel"] { display: none !important; }

        /* 7. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม) */
        .stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            margin-top: 10px;
        }

        /* 8. ลืมรหัสผ่าน */
        .forgot-link {
            color: #1877f2;
            font-size: 14px;
            text-decoration: none;
            display: block;
            margin: 15px 0;
        }

        /* 9. เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }

        /* 10. ปุ่มสร้างบัญชีใหม่ (สีเขียว) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            font-size: 16px !important;
            width: auto !important;
            padding: 0 25px !important;
            margin: 0 auto !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การแสดงผล UI ---

# หัวข้อด้านบน
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

# เริ่มกรอบขาว
with st.container():
    # ตัวบอก CSS ว่านี่คือการ์ด
    st.markdown('<div class="login-card-trigger"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (ใช้ collapsed เพื่อลบช่องว่างด้านบน)
    u_id = st.text_input("UserID", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีลูกตา)
    u_pw = st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        if u_id and u_pw:
            st.info("กำลังตรวจสอบข้อมูล...")
        else:
            st.error("กรุณากรอกข้อมูล")

    # ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-link">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.info("ระบบกำลังพาไปหน้าสมัครสมาชิก")
    st.markdown('</div>', unsafe_allow_html=True)

# ปิดท้าย
st.markdown("<p style='color:#606770; font-size:12px; margin-top:30px;'>Traffic Discipline System</p>", unsafe_allow_html=True)
