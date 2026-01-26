import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. เชื่อมต่อระบบ (พร้อมตัวแก้ Bug PEM File) ---
try:
    # เชื่อมต่อ Supabase
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # ดึงค่าจาก Secrets มาใส่ในตัวแปรแบบ Dictionary
    gcp_info = dict(st.secrets["gcp_service_account"])
    
    # 🟢 จุดสำคัญ: แก้ไขปัญหา \n ในกุญแจลับ
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")
    
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
    
    # สร้างการเชื่อมต่อ Google Drive ด้วยข้อมูลที่แก้ไขแล้ว
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)

except Exception as e:
    st.error(f"❌ ระบบขัดข้องในการเชื่อมต่อ: {e}")
    st.stop()

# --- 3. ฟังก์ชันอัปโหลดรูป ---
def upload_to_drive(file_obj, filename):
    try:
        metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except: return None

# --- 4. CSS แต่งหน้าตา (ตามสไตล์เดิมที่พี่ชอบ) ---
st.markdown("""
    <style>
        .block-container { max-width: 420px; padding-top: 2rem; margin: auto; }
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; font-weight: bold !important;
            height: 50px !important; width: 100% !important; border-radius: 8px !important;
        }
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important; color: white !important; font-weight: bold !important;
            height: 50px !important; width: 100% !important; border-radius: 8px !important;
        }
        div.stButton > button[kind="secondary"] {
            background: transparent !important; border: none !important; color: #1877f2 !important;
            font-size: 14px !important; text-decoration: none !important; width: 100% !important;
        }
        input { text-align: center !important; border-radius: 8px !important; }
        .mission-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. จัดการหน้าจอ (State Management) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state.user: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 6. แสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom:0;'>traffic game</h1><p style='text-align: center;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("user", placeholder="ชื่อผู้ใช้", label_visibility="collapsed")
        p = st.text_input("pass", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed")
        if st.form_submit_button("เข้าสู่ระบบ"):
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                go_to('game')
            else: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านผิด")
    if st.button("ลืมรหัสผ่าน?", type="secondary"): go_to('forgot')
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", type="primary"): go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    with st.form("signup"):
        name = st.text_input("ชื่อ-นามสกุล")
        user = st.text_input("ชื่อผู้ใช้")
        phone = st.text_input("เบอร์โทรศัพท์", max_chars=10)
        p1 = st.text_input("รหัสผ่าน", type="password")
        p2 = st.text_input("ยืนยันรหัสผ่าน", type="password")
        st.markdown("<style>div[data-testid='stFormSubmitButton']>button{background-color:#42b72a !important;}</style>", unsafe_allow_html=True)
        if st.form_submit_button("ลงทะเบียน"):
            if p1 == p2 and len(user) >= 6:
                try:
                    supabase.table("users").insert({"fullname":name, "username":user, "phone":phone, "password":p1}).execute()
                    st.success("✅ สมัครสำเร็จ!")
                    time.sleep(1); go_to('login')
                except: st.error("❌ ชื่อผู้ใช้นี้ถูกใช้งานแล้ว")
            else: st.warning("กรุณาตรวจสอบข้อมูลอีกครั้ง")
    if st.button("ยกเลิก", type="secondary"): go_to('login')

# 🎮 หน้าเล่นเกม / ภารกิจ
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color:#1877f2;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    
    missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
    subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
    done_ids = [s['mission_id'] for s in subs]
    
    for m in missions:
        is_done = m['id'] in done_ids
        st.markdown(f"""<div class="mission-card" style="background:{'#f0fdf4' if is_done else 'white'}">
            <b>{m['title']}</b> {'✅' if is_done else '🔴'}<br><small>{m['description']}</small></div>""", unsafe_allow_html=True)
        
        if not is_done:
            f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
            if f and st.button(f"ยืนยันส่งภารกิจ", key=f"b{m['id']}", type="primary"):
                with st.spinner("กำลังอัปโหลด..."):
                    link = upload_to_drive(f, f"{u['username']}_m{m['id']}.jpg")
                    if link:
                        supabase.table("submissions").insert({"user_username":u['username'], "mission_id":m['id'], "image_url":link}).execute()
                        st.success("สำเร็จ!"); time.sleep(1); st.rerun()
    
    st.markdown("---")
    if st.button("ออกจากระบบ"):
        st.session_state.user = None
        go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    with st.form("forgot"):
        user_input = st.text_input("ชื่อผู้ใช้")
        if st.form_submit_button("ค้นหา"):
            res = supabase.table("users").select("password").eq("username", user_input).execute()
            if res.data: st.success(f"🔑 รหัสผ่านของคุณคือ: {res.data[0]['password']}")
            else: st.error("❌ ไม่พบข้อมูลผู้ใช้")
    if st.button("กลับไปหน้าแรก", type="secondary"): go_to('login')
