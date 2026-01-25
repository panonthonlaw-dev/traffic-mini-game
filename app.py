import streamlit as st
import re

# --- 1. ตั้งค่าหน้าตาแอป (Lock Design 100%) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS ขั้นสูง: ลบปุ่มลูกตา ลบช่องว่าง และจัดกึ่งกลางตามสั่ง
st.markdown("""
    <style>
        /* 1. พื้นหลังเทาอ่อน และจัดตัวแอปให้กึ่งกลางหน้าจอ */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดการให้ทุกอย่างใน block-container อยู่กึ่งกลาง */
        .block-container {
            max-width: 400px !important;
            padding-top: 4rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        /* 4. หัวข้อหลัก: traffic game (สีฟ้าเข้ม ตัวใหญ่) */
        .main-logo {
            color: #1877f2;
            font-size: 55px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            letter-spacing: -2px;
            margin-bottom: 0px;
            text-align: center;
        }
        
        /* 5. บรรทัดต่อมา: เล่นเปลี่ยนรอด (สีดำ ตัวเล็กกว่า) */
        .sub-logo {
            color: #000000;
            font-size: 22px;
            font-weight: 500;
            margin-top: -10px;
            margin-bottom: 30px;
            text-align: center;
        }

        /* 6. กรอบสีขาว (The White Card) ขอบมน */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 25px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
            text-align: center;
        }

        /* 7. ช่องกรอก (Inputs) ตัวหนังสือดำ พื้นขาว ขอบมน */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px 16px !important;
            font-size: 17px !important;
            text-align: center; /* จัดตัวหนังสือในช่องกรอกกึ่งกลาง */
        }
        ::placeholder { color: #8d949e !important; }

        /* **8. ลบช่องแปลกๆ (Label) เหนือช่องกรอกออกถาวร** */
        div[data-testid="stWidgetLabel"] {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
        }
        
        /* **9. สั่งทำลายปุ่มลูกตา (Show/Hide Password) ถาวร** */
        button[aria-label="Show password"] {
            display: none !important;
        }
        /* แก้ไขโครงสร้างภายในช่องรหัสผ่านไม่ให้เละ */
        div[data-baseweb="input"] {
            background-color: transparent !important;
        }

        /* 10. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม ตัวขาว ขอบมน) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            height: 52px !important;
            width: 100% !important;
            margin-top: 15px;
        }

        /* 11. ลืมรหัสผ่าน (สีฟ้า ตัวเล็ก) */
        .forgot-pass {
            color: #1877f2;
            font-size: 14px;
            margin-top: 15px;
            display: block;
            text-decoration: none;
            text-align: center;
        }

        /* 12. เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }

        /* 13. ปุ่มสร้างบัญชีใหม่ (สีเขียว ขอบมน) */
        .signup-area div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            font-size: 17px !important;
            width: auto !important;
            padding: 0 25px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การแสดงผล UI ---

# หัวข้อนอกกรอบขาว (จัดกึ่งกลาง)
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

# เริ่มกรอบขาว
with st.container():
    # ตัวยึด CSS เพื่อให้รู้ว่าคือ Card
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (ไม่มีช่องว่างด้านบน)
    st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีลูกตา 100%)
    st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        st.success("กำลังเข้าสู่ระบบ...")

    # ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่
    st.markdown('<div class="signup-area">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.info("กำลังพาไปหน้าสมัครสมาชิก...")
    st.markdown('</div>', unsafe_allow_html=True)

# ข้อความท้ายสุด
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:25px;'>Safety First, Save Lives.</p>", unsafe_allow_html=True)
