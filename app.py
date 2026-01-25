import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (Facebook Style Theme) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        /* 1. พื้นหลังสีเทาอมฟ้าแบบ Facebook */
        .stApp {
            background-color: #f0f2f5 !important;
        }

        /* 2. ซ่อน Header/Sidebar */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        footer {visibility: hidden;}

        /* 3. ปรับขนาดหน้าจอให้เหมือน Mobile Card */
        .block-container {
            max-width: 420px !important;
            padding-top: 2rem !important;
        }

        /* 4. ตกแต่งหัวข้อโลโก้ */
        .fb-logo {
            color: #1877f2;
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            font-family: Arial, sans-serif;
            margin-bottom: 5px;
        }
        .fb-sub {
            color: #1c1e21;
            font-size: 18px;
            text-align: center;
            margin-bottom: 25px;
            line-height: 1.2;
        }

        /* 5. ตกแต่งการ์ดขาว (Login Box) */
        [data-testid="stVerticalBlock"] > div:has(div.stTabs) {
            background-color: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1);
        }

        /* 6. ตกแต่งช่องกรอกข้อมูล */
        input {
            color: black !important;
            background-color: white !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 6px !important;
            padding: 12px !important;
            font-size: 16px !important;
        }
        input:focus {
            border-color: #1877f2 !important;
            box-shadow: 0 0 0 2px #e7f3ff !important;
        }
        label { color: #1c1e21 !important; font-weight: 500 !important; }

        /* 7. ปุ่ม "เข้าสู่ระบบ" (น้ำเงิน Facebook) */
        .stButton > button {
            width: 100% !important;
            border-radius: 6px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            height: 48px !important;
            transition: 0.3s;
        }
        
        /* เฉพาะปุ่มหลัก (Login / Reset) */
        div.stButton > button:first-child {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
        }
        div.stButton > button:first-child:hover {
            background-color: #166fe5 !important;
        }

        /* 8. ปุ่ม "สร้างบัญชีใหม่" (เขียว Facebook) */
        /* เราจะใช้ CSS คัดกรองผ่าน Key ของปุ่ม */
        div[data-testid="stForm"] div.stButton > button, 
        button[kind="secondaryFormSubmit"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-size: 17px !important;
            width: auto !important;
            margin: 0 auto !important;
            display: block !important;
        }

        /* 9. ลิงก์ลืมรหัสผ่าน */
        .forgot-link {
            display: block;
            text-align: center;
            color: #1877f2;
            text-decoration: none;
            font-size: 14px;
            margin-top: 15px;
        }

        /* 10. เส้นคั่น */
        .divider {
            border-bottom: 1px solid #dadde1;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services (Supabase & Google Drive) ---
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
        return False, "UserID ต้องเป็นอังกฤษ/เลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "รหัสผ่านต้องเป็นอังกฤษ/เลขเท่านั้น"
    if not s_id.isdigit():
        return False, "รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "เบอร์โทรต้องมี 10 หลัก (ขึ้นต้น 06,08,09)"
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

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    # โลโก้ด้านบน
    st.markdown("<div class='fb-logo'>traffic game</div>", unsafe_allow_html=True)
    st.markdown("<div class='fb-sub'>บันทึกวินัยจราจรและสะสมแต้มความดีเพื่อรับรางวัลมากมาย</div>", unsafe_allow_html=True)
    
    # การ์ดสำหรับ Login/Signup
    tab_l, tab_s, tab_f = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก", "ลืมรหัสผ่าน"])
    
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
            except: st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.info("คำแนะนำ: หากลืมรหัสผ่าน ให้ไปที่แท็บ 'ลืมรหัสผ่าน'")

    with tab_s:
        s_uid = st.text_input("ตั้งชื่อผู้ใช้", key="s_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์")
        if st.button("สมัครบัญชีใหม่", key="btn_signup"):
            if all([s_uid, s_pw, s_name, s_sid, s_phone]):
                valid, msg = validate_signup(s_uid, s_pw, s_sid, s_phone)
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
                            st.success("สมัครสำเร็จ! กลับไปที่หน้า 'เข้าสู่ระบบ'")
                    except: st.error("ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")

    with tab_f:
        st.write("ยืนยันตัวตนเพื่อตั้งรหัสผ่านใหม่")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทร", key="f_phone")
        f_newpw = st.text_input("รหัสผ่านใหม่", type="password", key="f_newpw")
        if st.button("เปลี่ยนรหัสผ่าน", key="btn_reset"):
            if all([f_uid, f_sid, f_phone, f_newpw]) and re.match("^[a-zA-Z0-9]*$", f_newpw):
                try:
                    check = supabase.table("profiles").select("id").eq("username", f_uid.lower()).eq("student_id", f_sid).eq("phone_number", f_phone).single().execute()
                    if check.data:
                        supabase_admin.auth.admin.update_user_by_id(check.data['id'], {"password": f_newpw})
                        supabase.table("profiles").update({"password_plain": f_newpw}).eq("id", check.data['id']).execute()
                        st.success("เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("ข้อมูลไม่ถูกต้อง")
                except: st.error("ไม่พบข้อมูลผู้ใช้")

else:
    # --- หน้าจอหลัง Login (Dashboard) ---
    prof_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    prof = prof_res.data
    
    # Header ส่วนตัว
    c1, c2 = st.columns([0.7, 0.3])
    c1.write(f"👤 **{prof['username']}** | {prof['full_name']}")
    if c2.button("Logout"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()

    if st.session_state.role == "admin":
        st.title("🛠️ สำหรับผู้ดูแล")
        # โค้ดส่วน Admin...
    else:
        st.title(f"สวัสดีคุณ {prof['username']} 👋")
        col1, col2 = st.columns(2)
        col1.metric("คะแนน", prof.get('total_points', 0))
        col2.metric("ระดับ", prof.get('rank_title', 'ผู้เริ่มต้น'))

        st.divider()
        task = supabase.table("daily_tasks").select("*").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        if task.data:
            t = task.data[0]
            st.info(f"🚩 **ภารกิจ:** {t['task_name']}\n\n{t['task_description']}")
            img = st.camera_input("ถ่ายรูปส่งงาน")
            if img:
                if st.button("ส่งภารกิจ"):
                    with st.spinner("กำลังส่งงาน..."):
                        d_id = upload_to_drive(img, prof['username'])
                        if d_id:
                            supabase.table("missions").insert({"user_id": st.session_state.user.id, "image_drive_id": d_id, "mission_name": t['task_name']}).execute()
                            st.success("ส่งงานสำเร็จ!")
