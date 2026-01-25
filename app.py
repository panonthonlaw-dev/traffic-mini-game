import streamlit as st

# --- 1. การตั้งค่าหน้าตาแอป (Lock Design) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS สำหรับบังคับดีไซน์ตามคำสั่งของคุณ
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อน */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อนส่วนเกินของ Streamlit ให้หมด */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดทุกอย่างให้อยู่กึ่งกลางหน้าจอ */
        .block-container {
            max-width: 400px !important;
            padding-top: 3rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 4. หัวข้อหลัก: traffic game (สีฟ้าเข้ม ตัวใหญ่) */
        .main-logo {
            color: #1877f2;
            font-size: 55px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            letter-spacing: -2px;
            margin-bottom: 0px;
        }
        
        /* 5. บรรทัดต่อมา: เล่นเปลี่ยนรอด (สีดำ ตัวเล็กกว่า) */
        .sub-logo {
            color: #000000;
            font-size: 24px;
            font-weight: 500;
            margin-top: -10px;
            margin-bottom: 30px;
        }

        /* 6. กรอบสีขาว (The White Card) ขอบมน */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-marker) {
            background-color: #ffffff !important;
            padding: 25px !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1) !important;
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
        }
        ::placeholder { color: #8d949e !important; } /* ตัวหนังสือเทาในช่องกรอก */
        
        /* ลบพื้นที่ว่างเหนือช่องกรอก (Label) ออก */
        div[data-testid="stWidgetLabel"] { display: none !important; }

        /* **8. ลบปุ่มลูกตาในช่องรหัสผ่าน** */
        button[aria-label="Show password"] { display: none !important; }

        /* 9. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม ตัวหนังสือขาว ขอบมน) */
        div.stButton > button {
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
        div.stButton > button:hover { background-color: #166fe5 !important; }

        /* 10. ลืมรหัสผ่าน (ตัวเล็กสีฟ้า) */
        .forgot-pass {
            color: #1877f2;
            font-size: 14px;
            margin-top: 15px;
            margin-bottom: 10px;
            display: block;
            text-decoration: none;
        }

        /* 11. เส้นคั่น (Divider) */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }

        /* 12. ปุ่มสร้างบัญชีใหม่ (สีเขียว ขอบมน) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            font-size: 17px !important;
            width: auto !important;
            padding: 0 20px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        .signup-container div.stButton > button:hover { background-color: #36a420 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ส่วนการแสดงผล (UI) ---

# หัวข้อนอกกรอบขาว
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

# เริ่มกรอบขาว (White Box)
with st.container():
    # ตัว Marker สำหรับ CSS
    st.markdown('<div class="login-card-marker"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (ตัวหนังสือเทา "ชื่อผู้ใช้")
    st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีลูกตา)
    st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม ตัวขาว)
    if st.button("เข้าสู่ระบบ"):
        st.info("ระบบกำลังตรวจสอบ...")

    # ลืมรหัสผ่าน (ตัวเล็กสีฟ้า)
    st.markdown('<a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ (สีเขียว ขอบมน)
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่"):
        st.success("กำลังไปหน้าสมัครสมาชิก...")
    st.markdown('</div>', unsafe_allow_html=True)

# ปลายทาง
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:20px;'>สร้างเพื่อวินัยจราจร</p>", unsafe_allow_html=True)
