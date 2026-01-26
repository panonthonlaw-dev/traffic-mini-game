import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (Fix Bug PEM File) ---
try:
    # Supabase
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # Google Drive - แก้ปัญหาขึ้นบรรทัดใหม่ใน Private Key
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")
    
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
except Exception as e:
    st.error(f"❌ ระบบเชื่อมต่อไม่ได้: {e}")
    st.stop()

# --- 2. CSS แต่งสวย (ปุ่มฟ้า/เขียว/กึ่งกลาง) ---
st.markdown("""
    <style>
        .block-container { max-width: 450px; margin: auto; }
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; width: 100% !important; border-radius: 8px; font-weight: bold; height: 50px;
        }
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important; color: white !important; width: 100% !important; border-radius: 8px; font-weight: bold; height: 50px;
        }
        input { text-align: center; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; border: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# --- 3. จัดการ State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. หน้าจอหลัก ---
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed")
        p = st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed")
        if st.form_submit_button("เข้าสู่ระบบ"):
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                go_to('game')
            else: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    if st.button("สร้างบัญชีใหม่", type="primary"): go_to('signup')

elif st.session_state.page == 'signup':
    st.markdown("## สมัครสมาชิก")
    with st.form("signup"):
        name = st.text_input("ชื่อ-นามสกุล")
        user = st.text_input("ชื่อผู้ใช้")
        phone = st.text_input("เบอร์โทร")
        pw = st.text_input("รหัสผ่าน", type="password")
        if st.form_submit_button("ลงทะเบียน"):
            try:
                supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                st.success("สำเร็จ!"); time.sleep(1); go_to('login')
            except: st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
    if st.button("กลับ"): go_to('login')

elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"### สวัสดีคุณ {u['fullname']} 👋")
    missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
    subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
    done_ids = [s['mission_id'] for s in subs]
    
    for m in missions:
        done = m['id'] in done_ids
        st.markdown(f"""<div class="card"><b>{m['title']}</b> {'✅' if done else '🔴'}<br><small>{m['description']}</small></div>""", unsafe_allow_html=True)
        if not done:
            f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
            if f and st.button(f"ยืนยันส่งภารกิจ", key=f"b{m['id']}", type="primary"):
                with st.spinner("กำลังส่ง..."):
                    try:
                        meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                        media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                        file = drive_service.files().create(body=meta, media_body=media, fields='id, webViewLink').execute()
                        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
                        supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id'], "image_url": file.get('webViewLink')}).execute()
                        st.success("สำเร็จ!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
    if st.button("ออกจากระบบ"):
        st.session_state.user = None
        go_to('login')
