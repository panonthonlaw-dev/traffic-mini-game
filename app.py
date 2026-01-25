import streamlit as st

# --- 1. ตั้งค่าแอป ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# --- 2. CSS ชุดถล่มลูกตา (ฆ่าปุ่ม Show Password ถาวร) ---
st.markdown("""
    <style>
        /* บังคับพื้นหลังเทา */
        .stApp { background-color: #f0f2f5 !important; }

        /* ซ่อนส่วนเกิน Streamlit */
        header, footer { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        
        /* จัดกึ่งกลางหน้าจอ */
        .block-container {
            max-width: 400px !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-top: 5rem !important;
        }

        /* กล่องขาวขอบมน */
        div[data-testid="stVerticalBlock"] > div:has(div.login-card) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            border: 1px solid #dddfe2 !important;
            width: 100%;
        }

        /* ------------------------------------------- */
        /* จุดสำคัญ: สั่งลบ "ลูกตา" และกล่องว่างด้านบน  */
        /* ------------------------------------------- */
        
        /* 1. ลบปุ่มลูกตาดูรหัสผ่าน ทุกกรณี */
        button[aria-label="Show password"], 
        button[title="Show password"],
        .stTextInput div[data-baseweb="input"] button {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        /* 2. ลบกล่องว่าง/Label เหนือช่องกรอก (ไอ้ที่ทำให้เละ) */
        div[data-testid="stWidgetLabel"] {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
        }
        
        /* 3. ปรับช่อง Input ให้ขยับมาชิดกันและตัวหนังสือดำ */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            text-align: center !important;
            height: 45px !important;
        }

        /* ------------------------------------------- */

        /* ปุ่มเข้าสู่ระบบ สีฟ้าเข้ม */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            font-weight: bold !important;
            width: 100% !important;
            border-radius: 8px !important;
            height: 50px !important;
            border: none !important;
            margin-top: 10px;
        }

        /* ปุ่มสร้างบัญชี สีเขียว */
        .signup-area div.stButton > button {
            background-color: #42b72a !important;
            width: auto !important;
            padding: 0 20px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ส่วนแสดงผล UI ---

# หัวข้อ (กึ่งกลาง)
st.markdown("<h1 style='color:#1877f2; text-align:center; font-size:50px; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#000000; text-align:center; font-size:20px; margin-top:-10px; margin-bottom:20px;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)

# กล่องขาว
with st.container():
    st.markdown('<div class="login-card"></div>', unsafe_allow_html=True)
    
    # ช่องชื่อผู้ใช้
    st.text_input("U", placeholder="ชื่อผู้ใช้", label_visibility="collapsed", key="u_id")
    
    # ช่องรหัสผ่าน (ไม่มีลูกตาแน่นอน)
    st.text_input("P", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed", key="u_pw")
    
    # ปุ่มเข้าสู่ระบบ
    st.button("เข้าสู่ระบบ")
    
    st.markdown("<p style='text-align:center; color:#1877f2; font-size:14px; margin:15px 0;'>ลืมรหัสผ่านใช่หรือไม่?</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top:1px solid #dddfe2; margin:20px 0;'>", unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชี
    st.markdown('<div class="signup-area">', unsafe_allow_html=True)
    st.button("สร้างบัญชีใหม่")
    st.markdown('</div>', unsafe_allow_html=True)
