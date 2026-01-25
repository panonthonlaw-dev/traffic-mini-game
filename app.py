import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- 1. เชื่อมต่อ Google Sheets (ใช้ค่าจาก Secrets) ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
# ใส่ ID ของ Google Sheets ของพี่ตรงนี้
sheet = client.open_by_key("ใส่_ID_ของ_แผ่นงาน_พี่ตรงนี้").sheet1

# --- 2. CSS จัดกึ่งกลาง (แบบครอบคลุม ไม่ต้องใช้ HTML) ---
st.markdown("""
    <style>
    .block-container { max-width: 400px; padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    input { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบสลับหน้า (Login / Signup) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# --- หน้าสมัครสมาชิก ---
if st.session_state.page == 'signup':
    st.markdown("<h1 style='text-align:center; color:#1877f2;'>ลงทะเบียน</h1>", unsafe_allow_html=True)
    
    reg_name = st.text_input("ชื่อ-นามสกุล", placeholder="ภาษาไทยหรืออังกฤษ")
    reg_user = st.text_input("ชื่อผู้ใช้", placeholder="อังกฤษ/ตัวเลข 6-12 ตัว")
    reg_phone = st.text_input("เบอร์โทรศัพท์", placeholder="ตัวเลข 10 หลัก", max_chars=10)
    reg_pass = st.text_input("รหัสผ่าน", type="password", placeholder="6-13 ตัว")
    reg_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")

    if st.button("ลงทะเบียน"):
        # เช็คเงื่อนไขแบบง่ายๆ
        if not reg_name or len(reg_user) < 6 or len(reg_phone) != 10 or reg_pass != reg_confirm:
            st.error("❌ กรุณากรอกข้อมูลให้ถูกต้องตามเงื่อนไข")
        else:
            # เช็คชื่อซ้ำแบบบ้านๆ
            all_users = sheet.col_values(2) # สมมติชื่อผู้ใช้อยู่คอลัมน์ที่ 2
            if reg_user.strip() in all_users:
                st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว!")
            else:
                # --- บันทึกข้อมูล: บรรทัดเดียวจบ! ---
                sheet.append_row([reg_name, reg_user.strip(), reg_phone, reg_pass])
                
                st.success("✅ บันทึกสำเร็จ!")
                st.balloons()
                st.session_state.page = 'login' # สมัครเสร็จเด้งกลับหน้าแรก
                st.rerun()

    if st.button("ยกเลิก"):
        st.session_state.page = 'login'
        st.rerun()

# --- หน้าแรก (Login) ---
else:
    st.markdown("<h1 style='text-align:center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    st.text_input("ชื่อผู้ใช้", key="l_user")
    st.text_input("รหัสผ่าน", type="password", key="l_pass")
    
    if st.button("เข้าสู่ระบบ"):
        st.info("ระบบกำลังตรวจสอบ...")
        
    if st.button("สร้างบัญชีใหม่"):
        st.session_state.page = 'signup'
        st.rerun()
