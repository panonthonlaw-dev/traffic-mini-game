import streamlit as st

# --- 1. ตั้งค่าหน้ากระดาษ ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ขั้นเทพ (บังคับกึ่งกลางและคลีน 100%) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อนและบังคับ Layout หลักให้กึ่งกลาง */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer */
        header, footer, [data-testid="stSidebar"] { display: none !important; }
        
        /* 3. จัดการ Container หลักให้กึ่งกลางตลอดเวลา */
        .block-container {
            max-width: 400px !important;
            padding-top: 5rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        /* 4. หัวข้อหลัก: traffic game (สีฟ้าเข้ม ตัวใหญ่ กึ่งกลาง) */
        .main-logo {
            color: #1877f2 !important;
            font-size: 50px !important;
            font-weight: bold !important;
            font-family: Arial, sans-serif !important;
            letter-spacing: -2px !important;
            margin: 0 !important;
            text-align: center;
            width: 100%;
        }
        
        /* 5. หัวข้อรอง: เล่นเปลี่ยนรอด (สีดำ ตัวเล็กกว่า กึ่งกลาง) */
        .sub-logo {
            color: #000000 !important;
            font-size: 20px !important;
            font-weight: 500 !important;
            margin-top: -10px !important;
            margin-bottom: 25px !important;
            text-align: center;
            width: 100%;
        }

        /* 6. การ์ดสีขาว (The White Card) ขอบมน เนียนกริ๊บ */
        /* บังคับให้ลูกข้างใน (ปุ่ม/ช่องกรอก) จัดกึ่งกลาง */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.05) !important;
            border: 1px solid #dddfe2 !important;
            width: 100% !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 7. ช่องกรอกข้อมูล (Inputs) - ตัวหนังสือดำ กึ่งกลาง */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-size: 16px !important;
            text-align: center !important; /* จัดกึ่งกลางตัวหนังสือที่พิมพ์ */
            box-shadow: none !important;
        }
        ::placeholder { color: #8d949e !important; text-align: center; }

        /* 8. **ลบกล่องว่างประหลาด (Label) ออกถาวร** */
        [data-testid="stWidgetLabel"] {
            display: none !important;
        }
        .stTextInput { margin-top: -15px !important; margin-bottom: 10px !important; width: 100%; }

        /* 9. **ฆ่าปุ่มลูกตา (Show password) ให้หายสาบสูญ** */
        button[aria-label="Show password"], 
        .stTextInput div[data-baseweb="input"] button {
            display: none !important;
            visibility: hidden !important;
        }

        /* 10. **จัดกึ่งกลางทุกปุ่ม (Streamlit Button Wrapper)** */
        div.stButton {
            display: flex;
            justify-content: center;
            width: 100%;
        }

        /* ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม กึ่งกลาง) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            margin-top: 10px !important;
            transition: 0.2s;
        }
        div.stButton > button:hover {
            background-color: #166fe5 !important;
            box-shadow: 0 4px 8px rgba(24, 119, 242, 0.2) !important;
        }

        /* 11. ลืมรหัสผ่าน (กึ่งกลาง) */
        .forgot-link {
            color: #1877f2 !important;
            font-size: 14px !important;
            text-decoration: none !important;
            display: block;
            margin: 15px 0;
            text-align: center;
            width: 100%;
        }

        /* 12. เส้นคั่นบางๆ กึ่งกลาง */
        .divider {
            border-bottom: 1px solid #dddfe2;
            margin: 20px 0;
            width: 100%;
        }

        /* 13. ปุ่มสร้างบัญชีใหม่ (สีเขียว กึ่งกลาง) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            width: auto !important;
            min-width: 180px;
            padding: 0 30px !important;
            margin: 0 auto !important;
            display: block !important;
            font-size: 17px !important;
        }
        .signup-container div.stButton > button:hover {
            background-color: #36a420 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. การแสดงผล UI ---

# Header ด้านบน
st.markdown('<p class="main-logo">traffic game</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-logo">เล่นเปลี่ยนรอด</p>', unsafe_allow_html=True)

# กล่องขาวพรีเมียม
with st.container():
    # Anchor สำหรับ CSS สั่งจัดการ
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องชื่อผู้ใช้
    st.text_input("U", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องรหัสผ่าน (ไม่มีลูกตา 100% กึ่งกลาง)
    st.text_input("P", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ (ฟ้าเข้ม กึ่งกลาง)
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        if u_id and u_pw:
            st.info("ระบบกำลังตรวจสอบข้อมูล...")
        else:
            st.error("กรุณากรอกข้อมูลให้ครบ")

    # ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-link">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ (สีเขียว กึ่งกลาง)
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.success("กำลังพาไปหน้าสมัครสมาชิก")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:30px;'>Safety First • Traffic Discipline © 2026</p>", unsafe_allow_html=True)
