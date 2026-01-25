import streamlit as st
from supabase import create_client
import re

# --- 1. ตั้งค่าหน้าตาแอป (Lock Design) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS สำหรับบังคับดีไซน์ให้ตรงตามสั่ง 100%
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อนแบบ Facebook */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer ของ Streamlit ออกให้หมด */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        .block-container { max-width: 400px !important; padding-top: 2rem !important; }

        /* 3. ส่วนหัวข้อ (Header) */
        .header-container { text-align: center; margin-bottom: 20px; }
        .main-logo { color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: -10px; font-family: sans-serif; }
        .sub-logo { color: #000000; font-size: 24px; font-weight: 500; margin-bottom: 20px; }

        /* 4. กรอบขาว (The White Box) */
        /* บังคับให้พื้นหลังขาวและขอบมน */
        div[data-testid="stVerticalBlock"] > div:has(div.login-box-trigger) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        }

        /* 5. ช่องกรอกข้อมูล (Inputs) */
        /* บังคับตัวหนังสือดำ พื้นขาว ขอบมน และลบปุ่มลูกตา */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px 16px !important;
            font-size: 17px !important;
        }
        ::placeholder { color: #8d949e !important; } /* ตัวหนังสือเทาในช่องกรอก */
        
        /* ซ่อนปุ่มดวงตา (Show Password) */
        button[aria-label="Show password"] { display: none !important; }
        
        /* ซ่อน Label (ชื่อหัวข้อด้านบนช่องกรอก) เพราะเราใช้ Placeholder แทน */
        label { display: none !important; }

        /* 6. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม ขอบมน) */
        .stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            height: 52px !important;
            width: 100% !important;
            margin-top: 10px;
        }
        .stButton > button:hover { background-color: #166fe5 !important; }

        /* 7. ลืมรหัสผ่าน (ตัวเล็กสีฟ้า) */
        .forgot-pass {
            color: #1877f2;
            font-size: 14px;
            text-align: center;
            display: block;
            margin-top: 15px;
            text-decoration: none;
        }

        /* 8. เส้นคั่น (Divider) */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }

        /* 9. ปุ่มสร้างบัญชีใหม่ (สีเขียว ขอบมน) */
        .signup-btn div.stButton > button {
            background-color: #42b72a !important;
            font-size: 17px !important;
            width: auto !important;
            padding: 0 20px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        .signup-btn div.stButton > button:hover { background-color: #36a420 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ส่วนแสดงผล UI ---

# หัวข้อโลโก้ด้านบน (นอกกรอบขาว)
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# เริ่มต้นกรอบขาว (White Box)
with st.container():
    # ตัว Marker สำหรับ CSS ให้รู้ว่านี่คือกล่องขาว
    st.markdown('<div class="login-box-trigger"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (Placeholder สีเทา)
    u_id = st.text_input("Username", placeholder="ชื่อผู้ใช้", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีลูกตา)
    u_pw = st.text_input("Password", type="password", placeholder="รหัสผ่าน", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม)
    if st.button("เข้าสู่ระบบ"):
        if u_id and u_pw:
            # ใส่ระบบเชื่อมต่อ Supabase ของคุณตรงนี้
            st.success("กำลังตรวจสอบข้อมูล...")
        else:
            st.error("กรุณากรอกข้อมูลให้ครบ")

    # ลิงก์ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ (สีเขียว)
    st.markdown('<div class="signup-btn">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่"):
        # ใส่คำสั่งให้ไปหน้าสมัครสมาชิก
        st.info("กำลังไปหน้าสมัครสมาชิก...")
    st.markdown('</div>', unsafe_allow_html=True)

# ปิดท้าย
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:20px;'>สร้างขึ้นเพื่อวินัยจราจรของพวกเรา</p>", unsafe_allow_html=True)
