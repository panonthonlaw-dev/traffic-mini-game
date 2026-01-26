import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ (Fix Bug PEM File) ---
try:
    # เชื่อมต่อ Supabase
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # ดึงค่า GCP และแก้ปัญหาการอ่าน Private Key (\n)
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")
    
    # สร้างการเชื่อมต่อ Google Drive
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]

except Exception as e:
    st.error(f"❌ ระบบเชื่อมต่อไม่ได้: {e}")
    st.stop()

# --- 3. ฟังก์ชันอัปโหลดรูป ---
def upload_to_drive(file_obj, filename):
    try:
        metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        # เปิดสิทธิ์ให้คนที่มีลิงก์เข้าดูได้
        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except: return None

# --- 4. CSS แต่งสวย (ปุ่มฟ้า/เขียว/กึ่งกลาง) ---
st.markdown("""
    <style>
        .block-container { max-width: 450px; margin: auto; }
        /* ปุ่มเข้าสู่ระบบ สีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; width: 100% !important; border-radius: 8px; font-weight: bold; height: 45px;
        }
        /* ปุ่มสมัครสมาชิก สีเขียว */
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important; color: white !important; width: 100% !important; border-radius: 8px; font-weight: bold; height: 45px;
        }
        input { text-align: center; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; border: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# --- 5. จัดการสถานะหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 6. แสดงผลหน้าจอ ---

# 🔵 หน้าเข้าสู่ระบบ
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("ชื่อผู้ใช้", placeholder="Username", label_visibility="collapsed")
        p = st.text_input("รหัสผ่าน", type="password", placeholder="Password", label_visibility="collapsed")
        if st.form_submit_button("เข้าสู่ระบบ"):
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                go_to('game')
            else: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", type="primary"): go_to('signup')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    user = st.session_state.user
    st.markdown(f"### สวัสดีคุณ {user['fullname']} 👋")
    st.markdown("---")
    
    missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
    subs = supabase.table("submissions").select("mission_id").eq("user_username", user['username']).execute().data
    done_ids = [s['mission_id'] for s in subs]
    
    for m in missions:
        is_done = m['id'] in done_ids
        st.markdown(f"""<div class="card"><b>{m['title']}</b> {'✅' if is_done else '🔴'}<br><small>{m['description']}</small></div>""", unsafe_allow_html=True)
        
        if not is_done:
            f = st.file_uploader(f"ส่งงาน: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
            if f and st.button(f"ยืนยันส่งภารกิจ", key=f"b{m['id']}", type="primary"):
                with st.spinner("กำลังอัปโหลด..."):
                    link = upload_to_drive(f, f"{user['username']}_m{m['id']}.jpg")
                    if link:
                        supabase.table("submissions").insert({"user_username": user['username'], "mission_id": m['id'], "image_url": link}).execute()
                        st.success("ส่งงานสำเร็จ!"); time.sleep(1); st.rerun()
                    else: st.error("❌ อัปโหลดล้มเหลว")
    
    st.markdown("---")
    if st.button("ออกจากระบบ"):
        st.session_state.user = None
        go_to('login')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("## สมัครสมาชิก")
    with st.form("signup"):
        name = st.text_input("ชื่อ-นามสกุล")
        user = st.text_input("ชื่อผู้ใช้")
        phone = st.text_input("เบอร์โทร")
        pw = st.text_input("รหัสผ่าน", type="password")
        if st.form_submit_button("ลงทะเบียน"):
            try:
                supabase.table("users").insert({"fullname":name, "username":user, "phone":phone, "password":pw}).execute()
                st.success("สมัครสมาชิกสำเร็จ!"); time.sleep(1); go_to('login')
            except: st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
    if st.button("กลับไปหน้าแรก"): go_to('login')
