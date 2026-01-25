import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอปและการเชื่อมต่อ ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# CSS ขั้นสูง: บังคับทุกอย่างเป็นสีขาวและปุ่มสีขาว
st.markdown("""
    <style>
        /* 1. บังคับพื้นหลังแอปเป็นสีขาว */
        .stApp {
            background-color: white !important;
            color: black !important;
        }

        /* 2. ซ่อนแถบด้านบนและเมนูข้าง */
        header[data-testid="stHeader"] { visibility: hidden; height: 0%; }
        section[data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        
        /* 3. จัดการ "ทุกปุ่ม" ให้เป็นพื้นหลังขาว ตัวอักษรดำ */
        button, .stButton>button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #cccccc !important;
            border-radius: 10px !important;
            height: 3em !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }

        /* เอฟเฟกต์ตอนเอาเมาส์ไปวางบนปุ่ม (Hover) */
        button:hover, .stButton>button:hover {
            background-color: #f0f2f6 !important;
            border: 1px solid #999999 !important;
        }

        /* 4. ปรับสีตัวอักษรของ Header และข้อความต่างๆ */
        h1, h2, h3, p, span, label, .stMarkdownContainer p {
            color: black !important;
        }

        /* 5. ปรับสีช่องกรอกข้อมูล (Input) */
        .stTextInput>div>div>input {
            background-color: #ffffff !important;
            color: black !important;
            border: 1px solid #dddddd !important;
            border-radius: 8px !important;
        }

        /* 6. ปรับระยะขอบหน้าจอให้พอดีมือถือ */
        .block-container {
            padding-top: 2rem;
            max-width: 450px;
        }

        /* ปรับสี Tabs ให้เป็นโทนเทา-ดำ */
        .stTabs [data-baseweb="tab-list"] button {
            color: #888888 !important;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: black !important;
            border-bottom-color: black !important;
        }
    </style>
""", unsafe_allow_html=True)

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

# --- 2. ฟังก์ชันระบบ (Logic) ---

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

# --- 3. ส่วน Authentication UI ---

if 'user' not in st.session_state:
    st.title("🚦 มินิเกมจราจร")
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("UserID", key="login_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID", key="reg_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="reg_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์")
        if st.button("ยืนยันการสมัคร", key="btn_signup"):
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
                            st.success("✅ สมัครสำเร็จ!")
                    except: st.error("❌ ชื่อนี้อาจถูกใช้ไปแล้ว")

    with tab_f:
        st.subheader("กู้คืนรหัสผ่าน")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทร", key="f_phone")
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
                except: st.error("❌ ไม่พบข้อมูล")

else:
    # --- เมื่อ Login สำเร็จ ---
    prof_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    prof = prof_res.data
    username = prof.get('username', 'User')
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.write(f"👤 **{username}**")
    if col_o.button("Logout", key="btn_logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()

    if st.session_state.role == "admin":
        st.title("🛠️ แอดมิน")
        # ส่วนแอดมิน...
    else:
        st.title(f"สวัสดีคุณ {username} 👋")
        c1, c2 = st.columns(2)
        c1.metric("🪙 คะแนน", prof.get('total_points', 0))
        c2.metric("🎖️ ระดับ", prof.get('rank_title', 'ผู้เริ่มต้น'))

        st.divider()
        task_res = supabase.table("daily_tasks").select("*").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        if task_res.data:
            t = task_res.data[0]
            st.info(f"🚩 **ภารกิจ:** {t['task_name']}\n\n{t['task_description']}")
            img = st.camera_input("📸 ถ่ายรูปส่งงาน")
            if img:
                if st.button("ส่งงานตรวจสอบ", key="btn_submit"):
                    with st.spinner("กำลังส่งงาน..."):
                        d_id = upload_to_drive(img, username)
                        if d_id:
                            supabase.table("missions").insert({"user_id": st.session_state.user.id, "image_drive_id": d_id, "mission_name": t['task_name']}).execute()
                            st.success("ส่งเรียบร้อย!")
