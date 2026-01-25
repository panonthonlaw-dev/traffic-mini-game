import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. ตั้งค่าแอปและการเชื่อมต่อ ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

st.markdown("""
    <style>
        header[data-testid="stHeader"] { visibility: hidden; height: 0%; }
        section[data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# เชื่อมต่อแบบปกติ
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
# เชื่อมต่อแบบ Admin (สำหรับรีเซ็ตรหัสผ่าน)
supabase_admin = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

def init_drive():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

# --- 2. ฟังก์ชันจัดการระบบ ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def is_valid_userid(user_id):
    if len(user_id) < 6: return False, "❌ UserID ต้องยาวอย่างน้อย 6 ตัวอักษร"
    if not re.match("^[a-zA-Z0-9]*$", user_id): return False, "❌ UserID ต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
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

# --- 3. ระบบ Authentication ---

def sign_up(u_id, u_pw, name, s_id, phone):
    valid, msg = is_valid_userid(u_id)
    if not valid: st.error(msg); return
    email = format_email(u_id)
    try:
        res = supabase.auth.sign_up({"email": email, "password": u_pw})
        if res.user:
            supabase.table("profiles").insert({
                "id": res.user.id, "username": u_id.lower(), "full_name": name, 
                "student_id": s_id, "phone_number": phone, "role": "player"
            }).execute()
            st.success(f"✅ สมัครสำเร็จ! ใช้ชื่อ '{u_id.lower()}' ล็อกอินได้เลย")
    except Exception as e:
        if "already registered" in str(e).lower(): st.error("❌ ชื่อผู้ใช้นี้มีคนใช้ไปแล้ว")
        else: st.error(f"Error: {e}")

def reset_password_logic(u_id, s_id, phone, new_pw):
    try:
        # ตรวจสอบว่าข้อมูลตรงกันไหม
        check = supabase.table("profiles").select("id").eq("username", u_id.lower()).eq("student_id", s_id).eq("phone_number", phone).single().execute()
        if check.data:
            user_uuid = check.data['id']
            # ใช้ Admin Client สั่งอัปเดตรหัสผ่านโดยระบุ UUID
            supabase_admin.auth.admin.update_user_by_id(user_uuid, {"password": new_pw})
            st.success("✅ เปลี่ยนรหัสผ่านใหม่สำเร็จแล้ว! ลองเข้าสู่ระบบอีกครั้ง")
            return True
        else:
            st.error("❌ ข้อมูลไม่ถูกต้อง ไม่สามารถยืนยันตัวตนได้")
            return False
    except:
        st.error("❌ เกิดข้อผิดพลาดในการตรวจสอบข้อมูล")
        return False

# --- 4. ส่วนแสดงผล UI ---

if 'user' not in st.session_state:
    st.title("🚦 มินิเกมจราจร")
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_uid = st.text_input("UserID", key="l_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="l_pw")
        if st.button("เข้าสู่ระบบ", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_uid), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_uid = st.text_input("ตั้ง UserID (อังกฤษ/เลข)", key="s_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์")
        if st.button("ยืนยันการสมัคร", use_container_width=True):
            if all([s_uid, s_pw, s_name, s_sid, s_phone]):
                sign_up(s_uid, s_pw, s_name, s_sid, s_phone)
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")

    with tab_f:
        st.subheader("กู้คืนรหัสผ่าน")
        st.write("กรุณากรอกข้อมูลให้ตรงกับที่สมัครไว้")
        f_uid = st.text_input("UserID", key="f_uid")
        f_sid = st.text_input("รหัสนักเรียน", key="f_sid")
        f_phone = st.text_input("เบอร์โทรศัพท์", key="f_phone")
        f_newpw = st.text_input("ตั้งรหัสผ่านใหม่", type="password", key="f_newpw")
        if st.button("ยืนยันเปลี่ยนรหัสผ่าน", use_container_width=True):
            if all([f_uid, f_sid, f_phone, f_newpw]):
                reset_password_logic(f_uid, f_sid, f_phone, f_newpw)
            else: st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- เมื่อ Login สำเร็จ ---
    prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    username = prof.data.get('username', 'User')
    
    c_head, c_out = st.columns([0.8, 0.2])
    c_head.write(f"👤 **{username}** ({st.session_state.role})")
    if c_out.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

    st.divider()

    if st.session_state.role == "admin":
        st.title("🛠️ ระบบแอดมิน")
        # โค้ดส่วน Admin (สร้างภารกิจ/ตรวจงาน) ใส่ตามเดิมได้เลยครับ
    else:
        st.title(f"สวัสดีคุณ {username} 👋")
        c1, c2 = st.columns(2)
        c1.metric("🪙 คะแนน", prof.data.get('total_points', 0))
        c2.metric("🎖️ ระดับ", prof.data.get('rank_title', 'ผู้เริ่มต้น'))
        
        # โค้ดส่วน Player (ส่งรูปภารกิจ) ใส่ตามเดิมได้เลยครับ
