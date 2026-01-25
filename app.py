import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. ตั้งค่าหน้าตาแอปและการเชื่อมต่อ ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# เชื่อมต่อ Supabase
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# เชื่อมต่อ Google Drive
def init_drive():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

# --- 2. ฟังก์ชันจัดการระบบ (Logic) ---

def format_email(user_id):
    # บังคับเป็นตัวพิมพ์เล็กและโดเมนมาตรฐานเพื่อป้องกัน Error
    return f"{user_id.strip().lower()}@traffic.com"

def is_valid_userid(user_id):
    if len(user_id) < 6:
        return False, "❌ UserID ต้องมีความยาวอย่างน้อย 6 ตัวอักษร"
    if not re.match("^[a-zA-Z0-9]*$", user_id):
        return False, "❌ UserID ต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    return True, ""

def upload_to_drive(file, user_id):
    try:
        drive_service = init_drive()
        folder_id = st.secrets["GDRIVE_FOLDER_ID"]
        
        # ย่อขนาดรูปภาพ (Image Compression) เพื่อประหยัดพื้นที่ 2TB
        img = Image.open(file)
        img = img.convert("RGB")
        img.thumbnail((1024, 1024))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)

        file_metadata = {
            'name': f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(img_byte_arr, mimetype='image/jpeg', resumable=True)
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return uploaded_file.get('id')
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปโหลด: {e}")
        return None

# --- 3. ระบบ Authentication (Login/Signup) ---

def sign_in(u_id, u_pw):
    email = format_email(u_id)
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": u_pw})
        if res.user:
            # ดึงข้อมูล Role
            role_query = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
            st.session_state.user = res.user
            st.session_state.role = role_query.data.get('role', 'player') if role_query.data else "player"
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
    except:
        st.error("❌ ไม่พบชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")

def sign_up(u_id, u_pw, name, s_id):
    valid, msg = is_valid_userid(u_id)
    if not valid:
        st.error(msg)
        return
    email = format_email(u_id)
    try:
        res = supabase.auth.sign_up({"email": email, "password": u_pw})
        if res.user:
            supabase.table("profiles").insert({
                "id": res.user.id, "full_name": name, "student_id": s_id, "role": "player"
            }).execute()
            st.success(f"✅ สมัครสำเร็จ! ใช้ UserID: {u_id.lower()} ล็อกอินได้เลย")
    except Exception as e:
        if "already registered" in str(e).lower(): st.error("❌ มีชื่อผู้ใช้นี้ในระบบแล้ว")
        else: st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 4. ส่วนแสดงผลบนหน้าจอ (UI) ---



if 'user' not in st.session_state:
    st.title("🚦 ระบบมินิเกมจราจร")
    tab_l, tab_s = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก"])
    with tab_l:
        l_uid = st.text_input("UserID", key="login_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("ตกลง เข้าสู่ระบบ", use_container_width=True):
            if l_uid and l_pw: sign_in(l_uid, l_pw)
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")
    with tab_s:
        s_uid = st.text_input("ตั้ง UserID (อังกฤษ/เลข > 6 ตัว)", key="reg_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="reg_pass")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        if st.button("ยืนยันการสมัคร", use_container_width=True):
            if s_uid and s_pw and s_name and s_sid: sign_up(s_uid, s_pw, s_name, s_sid)
            else: st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- เมื่อ Login สำเร็จ ---
    user_id_clean = st.session_state.user.email.split('@')[0]
    st.sidebar.title("Traffic Game")
    st.sidebar.info(f"👤 ยินดีต้อนรับ: {user_id_clean}\n🎭 สถานะ: {st.session_state.role}")
    if st.sidebar.button("ออกจากระบบ"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

    # --- หน้าจอแอดมิน (Admin) ---
    if st.session_state.role == "admin":
        st.title("🛠️ ระบบหลังบ้านแอดมิน")
        ad_tab1, ad_tab2 = st.tabs(["📢 สร้างภารกิจ", "✅ ตรวจสอบงาน"])
        
        with ad_tab1:
            st.subheader("สร้างภารกิจใหม่")
            t_name = st.text_input("ชื่อภารกิจ")
            t_desc = st.text_area("รายละเอียด")
            t_pts = st.number_input("คะแนน", min_value=1, value=10)
            if st.button("ประกาศภารกิจ"):
                supabase.table("daily_tasks").insert({"task_name": t_name, "task_description": t_desc, "points_to_give": t_pts}).execute()
                st.success("ประกาศสำเร็จ!")

        with ad_tab2:
            st.subheader("รายการรอตรวจ")
            pending = supabase.table("missions").select("*, profiles(full_name)").eq("status", "pending").execute()
            if not pending.data: st.write("ยังไม่มีงานใหม่")
            for p in pending.data:
                with st.expander(f"งานของ: {p['profiles']['full_name']} - {p['mission_name']}"):
                    st.image(f"https://drive.google.com/thumbnail?id={p['image_drive_id']}&sz=w800")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ อนุมัติ", key=f"a_{p['id']}"):
                        supabase.table("missions").update({"status": "approved"}).eq("id", p['id']).execute()
                        # ให้คะแนนตามที่ตั้งไว้ในภารกิจ (หรือใช้ค่าคงที่)
                        supabase.rpc('increment_points', {'row_id': p['user_id'], 'amount': 10}).execute()
                        st.rerun()
                    if c2.button("❌ ไม่ผ่าน", key=f"r_{p['id']}"):
                        supabase.table("missions").update({"status": "rejected"}).eq("id", p['id']).execute()
                        st.rerun()

    # --- หน้าจอผู้เล่น (Player) ---
    else:
        st.title(f"👋 สวัสดีคุณ {user_id_clean}")
        
        # ดึงข้อมูลโปรไฟล์แบบปลอดภัย (ป้องกัน KeyError)
        prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
        points = prof.data.get('total_points', 0) if prof.data else 0
        rank = prof.data.get('rank_title', 'ผู้เริ่มต้น') if prof.data else 'ผู้เริ่มต้น'
        
        col1, col2 = st.columns(2)
        col1.metric("คะแนนของคุณ", f"{points} 🪙")
        col2.metric("ระดับ", rank)

        st.divider()
        task = supabase.table("daily_tasks").select("*").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        
        if task.data:
            t = task.data[0]
            st.info(f"🚩 **ภารกิจ:** {t['task_name']}\n\n{t['task_description']}")
            img_file = st.camera_input("📸 ถ่ายรูปยืนยัน")
            if img_file:
                if st.button("🚀 ส่งงาน"):
                    with st.spinner("กำลังอัปโหลด..."):
                        d_id = upload_to_drive(img_file, user_id_clean)
                        if d_id:
                            supabase.table("missions").insert({
                                "user_id": st.session_state.user.id,
                                "image_drive_id": d_id,
                                "mission_name": t['task_name']
                            }).execute()
                            st.success("ส่งเรียบร้อย! รอแอดมินตรวจนะ")
        else:
            st.warning("ยังไม่มีภารกิจใหม่")
