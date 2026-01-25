import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (High Contrast Facebook Theme) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        /* 1. พื้นหลังสีเทาอมฟ้า */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        footer {visibility: hidden;}

        /* 3. การ์ดสีขาว (Login Box) */
        .block-container {
            max-width: 420px !important;
            padding-top: 2rem !important;
        }
        
        [data-testid="stVerticalBlock"] > div:has(div.stTabs) {
            background-color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        /* 4. **แก้ไขสีตัวอักษรหมวดหมู่ (Tabs)** */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #e4e6eb; /* พื้นหลัง Tab Bar เข้มขึ้น */
            padding: 5px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] p {
            color: #4b4f56 !important; /* สีเทาเข้มสำหรับ Tab ที่ไม่ได้เลือก */
            font-size: 16px !important;
            font-weight: 600 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {
            color: #1877f2 !important; /* สีน้ำเงินเด่นสำหรับ Tab ที่เลือก */
        }

        /* 5. **บังคับตัวหนังสือทุกจุดเป็นสีดำ** */
        h1, h2, h3, p, span, label, .stMarkdown p {
            color: #000000 !important;
            font-weight: 600 !important;
        }

        /* 6. ตกแต่งช่องกรอกข้อมูล */
        input {
            color: black !important;
            background-color: #ffffff !important;
            border: 1px solid #ccd0d5 !important;
            border-radius: 8px !important;
            padding: 12px !important;
        }
        input:focus {
            border-color: #1877f2 !important;
            box-shadow: 0 0 0 2px #e7f3ff !important;
        }

        /* 7. ปุ่มกด (Facebook Style) */
        button, .stButton > button {
            width: 100% !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 50px !important;
            transition: 0.3s;
            border: none !important;
        }
        /* ปุ่มน้ำเงิน */
        div.stButton > button {
            background-color: #1877f2 !important;
            color: white !important;
        }
        div.stButton > button:hover {
            background-color: #166fe5 !important;
        }
        
        /* เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services (ใช้ค่าจาก Secrets) ---
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

# --- 3. ฟังก์ชันระบบ ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_signup(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "UserID ต้องเป็นอังกฤษ/เลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "รหัสผ่านต้องเป็นอังกฤษ/เลขเท่านั้น"
    if not s_id.isdigit():
        return False, "รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "เบอร์โทรต้องมี 10 หลัก (ขึ้นต้น 06,08,09)"
    return True, ""

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #1877f2 !important; font-size: 42px;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #1c1e21 !important; margin-bottom: 20px;'>บันทึกวินัยจราจรและสะสมแต้มความดี</p>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก", "ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้ (UserID)", key="l_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="l_pw")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID", key="s_uid", placeholder="อังกฤษ/เลข 6 ตัวขึ้นไป")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw", placeholder="อังกฤษ/เลขเท่านั้น")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์", placeholder="06XXXXXXXX")
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
                            st.success("สมัครสำเร็จ! กรุณาไปที่แท็บ 'เข้าสู่ระบบ'")
                    except: st.error("ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")

    with tab_f:
        st.markdown("### กู้คืนรหัสผ่าน")
        f_uid = st.text_input("UserID ของคุณ", key="f_uid")
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
                        st.success("เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("ข้อมูลไม่ถูกต้อง")
                except: st.error("ไม่พบข้อมูลผู้ใช้งาน")

else:
    # --- หน้าจอหลัง Login ---
    prof_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    prof = prof_res.data
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{prof['username']}** | {prof['role']}")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    if st.session_state.role == "admin":
        st.title("🛠️ แผงควบคุมแอดมิน")
    else:
        st.title(f"สวัสดีคุณ {prof['username']} 👋")
        # โค้ดส่วนอื่นๆ ของผู้เล่น...
