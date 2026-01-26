import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (คงไว้เพื่อความเสถียร) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n").strip()
    
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
except Exception as e:
    st.error(f"❌ ระบบเชื่อมต่อไม่ได้: {e}")
    st.stop()

# --- 2. CSS จัดทุกอย่างให้อยู่ตรงกลาง (Centering) ---
st.markdown("""
    <style>
        /* บีบหน้าจอให้เล็กลงเหมือนแอปมือถือและจัดกึ่งกลางจอ */
        .block-container {
            max-width: 400px !important;
            padding-top: 2rem !important;
            margin: auto !important;
        }

        /* จัดปุ่มทุกอันให้กว้างเต็มและอยู่ตรงกลาง */
        .stButton button {
            display: block !important;
            margin-left: auto !important;
            margin-right: auto !important;
            width: 100% !important;
            border-radius: 12px !important;
            height: 50px !important;
            font-weight: bold !important;
            font-size: 16px !important;
            transition: 0.3s;
        }

        /* ปุ่มสีฟ้า (Login) */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
        }

        /* ปุ่มสีเขียว (Signup / ส่งงาน) */
        .green-btn button {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
        }

        /* ปุ่มรอง (Logout) */
        .logout-btn button {
            background-color: #f02849 !important;
            color: white !important;
            border: none !important;
        }

        /* จัดตัวหนังสือใน Input ให้อยู่กึ่งกลาง */
        input {
            text-align: center !important;
            border-radius: 10px !important;
        }

        /* ตกแต่ง Card ภารกิจ */
        .mission-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบหน้าจอ (State) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. แสดงผลแต่ละหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; font-family: sans-serif;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #606770;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        u = st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed")
        p = st.text_input("Password", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed")
        login_btn = st.form_submit_button("เข้าสู่ระบบ")
        
        if login_btn:
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                go_to('game')
            else: st.error("ชื่อผู้ใช้หรือรหัสผ่านผิด")
            
    st.markdown("<hr style='border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
    
    st.markdown('<div class="green-btn">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่"): go_to('signup')
    st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    with st.form("signup_form"):
        name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อ-นามสกุล")
        user = st.text_input("ชื่อผู้ใช้", placeholder="Username")
        phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทร")
        pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password")
        
        st.markdown('<div class="green-btn">', unsafe_allow_html=True)
        if st.form_submit_button("ลงทะเบียน"):
            try:
                supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                st.success("สำเร็จ!"); time.sleep(1); go_to('login')
            except: st.error("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว")
        st.markdown('</div>', unsafe_allow_html=True)
    if st.button("ย้อนกลับ"): go_to('login')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    
    # ดึงภารกิจ
    missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
    subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
    done_ids = [s['mission_id'] for s in subs]
    
    for m in missions:
        is_done = m['id'] in done_ids
        st.markdown(f"""
            <div class="mission-card" style="background:{'#f0fdf4' if is_done else 'white'}">
                <b style="font-size: 18px;">{m['title']}</b><br>
                <span style="color:{'#2e7d32' if is_done else '#d32f2f'}; font-weight:bold;">
                    {'✅ สำเร็จแล้ว' if is_done else '🔴 รอดำเนินการ'}
                </span><br>
                <small style="color: #666;">{m['description']}</small>
            </div>
        """, unsafe_allow_html=True)
        
        if not is_done:
            f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
            if f:
                st.markdown('<div class="green-btn">', unsafe_allow_html=True)
                if st.button(f"ยืนยันส่งภารกิจ {m['id']}", key=f"b{m['id']}"):
                    with st.spinner("กำลังอัปโหลด..."):
                        try:
                            meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                            media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                            file = drive_service.files().create(body=meta, media_body=media, fields='id, webViewLink').execute()
                            drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
                            supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id'], "image_url": file.get('webViewLink')}).execute()
                            st.success("ส่งงานสำเร็จ!"); time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("ออกจากระบบ"):
        st.session_state.user = None
        go_to('login')
    st.markdown('</div>', unsafe_allow_html=True)
