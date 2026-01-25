import streamlit as st

# --- 1. ตั้งค่าหน้ากระดาษ ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ขั้นเทพ (บังคับเป๊ะ 100% ไม่สนระบบเดิม) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อนแบบ Facebook */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ลบ Header/Sidebar/Footer ออกให้หมด */
        header, footer, [data-testid="stSidebar"] { display: none !important; }
        
        /* 3. จัดการ Layout ให้กึ่งกลาง */
        .block-container {
            max-width: 400px !important;
            padding-top: 5rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 4. หัวข้อหลัก (สีฟ้าเข้ม) */
        .main-logo {
            color: #1877f2 !important;
            font-size: 50px !important;
            font-weight: bold !important;
            font-family: Arial, sans-serif !important;
            letter-spacing: -2px !important;
            margin: 0 !important;
        }
        
        /* 5. หัวข้อรอง (สีดำ) */
        .sub-logo {
            color: #000000 !important;
            font-size: 20px !important;
            font-weight: 500 !important;
            margin-top: -10px !important;
            margin-bottom: 25px !important;
        }

      
        }

        /* 7. ช่องกรอกข้อมูล (Inputs) - บังคับสีดำ-ขาว */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 14px !important;
            font-size: 16px !important;
            text-align: center !important;
        }
        ::placeholder { color: #8d949e !important; }

        /* 8. **ลบกล่องว่างประหลาด (Label) ออกถาวร** */
        [data-testid="stWidgetLabel"] {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
        }
        .stTextInput { margin-top: -15px !important; margin-bottom: 10px !important; }

        /* 9. **ฆ่าปุ่มลูกตา (Show password) ให้หายสาบสูญ** */
        button[aria-label="Show password"], 
        .stTextInput div[data-baseweb="input"] button {
            display: none !important;
            visibility: hidden !important;
        }

        /* 10. ปุ่มเข้าสู่ระบบ (สีฟ้าเข้ม) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            margin-top: 10px !important;
        }

        /* 11. ลืมรหัสผ่าน */
        .forgot-link {
            color: #1877f2 !important;
            font-size: 14px !important;
            text-decoration: none !important;
            display: block;
            margin: 15px 0;
            text-align: center;
        }

        /* 12. เส้นคั่นบางๆ */
        .divider {
            border-bottom: 1px solid #dddfe2;
            margin: 20px 0;
            width: 100%;
        }

        /* 13. ปุ่มสร้างบัญชีใหม่ (สีเขียว) */
        .signup-container div.stButton > button {
            background-color: #42b72a !important;
            color: #ffffff !important;
            width: auto !important;
            padding: 0 30px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. การแสดงผล UI ---

# Header ด้านบน
st.markdown('<p class="main-logo">traffic game</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-logo">เล่นเปลี่ยนรอด</p>', unsafe_allow_html=True)

# กล่องขาว
with st.container():
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องชื่อผู้ใช้
    st.text_input("U", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องรหัสผ่าน (ไม่มีลูกตา 100%)
    st.text_input("P", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    if st.button("เข้าสู่ระบบ", key="btn_login"):
        st.info("ระบบกำลังตรวจสอบ...")

    # ลืมรหัสผ่าน
    st.markdown('<a href="#" class="forgot-link">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
    
    # เส้นคั่น
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่
    st.markdown('<div class="signup-container">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", key="btn_signup"):
        st.success("ไปหน้าสมัครสมาชิก")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:30px;'>Traffic Mini Game © 2026</p>", unsafe_allow_html=True) 
