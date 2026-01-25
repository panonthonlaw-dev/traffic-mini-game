import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. ตั้งค่าแอปและการเชื่อมต่อ (Facebook Style Theme) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS ขั้นสูง: ล้างค่าเก่าที่ทำให้เละ และบังคับสีดำ-ขาว
st.markdown("""
    <style>
        /* 1. พื้นหลังแอปสีเทาอ่อน Facebook */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar/Footer */
        header[data-testid="stHeader"], footer { visibility: hidden; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-top: 2rem; max-width: 450px !important; }

        /* 3. การ์ดสีขาว (Login Box) บังคับพื้นหลังขาว 100% */
        div[data-testid="stVerticalBlock"] > div:has(div.stTabs) {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 8px 16px rgba(0,0,0,0.1) !important;
            border: 1px solid #dddfe2 !important;
        }

        /* 4. แก้ปัญหาช่องกรอกเละ (โดยเฉพาะช่องรหัสผ่าน) */
        input {
            color: #1c1e21 !important; /* ตัวหนังสือดำ */
            background-color: #ffffff !important; /* พื้นหลังขาว */
            border: 1px solid #dddfe2 !important;
            border-radius: 6px !important;
            padding: 14px 16px !important;
            font-size: 17px !important;
        }
        
        /* ลบแถบดำและสีพื้นแปลกๆ ของ Streamlit */
        div[data-baseweb="input"], div[data-baseweb="base-input"] {
            background-color: transparent !important;
            border: none !important;
        }
        
        /* ปรับสี Label ให้ดำเข้ม */
        label, p, span, .stMarkdownContainer p {
            color: #1c1e21 !important;
            font-weight: 500 !important;
        }

        /* 5. ปรับแต่ง Tabs ให้ดูสะอาดเหมือนหมวดหมู่ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #f0f2f5;
            padding: 5px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] p {
            color: #606770 !important;
            font-size: 15px !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {
            color: #1877f2 !important; /* สีฟ้า Facebook */
            font-weight: bold !important;
        }

        /* 6. ปุ่มกดน้ำเงิน Facebook */
        button, .stButton>button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            transition: 0.3s;
        }
        button:hover { background-color: #166fe5 !important; }

        /* ปุ่มเขียว "สมัครสมาชิก" */
        .green-btn button {
            background-color: #42b72a !important;
            font-size: 17px !important;
        }
        .green-btn button:hover { background-color: #36a420 !important; }
        
        /* หัวข้อ traffic game */
        .fb-logo {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
            letter-spacing: -1px;
        }
        .fb-sub {
            color: #1c1e21;
            font-size: 18px;
            text-align: center;
            margin-bottom: 20px;
            line-height: 1.2;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services ---
@st.cache_resource
def init_services():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    s_key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key), create_client(url, s_key)

supabase, supabase_admin = init_services()

# --- 3. ระบบ Logic (เหมือนเดิมแต่แม่นยำขึ้น) ---

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
        return False, "❌ เบอร์โทรต้องมี 10 หลัก (06, 08, 09)"
    return True, ""

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    # ส่วนหัว Facebook Style
    st.markdown("<div class='fb-logo'>traffic game</div>", unsafe_allow_html=True)
    st.markdown("<div class='fb-sub'>บันทึกวินัยจราจรและสะสมแต้มความดีเพื่อรับรางวัล</div>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_id = st.text_input("ชื่อผู้ใช้", placeholder="UserID", key="l_id")
        l_pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password", key="l_pw")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_id), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_u = st.text_input("ตั้ง UserID", key="s_u", placeholder="student01")
        s_p = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_p", placeholder="อังกฤษ/เลข")
        s_n = st.text_input("ชื่อ-นามสกุลจริง")
        s_si = st.text_input("รหัสนักเรียน")
        s_ph = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
        
        st.markdown("<div class='green-btn'>", unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", key="btn_signup"):
            if all([s_u, s_p, s_n, s_si, s_ph]):
                is_v, msg = validate_data(s_u, s_p, s_si, s_ph)
                if not is_v: st.error(msg)
                else:
                    try:
                        res = supabase.auth.sign_up({"email": format_email(s_u), "password": s_p})
                        if res.user:
                            supabase.table("profiles").insert({
                                "id": res.user.id, "username": s_u.lower(), "full_name": s_n, 
                                "student_id": s_si, "phone_number": s_ph, "role": "player", "password_plain": s_p
                            }).execute()
                            st.success("✅ สมัครสำเร็จ! กรุณาไปที่แท็บ 'เข้าสู่ระบบ'")
                    except: st.error("❌ ชื่อนี้มีคนใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_f:
        st.write("ระบุข้อมูลเพื่อยืนยันตัวตน")
        f_u = st.text_input("UserID ของคุณ", key="f_u")
        f_s = st.text_input("รหัสนักเรียน", key="f_s")
        f_p = st.text_input("เบอร์โทรศัพท์", key="f_p")
        f_nw = st.text_input("รหัสผ่านใหม่", type="password", key="f_nw")
        if st.button("เปลี่ยนรหัสผ่าน", key="btn_reset"):
            if all([f_u, f_s, f_p, f_nw]) and re.match("^[a-zA-Z0-9]*$", f_nw):
                try:
                    c = supabase.table("profiles").select("id").eq("username", f_u.lower()).eq("student_id", f_s).eq("phone_number", f_p).single().execute()
                    if c.data:
                        supabase_admin.auth.admin.update_user_by_id(c.data['id'], {"password": f_nw})
                        supabase.table("profiles").update({"password_plain": f_nw}).eq("id", c.data['id']).execute()
                        st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("❌ ข้อมูลไม่ถูกต้อง")
                except: st.error("❌ ไม่พบข้อมูลผู้ใช้")

else:
    # --- หน้า Dashboard หลัง Login ---
    prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{prof['username']}** | {prof['role']}")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    st.title(f"สวัสดีคุณ {prof['username']} 👋")
