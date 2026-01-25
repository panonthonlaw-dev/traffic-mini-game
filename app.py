import streamlit as st

# --- 1. ตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ขั้นสูง (เน้นความเนียน 100% ลบขอบดำเลอะเทอะ) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อนสะอาดตา */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อนส่วนเกิน Streamlit */
        header, footer { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        
        /* 3. จัดกึ่งกลางหน้าจอแบบเป๊ะๆ */
        .block-container {
            max-width: 400px !important;
            padding-top: 5rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 4. กล่องขาวพรีเมียม (ลบขอบดำ/เงาที่เลอะออก) */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card-anchor) {
            background-color: #ffffff !important;
            padding: 35px !important;
            border-radius: 12px !important;
            /* ใช้เงาจางๆ สีเทา ไม่เอาสีดำหนา */
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 5. จัดการช่องกรอกให้เนียน (ลบขอบดำตอนกด) */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            text-align: center !important;
            height: 48px !important;
            font-size: 16px !important;
            outline: none !important; /* ลบขอบดำตอนกด */
            box-shadow: none !important; /* ลบเงาที่ทำให้ดูเละ */
        }
        input:focus {
            border: 1px solid #1877f2 !important; /* เปลี่ยนเป็นสีน้ำเงินบางๆ ตอนกด */
        }

        /* 6. **ทำลายลูกตาถาวร** */
        button[aria-label="Show password"] {
            display: none !important;
        }
        /* แก้ไขช่องรหัสผ่านไม่ให้มีพื้นที่ว่างของลูกตา */
        div[data-baseweb="input"] {
            background-color: transparent !important;
            border: none !important;
        }

        /* 7. ลบ "กล่องว่าง" (Label) เหนือช่องกรอกออก 100% */
        div[data-testid="stWidgetLabel"] {
            display: none !important;
        }
        .stTextInput {
            margin-top: -20px !important; /* บีบช่องว่างให้หายไป */
            margin-bottom: 10px !important;
        }

        /* 8. ปุ่มเข้าสู่ระบบ (กึ่งกลาง - เนียน) */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            font-weight: bold !important;
            font-size: 18px !important;
            width: 100% !important;
            border-radius: 8px !important;
            height: 50px !important;
            border: none !important;
            margin-top: 15px !important;
        }

        /* 9. ปุ่มสร้างบัญชี (สีเขียว - กึ่งกลาง) */
        .signup-area div.stButton > button {
            background-color: #42b72a !important;
            width: auto !important;
            padding: 0 30px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
        /* ปรับสีตัวหนังสือให้ดำชัด */
        p, span, div {
            color: #000000;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ส่วนการแสดงผล (UI) ---

# หัวข้อ (กึ่งกลางเป๊ะ)
st.markdown("<h1 style='color:#1877f2; text-align:center; font-size:55px; font-weight:bold; font-family:Arial; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#000000; text-align:center; font-size:22px; font-weight:500; margin-top:-10px; margin-bottom:30px;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)

# เริ่มกล่องขาว
with st.container():
    st.markdown('<div class="login-card-anchor"></div>', unsafe_allow_html=True)
    
    # ช่องชื่อผู้ใช้
    st.text_input("U", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องรหัสผ่าน (ไร้ลูกตา ไร้ขอบดำ)
    st.text_input("P", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    st.button("เข้าสู่ระบบ")
    
    # ลิงก์ลืมรหัสผ่าน
    st.markdown("<p style='text-align:center; margin:15px 0;'><a href='#' style='color:#1877f2; text-decoration:none; font-size:14px;'>ลืมรหัสผ่านใช่หรือไม่?</a></p>", unsafe_allow_html=True)
    
    # เส้นคั่นบางๆ (เนียน)
    st.markdown("<hr style='border: 0; border-top: 1px solid #dddfe2; margin: 20px 0;'>", unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชี
    st.markdown('<div class="signup-area">', unsafe_allow_html=True)
    st.button("สร้างบัญชีใหม่")
    st.markdown('</div>', unsafe_allow_html=True)

# ข้อความท้าย
st.markdown("<p style='text-align:center; color:#606770; font-size:12px; margin-top:30px;'>Traffic Discipline Management</p>", unsafe_allow_html=True)
