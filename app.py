import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (Modern Facebook UI) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        /* 1. พื้นหลังเทาอ่อนแบบ Facebook และตัวหนังสือดำสนิท */
        .stApp {
            background-color: #f0f2f5 !important;
            color: #000000 !important;
        }

        /* 2. ซ่อน Header/Sidebar ของ Streamlit */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        footer {visibility: hidden;}

        /* 3. ปรับแต่งการ์ดสีขาว (Login Box) */
        .block-container {
            max-width: 420px !important;
            padding-top: 2rem !important;
        }
        
        /* ทำให้ Tabs ดูเหมือนเป็นการ์ดใบเดียว */
        .stTabs {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        }

        /* 4. ปรับแต่งช่องกรอกข้อมูล (Inputs) ให้สะอาดตา */
        input {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 6px !important;
            padding: 12px !important;
            font-size: 16px !important;
        }
        input:focus {
            border-color: #1877f2 !important;
            box-shadow: 0 0 0 2px #e7f3ff !important;
        }
        
        /* แก้ไข Label และหัวข้อต่างๆ ให้ดำชัดเจน */
        label, .stMarkdown p, h1, h2, h3 {
            color: #1c1e21 !important;
            font-weight: 600 !important;
            text-shadow: none !important;
        }

        /* 5. ปรับแต่ง Tabs (หมวดหมู่) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #f0f2f5;
            padding: 5px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .stTabs [data-baseweb="tab"] p {
            color: #606770 !important;
            font-size: 15px !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {
            color: #1877f2 !important;
            font-weight: bold !important;
        }

        /* 6. ปุ่มกด (น้ำเงิน Facebook) */
        button, .stButton > button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            transition: 0.2s;
        }
        button:hover {
            background-color: #166fe5 !important;
            box-shadow: 0 4px 12px rgba(24, 119, 242, 0.3) !important;
        }
        
        /* ปุ่มสมัครสมาชิก (สีเขียว) */
        div[key="btn_signup"] button {
            background-color: #42b72a !important;
        }
        div[key="btn_signup"] button:hover {
            background-color: #36a420 !important;
        }

        /* 7. เส้นคั่นและระยะห่าง */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    service_key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key), create_client(url, service_key)

supabase, supabase_admin = init_supabase()

def init_drive():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

# --- 3. ฟังก์ชันระบบ (Logic) ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_signup(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "❌ UserID ต้องเป็นภาษาอังกฤษ/ตัวเลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    if not s_id.isdigit():
        return False, "❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "❌ เบอร์โทรต้องมี 10 หลัก และขึ้นต้นด้วย 06, 08 หรือ 09"
    return True, ""

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    # ส่วนหัวโลโก้
    st.markdown("<h1 style='text-align: center; color: #1877f2 !important; font-size: 48px; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #1c1e21 !important; font-size: 18px; margin-bottom: 20px;'>บันทึกวินัยจราจรและสะสมแต้มความดี</p>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔒 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้", key="l_uid", placeholder="UserID")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="l_pw", placeholder="Password")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้งชื่อผู้ใช้", key="s_uid", placeholder="อังกฤษ/เลข 6 ตัวขึ้นไป")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw", placeholder="อังกฤษ/เลขเท่านั้น")
        s_name = st.text_input("ชื่อ-นามสกุลจริง", placeholder="นายสมชาย ใจดี")
        s_sid = st.text_input("รหัสนักเรียน", placeholder="ตัวเลขเท่านั้น")
        s_phone = st.text_input("เบอร์โทรศัพท์", placeholder="08XXXXXXXX")
        
        # ใช้ container เพื่อจัดสีปุ่มสมัครสมาชิกเป็นสีเขียว
        if st.button("สมัครบัญชีใหม่", key="btn_signup"):
            if all([s_uid, s_pw, s_name, s_sid, s_phone]):
                is_valid, msg = validate_signup(s_uid, s_pw, s_sid, s_phone)
                if not is_valid: st.error(msg)
                else:
                    try:
                        res = supabase.auth.sign_up({"email": format_email(s_uid), "password": s_pw})
                        if res.user:
                            supabase.table("profiles").insert({
                                "id": res.user.id, "username": s_uid.lower(), "full_name": s_name, 
                                "student_id": s_sid, "phone_number": s_phone, "role": "player",
                                "password_plain": s_pw
                            }).execute()
                            st.success("✅ สมัครสำเร็จ! กลับไปที่หน้า 'เข้าสู่ระบบ'")
                    except: st.error("❌ ชื่อนี้ถูกใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

    with tab_f:
        st.markdown("### กู้คืนบัญชี")
        f_uid = st.text_input("UserID ของคุณ", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทรศัพท์", key="f_phone")
        f_newpw = st.text_input("ตั้งรหัสผ่านใหม่", type="password", key="f_newpw")
        if st.button("รีเซ็ตรหัสผ่าน", key="btn_reset"):
            if all([f_uid, f_sid, f_phone, f_newpw]) and re.match("^[a-zA-Z0-9]*$", f_newpw):
                try:
                    check = supabase.table("profiles").select("id").eq("username", f_uid.lower()).eq("student_id", f_sid).eq("phone_number", f_phone).single().execute()
                    if check.data:
                        supabase_admin.auth.admin.update_user_by_id(check.data['id'], {"password": f_newpw})
                        supabase.table("profiles").update({"password_plain": f_newpw}).eq("id", check.data['id']).execute()
                        st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("❌ ข้อมูลไม่ถูกต้อง")
                except: st.error("❌ ไม่พบข้อมูลผู้ใช้งาน")

else:
    # --- หน้าจอหลัง Login ---
    prof_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    prof = prof_res.data
    
    # ส่วนหัว Dashboard
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{prof['username']}** | {prof['role']}")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    st.title(f"สวัสดีคุณ {prof['username']} 👋")
    # (โค้ดส่วน Dashboard อื่นๆ...)
