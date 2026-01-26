import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อ (คงเดิมเพื่อความเสถียร) ---
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

# --- 2. CSS ปรับแต่งความสวยงาม (ไม่ฝืนโครงสร้างหลัก) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังเวปสีเทาอ่อนออกไปทางขาว */
        .stApp {
            background-color: #f8f9fa !important;
        }

        /* 2. ช่อง Input ชิดซ้าย ทั้งตัวพิมพ์และ Placeholder */
        input {
            text-align: left !important;
            padding-left: 15px !important;
            border-radius: 8px !important;
        }

        /* 3. ปุ่มเข้าสู่ระบบ สีฟ้าเดียวกับ Traffic Game */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
        }

        /* 4. ปุ่มสร้างบัญชีใหม่ สีเขียวอ่อน */
        div.stButton > button:first-child {
            /* สำหรับปุ่มสร้างบัญชีในหน้า Login */
        }
        
        /* สไตล์พิเศษสำหรับปุ่มเขียวอ่อน */
        .green-sub-btn button {
            background-color: #b9f6ca !important;
            color: #1b5e20 !important;
            border: 1px solid #a5d6a7 !important;
        }

        /* 5. ตัวหนังสือลืมรหัสผ่านตัวเล็ก */
        .forgot-text button {
            background: transparent !important;
            border: none !important;
            color: #65676b !important;
            font-size: 13px !important;
            text-decoration: none !important;
            margin-top: -10px !important;
        }
        .forgot-text button:hover {
            text-decoration: underline !important;
            color: #1877f2 !important;
        }

        /* ตกแต่ง Card ภารกิจ */
        .mission-card {
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            margin-bottom: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    # หัวข้อสีฟ้ามาตรฐาน
    st.markdown("<h1 style='text-align: center; color:#1877f2; font-family: sans-serif; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #606770; margin-top: 0;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    # ใช้คอลัมน์ช่วยจัดกึ่งกลาง
    _, col, _ = st.columns([1, 4, 1])
    
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="ชื่อผู้ใช้")
            p = st.text_input("Password", type="password", placeholder="รหัสผ่าน")
            login_btn = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if login_btn:
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("ข้อมูลไม่ถูกต้อง")
        
        # ฟังก์ชันลืมรหัสผ่านตัวเล็กใต้ปุ่มเข้าสู่ระบบ
        st.markdown('<div class="forgot-text">', unsafe_allow_html=True)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", use_container_width=True):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ปุ่มสร้างบัญชีใหม่ (สีเขียวอ่อน)
        st.markdown('<div class="green-sub-btn">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", use_container_width=True):
            go_to('signup')
        st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ระบุชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="ระบุชื่อเข้าระบบ")
            phone = st.text_input("เบอร์โทร", placeholder="ระบุเบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
            if st.form_submit_button("ลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("ลงทะเบียนสำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อนี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h4 style='text-align: center;'>ยินดีต้อนรับคุณ {u['fullname']}</h4>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 4, 1])
    with col:
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
        done_ids = [s['mission_id'] for s in subs]
        
        for m in missions:
            is_done = m['id'] in done_ids
            st.markdown(f"""
                <div class="mission-card" style="border-left: 5px solid {'#2e7d32' if is_done else '#e53935'};">
                    <b>{m['title']}</b><br>
                    <small style="color:{'#2e7d32' if is_done else '#e53935'}; font-weight:bold;">
                        {'✅ ส่งภารกิจเรียบร้อย' if is_done else '🔴 รอดำเนินการ'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"แนบรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    if st.button(f"ยืนยันส่งงาน {m['id']}", key=f"b{m['id']}", use_container_width=True):
                        with st.spinner("กำลังอัปโหลด..."):
                            try:
                                meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                                drive_service.files().create(body=meta, media_body=media).execute()
                                supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id']}).execute()
                                st.success("ส่งงานสำเร็จ!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            user_target = st.text_input("ระบุชื่อผู้ใช้ของคุณ")
            if st.form_submit_button("ค้นหา", use_container_width=True):
                res = supabase.table("users").select("password").eq("username", user_target).execute()
                if res.data: st.success(f"รหัสผ่านของคุณคือ: {res.data[0]['password']}")
                else: st.error("ไม่พบข้อมูลผู้ใช้")
        if st.button("กลับหน้าหลัก", use_container_width=True): go_to('login')
