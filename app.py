import streamlit as st

# --- 1. ตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS บังคับกึ่งกลางและลบส่วนเกิน (เนียนที่สุด) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังและลบ Header/Footer */
        .stApp { background-color: #f0f2f5 !important; }
        header, footer, [data-testid="stSidebar"] { display: none !important; }
        
        /* 2. จัด Layout หลักให้กึ่งกลางหน้าจอ */
        .block-container {
            max-width: 400px !important;
            padding-top: 5rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 3. หัวข้อหลัก (สีฟ้าเข้ม) */
        .main-logo {
            color: #1877f2 !important;
            font-size: 50px !important;
            font-weight: bold !important;
            font-family: Arial, sans-serif !important;
            letter-spacing: -2px !important;
            margin: 0 !important;
            text-align: center;
        }
        
        /* 4. หัวข้อรอง (สีดำ) */
        .sub-logo {
            color: #000000 !important;
            font-size: 20px !important;
            font-weight: 500 !important;
            margin-top: -10px !important;
            margin-bottom: 25px !important;
            text-align: center;
        }

        /* 5. กล่องขาว (The White Card) ขอบมน */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100% !important;
        }

        /* 6. ช่องกรอก (Inputs) - กึ่งกลาง */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            text-align: center !important;
            font-size: 16px !important;
        }
        ::placeholder { color: #8d949e !important; text-align: center; }

        /* 7. ลบช่องว่าง/Label เหนือชื่อผู้ใช้ */
        [data-testid="stWidgetLabel"] { display: none !important; }
        .stTextInput { margin-top: -15px !important; margin-bottom: 10px !important; width: 100%; }

        /* 8. **ทำลายลูกตาถาวร** */
        button[aria-label="Show password"], .stTextInput div[data-baseweb="input"] button {
            display: none !important;
            visibility: hidden !important;
        }

        /* 9. จัดปุ่มทุกปุ่มให้กึ่งกลาง */
        div.stButton {
            display: flex;
            justify-content: center;
            width: 100%;
        }

        /* ปุ่มเข้าสู่ระบบ (ฟ้าเข้ม) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 8px !important;
            border: none !important;
        }

        /* ปุ่มสร้างบัญชี (เขียว) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            width: auto !important;
            padding: 0 30px !important;
            margin-top: 10px !important;
        }

        /* 10. ลืมรหัสผ่าน */
        .forgot-link {
            color: #1877f2 !important;
            font-size: 14px !important;
            text-decoration: none !important;
            display: block;
            margin: 15px 0;
            text-align: center;
        }

        /* 11. เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dddfe2;
            margin: 20px 0;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. การแสดงผล UI ---

# หัวข้อด้านบน
st.markdown('<p class="main-logo">traffic game</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-logo">เล่นเปลี่ยนรอด</p>', unsafe_allow_html=True)

# กล่องขาว
with st.container():
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องกรอกข้อมูล
    st.text_input("U", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    st.text_input("P", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        st.info("กำลังตรวจสอบข้อมูล...")

    # ส่วนล่างของฟอร์ม
    st.markdown('<a href="#" class="forgot-link">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.success("ไปหน้าสมัครสมาชิก")
    st.markdown('</div>', unsafe_allow_html=True)
