import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. เชื่อมต่อระบบ (Supabase + Drive) ---
try:
    # Supabase
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # Google Drive (Fix InvalidPadding Error)
    # แปลงข้อมูล Secret เป็น Dict เพื่อแก้ไข
    gcp_creds = dict(st.secrets["gcp_service_account"])
    
    # 🟢 แก้ไขปัญหา \n ใน Private Key
    gcp_creds["private_key"] = gcp_creds["private_key"].replace("\\n", "\n")
    
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
    
    # สร้าง Credential
    drive_creds = service_account.Credentials.from_service_account_info(
        gcp_creds, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=drive_creds)

except Exception as e:
    st.error(f"❌ เชื่อมต่อระบบไม่ได้: {e}")
    st.stop()

# --- 3. ฟังก์ชันอัปโหลดรูป ---
def upload_to_drive(file_obj, filename):
    try:
        metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
        # อัปโหลด
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        # เปิดสิทธิ์ (Public Link)
        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Google Drive Error: {e}")
        return None

# --- 4. CSS แต่งสวย ---
st.markdown("""
    <style>
        .block-container { max-width: 420px; padding-top: 2rem; margin: auto; }
        
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; border: none !important;
            font-weight: bold !important; height: 48px !important; width: 100% !important; border-radius: 8px !important;
        }
        
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important; color: white !important; border: none !important;
            font-weight: bold !important; height: 48px !important; width: 100% !important; border-radius: 8px !important;
        }
        
        div.stButton > button[kind="secondary"] {
            background: transparent !important; border: none !important; color: #1877f2 !important;
            height: auto !important; padding: 0 !important; width: 100% !important; text-decoration: none !important;
        }
        div.stButton > button[kind="secondary"]:hover { text-decoration: underline !important; }
        
        input { text-align: center; border-radius: 8px !important; }
        button[aria-label="Show password"] { display: none !important; }
        
        .mission-card {
            background-color: white; padding: 15px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 15px; border: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

# --- 5. จัดการหน้าจอ (State) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 6. Layout ---

# ==================== LOGIN ====================
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#606770;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        user = st.text_input("ชื่อผู้ใช้", placeholder="กรอกชื่อผู้ใช้", label_visibility="collapsed")
        pw = st.text_input("รหัสผ่าน", type="password", placeholder="กรอกรหัสผ่าน", label_visibility="collapsed")
        
        if st.form_submit_button("เข้าสู่ระบบ"):
            try:
                res = supabase.table("users").select("*").eq("username", user).execute()
                if res.data and res.data[0]['password'] == pw:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            except Exception as e: st.error(f"Login Error: {e}")
    
    if st.button("ลืมรหัสผ่านใช่หรือไม่?", type="secondary"): go_to('forgot')
    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่", type="primary"): go_to('signup')

# ==================== SIGNUP ====================
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อ-นามสกุล")
        user = st.text_input("ชื่อผู้ใช้", placeholder="ภาษาอังกฤษ 6-12 ตัว")
        phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทร 10 หลัก", max_chars=10)
        p1 = st.text_input("รหัสผ่าน", type="password", placeholder="รหัสผ่าน 6-13 ตัว")
        p2 = st.text_input("ยืนยันรหัสผ่าน", type="password", placeholder="ยืนยันรหัสผ่าน")
        
        st.markdown("""<style>div[data-testid="stFormSubmitButton"] > button { background-color: #42b72a !important; }</style>""", unsafe_allow_html=True)
        
        if st.form_submit_button("สมัครสมาชิก"):
            if not name or len(user) < 6 or len(phone) != 10 or p1 != p2:
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบและถูกต้อง")
            else:
                try:
                    check = supabase.table("users").select("username").eq("username", user).execute()
                    if check.data:
                        st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                    else:
                        supabase.table("users").insert({
                            "fullname": name, "username": user, "phone": phone, "password": p1
                        }).execute()
                        st.success("✅ สมัครสมาชิกสำเร็จ!")
                        time.sleep(1.5)
                        go_to('login')
                except Exception as e: st.error(f"Error: {e}")

    if st.button("กลับไปหน้าเข้าสู่ระบบ", type="secondary"): go_to('login')

# ==================== GAME ====================
elif st.session_state.page == 'game':
    me = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color:#1877f2;'>สวัสดีคุณ {me['fullname']} 👋</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    try:
        missions = supabase.table("missions").select("*").eq("is_active", True).order("id").execute().data
        my_subs = supabase.table("submissions").select("mission_id").eq("user_username", me['username']).execute().data
        done_ids = [s['mission_id'] for s in my_subs]
        
        if not missions: st.info("ยังไม่มีภารกิจจาก Admin")
        
        for m in missions:
            is_done = m['id'] in done_ids
            status = "✅ ส่งแล้ว" if is_done else "🔴 รอส่ง"
            bg = "#e8f5e9" if is_done else "white"
            
            st.markdown(f"""
            <div class="mission-card" style="background-color: {bg};">
                <div style="display:flex; justify-content:space-between;">
                    <b style="font-size:18px;">{m['title']}</b>
                    <span style="color:{'green' if is_done else 'red'}; font-weight:bold;">{status}</span>
                </div>
                <div style="color:#555; margin-top:5px;">{m['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                upl = st.file_uploader(f"ส่งงาน: {m['title']}", type=['jpg','png'], key=f"u_{m['id']}")
                if upl:
                    if st.button(f"ยืนยันส่งรูป", key=f"b_{m['id']}", type="primary"):
                        with st.spinner("กำลังส่งไป Google Drive..."):
                            fname = f"{me['username']}_m{m['id']}_{int(time.time())}.jpg"
                            link = upload_to_drive(upl, fname)
                            if link:
                                supabase.table("submissions").insert({
                                    "user_username": me['username'], "mission_id": m['id'], "image_url": link
                                }).execute()
                                st.success("🎉 ส่งงานเรียบร้อย!")
                                time.sleep(1.5)
                                st.rerun()
                            else: st.error("❌ อัปโหลดไม่ผ่าน")
            
    except Exception as e: st.error(f"โหลดข้อมูลไม่ได้: {e}")
    
    st.markdown("---")
    st.markdown("""<style>div.stButton > button[kind="secondaryForm"] { background-color: #ff4b4b !important; color: white !important; }</style>""", unsafe_allow_html=True)
    if st.button("ออกจากระบบ", type="primary", key="logout"):
        st.session_state.user = None
        go_to('login')

# ==================== FORGOT ====================
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center;'>ลืมรหัสผ่าน</h3>", unsafe_allow_html=True)
    with st.form("forgot_form"):
        f_user = st.text_input("กรอกชื่อผู้ใช้")
        if st.form_submit_button("ค้นหา"):
            res = supabase.table("users").select("password").eq("username", f_user).execute()
            if res.data: st.success(f"🔑 รหัสผ่านของคุณคือ: {res.data[0]['password']}")
            else: st.error("❌ ไม่พบข้อมูล")
    
    if st.button("กลับไปหน้าเข้าสู่ระบบ", type="secondary"): go_to('login')
