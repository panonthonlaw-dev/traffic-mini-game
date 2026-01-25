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
    # สำคัญมาก: ต้อง .lower() ทั้งตอนสมัครและล็อกอิน เพื่อให้หาเจอ
    return f"{user_id.strip().lower()}@traffic.com"

def is_valid_userid(user_id):
    if len(user_id) < 6: # ปรับเป็น < 6 ตามที่คุณต้องการ (หรือ <= 6)
        return False, "❌ ชื่อผู้ใช้ (UserID) ต้องมีความยาวอย่างน้อย 6 ตัวอักษร"
    if not re.match("^[a-zA-Z0-9]*$", user_id):
        return False, "❌ ชื่อผู้ใช้ต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น (ห้ามเว้นวรรค/ภาษาไทย)"
    return True, ""

def upload_to_drive(file, user_id):
    try:
        drive_service = init_drive()
        folder_id = st.secrets["GDRIVE_FOLDER_ID"]
        
        # ย่อขนาดรูปภาพเพื่อประหยัดพื้นที่ 2TB
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
        st.error(f"เกิดข้อผิดพลาดในการอัปโหลดรูป: {e}")
        return None

# --- 3. ระบบ Authentication (Login/Signup) ---

def sign_in(u_id, u_pw):
    email = format_email(u_id)
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": u_pw})
        if res.user:
            # ดึงบทบาทจาก profiles
            role_data = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
            st.session_state.user = res.user
            st.session_state.role = role_data.data['role'] if role_data.data else "player"
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
    except Exception as e:
        st.error("❌ ไม่พบชื่อผู้ใช้นี้ หรือรหัสผ่านไม่ถูกต้อง (ตรวจสอบตัวพิมพ์เล็ก-ใหญ่)")

def sign_up(u_id, u_pw, name, s_id):
    valid, msg = is_valid_userid(u_id)
    if not valid:
        st.error(msg)
        return
    
    email = format_email(u_id)
    try:
        # 1. สมัครใน Auth
        res = supabase.auth.sign_up({"email": email, "password": u_pw})
        if res.user:
            # 2. บันทึกข้อมูลลงตาราง profiles
            supabase.table("profiles").insert({
                "id": res.user.id, 
                "full_name": name, 
                "student_id": s_id, 
                "role": "player"
            }).execute()
            st.success(f"✅ สมัครสำเร็จ! ใช้ชื่อ '{u_id.lower()}' เข้าใช้งานได้เลย")
        else:
            st.error("เกิดข้อผิดพลาดในการสมัคร กรุณาลองใหม่")
    except Exception as e:
        if "already registered" in str(e).lower():
            st.error("❌ มีชื่อผู้ใช้นี้ในระบบแล้ว กรุณาตั้งชื่อใหม่")
        else:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 4. หน้าจอหลัก (UI) ---

if 'user' not in st.session_state:
    st.title("🚦 ระบบมินิเกมจราจร")
    tab_l, tab_s = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก"])
    
    with tab_l:
        l_uid = st.text_input("ชื่อผู้ใช้ (UserID)", key="l_uid")
        l_pw = st.text_input("รหัสผ่าน", type="password", key="l_pw")
        if st.button("ตกลง เข้าสู่ระบบ", use_container_width=True):
            if l_uid and l_pw:
                sign_in(l_uid, l_pw)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบ")

    with tab_s:
        st.info("💡 ชื่อผู้ใช้: ภาษาอังกฤษ/ตัวเลข มากกว่า 6 ตัว")
        s_uid = st.text_input("ตั้งชื่อผู้ใช้", key="s_uid")
        s_pw = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        if st.button("ยืนยันการสมัคร", use_container_width=True):
            if s_uid and s_pw and s_name and s_sid:
                sign_up(s_uid, s_pw, s_name, s_sid)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- เมื่อ Login สำเร็จ ---
    user_id_clean = st.session_state.user.email.split('@')[0]
    st.sidebar.title("Traffic Game")
    st.sidebar.info(f"👤 สวัสดี: {user_id_clean}\n🎭 สถานะ: {st.session_state.role}")
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
            t_name = st.text_input("ชื่อภารกิจ เช่น ถ่ายรูปสวมหมวก")
            t_desc = st.text_area("รายละเอียดภารกิจ")
            t_points = st.number_input("คะแนนที่จะให้", min_value=1, value=10)
            if st.button("ประกาศภารกิจ"):
                supabase.table("daily_tasks").insert({
                    "task_name": t_name, 
                    "task_description": t_desc, 
                    "points_to_give": t_points
                }).execute()
                st.success("ประกาศภารกิจสำเร็จ!")

        with ad_tab2:
            st.subheader("รายการที่นักเรียนส่งมา")
            pending = supabase.table("missions").select("*, profiles(full_name)").eq("status", "pending").execute()
            if not pending.data:
                st.write("ยังไม่มีงานรอตรวจในขณะนี้")
            for p in pending.data:
                with st.expander(f"งานของ: {p['profiles']['full_name']} - {p['mission_name']}"):
                    st.image(f"https://drive.google.com/thumbnail?id={p['image_drive_id']}&sz=w800")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ อนุมัติ (+แต้ม)", key=f"app_{p['id']}"):
                        supabase.table("missions").update({"status": "approved"}).eq("id", p['id']).execute()
                        supabase.rpc('increment_points', {'row_id': p['user_id'], 'amount': 10}).execute()
                        st.success("อนุมัติและเพิ่มคะแนนสำเร็จ!")
                        st.rerun()
                    if c2.button("❌ ไม่ผ่าน", key=f"rej_{p['id']}"):
                        supabase.table("missions").update({"status": "rejected"}).eq("id", p['id']).execute()
                        st.rerun()

    # --- หน้าจอผู้เล่น (Player) ---
    else:
        st.title(f"👋 ยินดีต้อนรับ คุณ {user_id_clean}")
        
        # 1. การ์ดคะแนน
        prof = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("คะแนนสะสม", f"{prof.data['total_points']} 🪙")
        with col2:
            st.metric("ฉายา", prof.data['rank_title'])

        # 2. ภารกิจปัจจุบัน
        st.divider()
        task = supabase.table("daily_tasks").select("*").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        
        if task.data:
            t = task.data[0]
            st.info(f"🚩 **ภารกิจวันนี้:** {t['task_name']}\n\n{t['task_description']}")
            
            # เช็คว่าเคยส่งงานนี้ไปหรือยัง
            img_file = st.camera_input("📸 ถ่ายรูปยืนยันภารกิจ")
            if img_file:
                if st.button("🚀 ส่งงานตรวจสอบ"):
                    with st.spinner("กำลังส่งรูปเข้า Drive..."):
                        d_id = upload_to_drive(img_file, user_id_clean)
                        if d_id:
                            supabase.table("missions").insert({
                                "user_id": st.session_state.user.id,
                                "image_drive_id": d_id,
                                "mission_name": t['task_name']
                            }).execute()
                            st.success("ส่งงานสำเร็จแล้ว! รอแอดมินตรวจเพื่อรับแต้มนะ")
        else:
            st.warning("ยังไม่มีภารกิจใหม่ในตอนนี้")
