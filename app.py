import streamlit as st

# --- 1. ตั้งค่าแอป ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ขั้นสูง (บังคับทุกอย่างตามสั่ง 100%) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อน และจัดกึ่งกลางหน้าจอ */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer ของ Streamlit ออกถาวร */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดการ block-container ให้ทุกอย่างกึ่งกลางหน้าจอ */
        .block-container {
            max-width: 400px !important;
            padding-top: 3rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 4. หัวข้อหลัก: traffic game (สีฟ้าเข้ม ตัวใหญ่ กึ่งกลาง) */
        .main-logo {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            font-family: Arial, Helvetica, sans-serif;
            letter-spacing: -2px;
            margin-bottom: 0px !important;
            text-align: center;
            width: 100%;
        }
        
        /* 5. บรรทัดต่อมา: เล่นเปลี่ยนรอด (สีดำ ตัวเล็กกว่า กึ่งกลาง) */
        .sub-logo {
            color: #000000;
            font-size: 20px;
            font-weight: 500;
            margin-top: -5px !important;
            margin-bottom: 25px !important;
            text-align: center;
            width: 100%;
        }

        /* 6. กรอบสีขาว (The White Card) ขอบมน กึ่งกลาง */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 25px 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 7. ช่องกรอกข้อมูล (Inputs) */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-size: 16px !important;
            text-align: center !important; /* จัดตัวหนังสือในช่องกึ่งกลาง */
        }
        ::placeholder { color: #8d949e !important; text-align: center; }

        /* **8. กำจัดกล่องแปลกๆ (Labels) ที่อยู่เหนือช่องกรอกออกถาวร** */
        div[data-testid="stWidgetLabel"] {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
        }

        /* **9. สั่งทำลายปุ่มลูกตาดูรหัสผ่านออกไปถาวร** */
        button[aria-label="Show password"] {
            display: none !important;
        }

        /* 10. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม ตัวขาว ขอบมน กึ่งกลาง) */
        div.stButton > button:first-child {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            margin: 10px auto 0px auto !important;
            display: block !important;
        }

        /* 11. ลืมรหัสผ่าน (สีฟ้า ตัวเล็ก กึ่งกลาง) */
        .forgot-pass {
            color: #1877f2;
            font-size: 14px;
            margin-top: 15px;
            display: block;
            text-decoration: none;
            text-align: center;
            width: 100%;
        }

        /* 12. เส้นคั่นกึ่งกลาง */
        .divider {
            border-bottom: 1px solid #dadde1;
            width: 100%;
            margin: 20px 0;
        }

        /* 13. ปุ่มสร้างบัญชีใหม่ (สีเขียว ขอบมน กึ่งกลาง) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 17px !important;
            font-weight: bold !important;
            width: auto !important;
            padding: 0 25px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ส่วนการแสดงผล (UI) ---

# หัวข้อด้านบน (จัดกึ่งกลาง)
st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

# เริ่มกรอบขาว
with st.container():
    # Anchor สำหรับ CSS บังคับกล่องนี้
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกชื่อผู้ใช้ (มี Placeholder เทาๆ)
    u_id = st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องกรอกรหัสผ่าน (ไม่มีปุ่มลูกตา 100%)
    u_pw = st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม กึ่งกลาง)
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        if u_id and u_pw:
            st.success("กำลังตรวจสอบข้อมูล...")
        else:
            st.error("กรุณากรอกข้อมูล")

    # ลืมรหัสผ่าน (สีฟ้า กึ่งกลาง)
    st.markdown('<a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ (สีเขียว กึ่งกลาง)
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.info("กำลังไปหน้าสมัครสมาชิก...")
    st.markdown('</div>', unsafe_allow_html=True)

# ปลายทาง
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:25px;'>Safety First System</p>", unsafe_allow_html=True)
