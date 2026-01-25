import streamlit as st

# --- 1. ตั้งค่าหน้าตาแอป ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ขั้นสูง (แก้ไขจุดที่เละทั้งหมด) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปและจัดกึ่งกลางหน้าจอ */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer ของ Streamlit */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดการ block-container ให้ทุกอย่างอยู่กึ่งกลางจริงๆ */
        .block-container {
            max-width: 400px !important;
            padding-top: 2rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 4. หัวข้อหลัก: traffic game (สีฟ้าเข้ม ตัวใหญ่) */
        .main-logo {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            letter-spacing: -2px;
            margin-bottom: 0px !important;
            text-align: center;
        }
        
        /* 5. บรรทัดต่อมา: เล่นเปลี่ยนรอด (สีดำ ตัวเล็กกว่า) */
        .sub-logo {
            color: #000000;
            font-size: 20px;
            font-weight: 500;
            margin-top: -10px !important;
            margin-bottom: 25px !important;
            text-align: center;
        }

        /* 6. กรอบสีขาว (The White Card) ขอบมน */
        /* ลบเงาที่เลอะเทอะ และบีบช่องว่างให้หายไป */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 7. ช่องกรอก (Inputs) */
        /* จัดตัวหนังสือในช่องกรอกให้กึ่งกลาง */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-size: 16px !important;
            text-align: center !important;
        }
        ::placeholder { color: #8d949e !important; text-align: center; }

        /* **8. กำจัดกล่องแปลกๆ (Labels) ที่อยู่เหนือช่องกรอกออกถาวร** */
        div[data-testid="stWidgetLabel"] {
            display: none !important;
        }
        /* กำจัดช่องว่างที่เหลือจากการซ่อน Label */
        .stTextInput {
            margin-top: -15px !important;
            margin-bottom: 10px !important;
        }

        /* **9. ทำลายปุ่มลูกตา (Show/Hide Password) ออกไปถาวร** */
        button[aria-label="Show password"] {
            display: none !important;
        }
        /* ปรับแต่งช่องรหัสผ่านไม่ให้เละ */
        div[data-baseweb="input"] {
            background-color: transparent !important;
            border: none !important;
        }

        /* 10. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม) - จัดกึ่งกลาง */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            margin: 15px auto 0px auto !important;
            display: block !important;
        }

        /* 11. ลืมรหัสผ่าน (สีฟ้า ตัวเล็ก) */
        .forgot-pass {
            color: #1877f2;
            font-size: 14px;
            margin-top: 15px;
            display: block;
            text-decoration: none;
            text-align: center;
            width: 100%;
        }

        /* 12. เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            width: 100%;
            margin: 20px 0;
        }

        /* 13. ปุ่มสร้างบัญชีใหม่ (สีเขียว) - จัดกึ่งกลาง */
        .signup-area div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            font-size: 16px !important;
            width: auto !important;
            padding: 0 30px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ส่วนการแสดงผล UI ---

# หัวข้อด้านบน (จัดกึ่งกลาง)
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

# เริ่มกรอบขาว
with st.container():
    # Anchor สำหรับ CSS สั่งจัดการกล่องนี้
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (ตัวเทาในช่อง)
    u_id = st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีลูกตา 100%)
    u_pw = st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ (กึ่งกลาง)
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        if u_id and u_pw:
            st.success("กำลังตรวจสอบข้อมูล...")
        else:
            st.error("กรุณากรอกข้อมูลให้ครบ")

    # ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ (สีเขียว กึ่งกลาง)
    st.markdown('<div class="signup-area">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.info("ระบบกำลังพาไปหน้าสมัครสมาชิก...")
    st.markdown('</div>', unsafe_allow_html=True)

# ข้อความท้ายสุด
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:25px;'>Traffic Discipline Management System</p>", unsafe_allow_html=True)
