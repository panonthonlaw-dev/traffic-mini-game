import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. ตั้งค่าหน้าเวป ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ (Supabase + Google Drive) ---
try:
    # เชื่อมต่อ Supabase
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # แก้ไขปัญหา PEM สำหรับ Google Drive
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

# --- 3. CSS คุมโทนสีและตำแหน่ง (สวยงามแบบไม่ฝืนระบบ) ---
st.markdown("""
    <style>
        /* พื้นหลังเทาอ่อนเกือบขาว */
        .stApp {
            background-color: #f8f9fa !important;
        }

        /* ช่องกรอกข้อมูล: ตัวหนังสือชิดซ้าย และเป็นสีน้ำเงินเข้ม */
        input {
            text-align: left !important;
            padding-left: 15px !important;
            color: #003366 !important;
            border-radius: 8px !important;
        }
        
        /* เปลี่ยนสีตัวหนังสืออธิบายในช่อง (Placeholder) */
        input::placeholder {
            color: #003366 !important;
            opacity: 0.5;
        }

        /* ปุ่มเข้าสู่ระบบ (สีฟ้า) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
        }

        /* ปุ่มสร้างบัญชีใหม่ (สีเขียว) - ใช้การเจาะจง Secondary */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
        }

        /* ตกแต่งลิงก์ลืมรหัสผ่านตัวเล็ก */
        .forgot-link-btn {
            text-align: center;
            margin-top: -10px;
        }
        
        /* สไตล์ Card ภารกิจ */
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

# --- 4. ระบบจัดการหน้าจอ (State) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; margin-top: 0;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    # จัดกึ่งกลางด้วย columns
    _, col, _ = st.columns([1, 5, 1])
    
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้", label_visibility="collapsed")
            p = st.text_input("Password", placeholder="ระบุรหัสผ่าน", type="password", label_visibility="collapsed")
            login_btn = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if login_btn:
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else:
                    st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        # ลืมรหัสผ่าน (ใช้ปุ่มใสๆ ให้เหมือนลิงก์)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", use_container_width=True, type="tertiary"):
            go_to('forgot')
        # บังคับสีปุ่มลืมรหัสให้เป็นสีฟ้าตัวเล็กผ่าน CSS
        st.markdown('<style>div[data-testid="stButton"] > button[kind="tertiary"] { color: #1877f2 !important; font-size: 14px !important; text-decoration: underline !important; background: transparent !important; }</style>', unsafe_allow_html=True)

        st.write("---")
        
        # ปุ่มสร้างบัญชีใหม่ (สีเขียว)
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ระบุชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="กำหนด Username")
            phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
            
            # ปุ่มลงทะเบียนใน Form จะใช้สีฟ้าตาม CSS หลัก
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color: #003366;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 6, 1])
    with col:
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
        done_ids = [s['mission_id'] for s in subs]
        
        for m in missions:
            is_done = m['id'] in done_ids
            st.markdown(f"""
                <div class="mission-card" style="border-left: 5px solid {'#42b72a' if is_done else '#1877f2'};">
                    <b style="color: #003366;">{m['title']}</b><br>
                    <small style="color:{'#42b72a' if is_done else '#1877f2'}; font-weight:bold;">
                        {'✅ ส่งงานเรียบร้อย' if is_done else '🔵 รอดำเนินการ'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"แนบรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    if st.button(f"ยืนยันส่งภารกิจ {m['id']}", key=f"b{m['id']}", use_container_width=True, type="secondary"):
                        with st.spinner("กำลังส่งรูป..."):
                            try:
                                meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                                drive_service.files().create(body=meta, media_body=media).execute()
                                supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id']}).execute()
                                st.success("🎉 สำเร็จ!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center; color: #003366;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("forgot_form"):
            user_target = st.text_input("ระบุ Username")
            if st.form_submit_button("ค้นหารหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("password").eq("username", user_target).execute()
                if res.data: st.success(f"🔑 รหัสของคุณคือ: {res.data[0]['password']}")
                else: st.error("ไม่พบข้อมูล")
        if st.button("กลับหน้าหลัก", use_container_width=True): go_to('login')
