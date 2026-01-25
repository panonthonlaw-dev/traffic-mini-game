import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. ตั้งค่าแอป (Modern UI Config) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS ขั้นสูง: ลบเงาที่เลอะเทอะ บังคับพื้นหลังขาว และตัวหนังสือดำสนิท
st.markdown("""
    <style>
        /* 1. บังคับสีพื้นหลังแอป (สีเทาอ่อน Facebook) */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer ของ Streamlit */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดการการ์ดสีขาว (Login Box) */
        .block-container {
            max-width: 420px !important;
            padding-top: 2rem !important;
        }
        
        /* บังคับกล่อง Tabs ให้เป็นสีขาว 100% และลบเงาดำที่เลอะออก */
        div[data-testid="stVerticalBlock"] > div:has(div.stTabs) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #dddfe2 !important;
        }

        /* 4. **แก้ปัญหาช่องกรอกรหัสผ่านดำ/เละ** */
        /* บังคับทุกส่วนของ Input ให้เป็นสีขาวและตัวหนังสือดำ */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 6px !important;
            padding: 12px !important;
            font-size: 16px !important;
        }

        /* เจาะจงแก้ปัญหาพื้นหลังดำในช่องรหัสผ่านของ Streamlit */
        div[data-baseweb="input"], div[data-baseweb="base-input"], .stTextInput div {
            background-color: transparent !important;
            border: none !important;
        }

        /* 5. บังคับตัวหนังสือทุกจุดเป็นสีดำเข้ม */
        h1, h2, h3, p, span, label, .stMarkdown p {
            color: #1c1e21 !important;
            font-weight: 500 !important;
            text-shadow: none !important;
        }

        /* 6. ตกแต่ง Tabs (หมวดหมู่) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #f0f2f5;
            padding: 5px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] p {
            color: #606770 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {
            color: #1877f2 !important;
            font-weight: bold !important;
        }

        /* 7. ปุ่มกด (น้ำเงิน/เขียว Facebook) */
        button, .stButton > button {
            width: 100% !important;
            border-radius: 6px !important;
            font-size: 19px !important;
            font-weight: bold !important;
            height: 48px !important;
            border: none !important;
            transition: 0.2s;
        }
        /* ปุ่มเข้าสู่ระบบ/รีเซ็ต (น้ำเงิน) */
        .stButton > button {
            background-color: #1877f2 !important;
            color: white !important;
        }
        /* ปุ่มสมัครสมาชิก (เขียว) - ใช้ช่องว่างล่างสุด */
        .green-btn button {
            background-color: #42b72a !important;
            color: white !important;
            margin-top: 10px;
        }

        /* หัวข้อ traffic game */
        .fb-logo {
            color: #1877f2;
            font-size: 45px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
            font-family: Arial, sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services (Supabase) ---
@st.cache_resource
def init_services():
    url, key, s_key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"], st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key), create_client(url, s_key)

supabase, supabase_admin = init_services()

# --- 3. ระบบ Logic ตรวจสอบความถูกต้อง ---
def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_data(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "❌ UserID ต้องเป็นอังกฤษ/เลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    if not s_id.isdigit():
        return False, "❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "❌ เบอร์โทรต้องมี 10 หลัก (ขึ้นต้น 06, 08, 09)"
    return True, ""

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    st.markdown("<div class='fb-logo'>traffic game</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>บันทึกวินัยจราจรและสะสมแต้มความดี</p>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้", placeholder="UserID", key="l_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password", key="l_pw")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID", placeholder="เช่น student01", key="s_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", placeholder="อังกฤษ/เลขเท่านั้น", key="s_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
        
        st.markdown("<div class='green-btn'>", unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", key="btn_signup"):
            if all([s_uid, s_pw, s_name, s_sid, s_phone]):
                is_v, msg = validate_data(s_uid, s_pw, s_sid, s_phone)
                if not is_v: st.error(msg)
                else:
                    try:
                        res = supabase.auth.sign_up({"email": format_email(s_uid), "password": s_pw})
                        if res.user:
                            supabase.table("profiles").insert({
                                "id": res.user.id, "username": s_uid.lower(), "full_name": s_name, 
                                "student_id": s_sid, "phone_number": s_phone, "role": "player", "password_plain": s_pw
                            }).execute()
                            st.success("✅ สมัครสำเร็จ! กลับไปที่หน้า 'เข้าสู่ระบบ'")
                    except: st.error("❌ ชื่อนี้มีคนใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_f:
        st.markdown("### กู้คืนบัญชี")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทรศัพท์", key="f_phone")
        f_newpw = st.text_input("รหัสผ่านใหม่", type="password", key="f_newpw")
        if st.button("รีเซ็ตรหัสผ่าน", key="btn_reset"):
            if all([f_uid, f_sid, f_phone, f_newpw]) and re.match("^[a-zA-Z0-9]*$", f_newpw):
                try:
                    check = supabase.table("profiles").select("id").eq("username", f_uid.lower()).eq("student_id", f_sid).eq("phone_number", f_phone).single().execute()
                    if check.data:
                        supabase_admin.auth.admin.update_user_by_id(check.data['id'], {"password": f_newpw})
                        supabase.table("profiles").update({"password_plain": f_newpw}).eq("id", check.data['id']).execute()
                        st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("❌ ข้อมูลไม่ถูกต้อง")
                except: st.error("❌ ไม่พบข้อมูลผู้ใช้")

else:
    # --- หน้า Dashboard (ส่วนที่ Login แล้ว) ---
    prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{prof['username']}** | {prof['role']}")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    st.title(f"สวัสดีคุณ {prof['username']} 👋")
