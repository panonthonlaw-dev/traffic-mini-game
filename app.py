import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (Modern UI Config) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS ขั้นสูงสำหรับ Modern Light Theme
st.markdown("""
    <style>
        /* บังคับพื้นหลังขาวสะอาด */
        .stApp {
            background-color: #ffffff !important;
        }

        /* ซ่อนส่วนเกินของ Streamlit */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        footer {visibility: hidden;}

        /* สร้างกรอบ Card ให้กับหน้าจอ Login */
        .block-container {
            max-width: 450px !important;
            padding-top: 3rem !important;
        }

        /* ตกแต่ง Tabs ให้ดูทันสมัย */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #f8f9fa;
            padding: 8px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            border-radius: 10px;
            background-color: transparent;
            border: none;
            color: #888;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: white !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            color: black !important;
            font-weight: bold;
        }

        /* ตกแต่งช่องกรอกข้อมูล (Input) */
        .stTextInput input {
            background-color: #fdfdfd !important;
            border: 1px solid #eeeeee !important;
            border-radius: 12px !important;
            padding: 12px !important;
            color: black !important;
        }
        .stTextInput input:focus {
            border-color: #cccccc !important;
            box-shadow: 0 0 0 1px #cccccc !important;
        }

        /* ตกแต่ง "ทุกปุ่ม" ให้เป็นสีขาวพรีเมียม */
        button, .stButton>button {
            background-color: #ffffff !important;
            color: #222222 !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        button:hover, .stButton>button:hover {
            border-color: #999999 !important;
            background-color: #fafafa !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        /* จัดการหัวข้อ */
        h1 {
            font-weight: 800 !important;
            color: #111111 !important;
            text-align: center;
            margin-bottom: 5px !important;
        }
        .sub-text {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 30px;
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

# --- 3. ฟังก์ชันการทำงาน (Logic) ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_signup_data(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "❌ UserID ต้องเป็นภาษาอังกฤษ/ตัวเลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    if not s_id.isdigit():
        return False, "❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "❌ เบอร์โทรต้องมี 10 หลัก และขึ้นต้นด้วย 06, 08 หรือ 09"
    return True, ""

def upload_to_drive(file, user_id):
    try:
        drive_service = init_drive()
        folder_id = st.secrets["GDRIVE_FOLDER_ID"]
        img = Image.open(file).convert("RGB")
        img.thumbnail((1024, 1024))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        file_metadata = {'name': f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg", 'parents': [folder_id]}
        media = MediaIoBaseUpload(img_byte_arr, mimetype='image/jpeg', resumable=True)
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return uploaded_file.get('id')
    except: return None

# --- 4. ส่วนแสดงผล UI ---

if 'user' not in st.session_state:
    st.markdown("<h1>Traffic Mini Game</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-text'>ระบบสะสมคะแนนวินัยจราจร</p>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔐 Login", "📝 Signup", "🔑 Forgot"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้", placeholder="UserID", key="login_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password", key="login_pass")
        st.write("") # เว้นวรรค
        if st.button("เข้าสู่ระบบ"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID", placeholder="เช่น somchai01", key="reg_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", placeholder="A-Z, 0-9", key="reg_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง", placeholder="นายสมชาย ใจดี")
        s_sid = st.text_input("รหัสนักเรียน", placeholder="ตัวเลขเท่านั้น")
        s_phone = st.text_input("เบอร์โทรศัพท์", placeholder="08XXXXXXXX")
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
                            st.success("✅ สมัครสำเร็จ! กลับไปที่หน้า Login ได้เลย")
                    except: st.error("❌ ชื่อนี้ถูกใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")

    with tab_f:
        st.markdown("### กู้คืนบัญชี")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทรศัพท์", key="f_phone")
        f_newpw = st.text_input("รหัสผ่านใหม่", type="password", key="f_newpw")
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
    # โค้ดส่วนหน้า Dashboard (Admin/Player) ใส่ต่อจากตรงนี้ได้เลยครับ...
    prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    username = prof.data.get('username', 'User')
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{username}**")
    if col_o.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    # (โค้ดหน้าหลัก Admin/Player ตามเวอร์ชันก่อนหน้า)
