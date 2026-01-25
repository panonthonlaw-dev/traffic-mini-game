import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (Fix Visibility & Shadows) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        /* 1. บังคับพื้นหลังขาวและตัวอักษรดำสนิท */
        .stApp {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }

        /* 2. ลบแถบ Header และเมนู */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        footer {visibility: hidden;}

        /* 3. แก้ไขตัวหนังสือในช่องกรอก (Input) ให้เป็นสีดำ */
        input {
            color: #000000 !important;
            background-color: #F9F9F9 !important;
            border: 1px solid #DEDEDE !important;
            border-radius: 8px !important;
            box-shadow: none !important; /* ลบเงาที่เลอะเทอะออก */
        }
        
        /* แก้ไข Label (หัวข้อช่องกรอก) ให้ดำชัดเจน */
        label, .stMarkdown p, .stTabs [data-baseweb="tab"] {
            color: #000000 !important;
            font-weight: 500 !important;
        }

        /* 4. ปรับแต่งปุ่มให้ดูสะอาด (พื้นขาว ขอบเทา ตัวหนังสือดำ) */
        button, .stButton>button {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #CCCCCC !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            height: 45px !important;
            width: 100% !important;
            margin-top: 10px;
        }
        button:hover {
            border-color: #000000 !important;
            background-color: #F0F0F0 !important;
        }

        /* 5. ปรับแต่ง Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #F0F2F6;
            border-radius: 10px;
            padding: 5px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #FFFFFF !important;
            border-radius: 7px;
        }

        /* จัดหน้าจอให้กึ่งกลางและไม่กว้างเกินไป */
        .block-container {
            max-width: 450px !important;
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. เชื่อมต่อ Services (เหมือนเดิม) ---
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

# --- 3. ฟังก์ชันการทำงาน ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_signup_data(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "❌ UserID ต้องเป็นอังกฤษ/เลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    if not s_id.isdigit():
        return False, "❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "❌ เบอร์โทรต้องมี 10 หลัก (06, 08, 09)"
    return True, ""

# --- 4. หน้าจอ UI ---

if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: black;'>Traffic Mini Game</h2>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้ (UserID)", key="login_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("ตกลง เข้าสู่ระบบ"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID", placeholder="เช่น student01", key="reg_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="reg_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์")
        if st.button("สมัครสมาชิก"):
            if all([s_uid, s_pw, s_name, s_sid, s_phone]):
                valid, msg = validate_signup_data(s_uid, s_pw, s_sid, s_phone)
                if not valid: st.error(msg)
                else:
                    try:
                        res = supabase.auth.sign_up({"email": format_email(s_uid), "password": s_pw})
                        if res.user:
                            supabase.table("profiles").insert({
                                "id": res.user.id, "username": s_uid.lower(), "full_name": s_name, 
                                "student_id": s_sid, "phone_number": s_phone, "role": "player",
                                "password_plain": s_pw
                            }).execute()
                            st.success("✅ สมัครสำเร็จ! กลับไปที่หน้า Login")
                    except: st.error("❌ ชื่อนี้ถูกใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")

    with tab_f:
        st.write("ระบุข้อมูลเพื่อตั้งรหัสใหม่")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทร", key="f_phone")
        f_newpw = st.text_input("รหัสใหม่", type="password", key="f_newpw")
        if st.button("รีเซ็ตรหัสผ่าน"):
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
    # --- เมื่อ Login สำเร็จ ---
    prof_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    prof = prof_res.data
    username = prof.get('username', 'User')
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{username}**")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    # (โค้ดหน้า Admin/Player ตามเวอร์ชันก่อนหน้า)
