import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (เหมือนเดิมของพี่) ---
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

# --- 2. CSS พื้นฐานระดับเวป (คุมสีพื้นและตัวหนังสือชิดซ้าย) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* สไตล์ช่องกรอก: บังคับขาว, น้ำเงินเข้ม, ชิดซ้าย, ตาอยู่ข้างใน */
        div[data-testid="stTextInput"] > div {
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 8px !important;
        }
        input {
            color: #003366 !important;
            -webkit-text-fill-color: #003366 !important;
            text-align: left !important;
            border: none !important;
            box-shadow: none !important;
        }
        label { color: #003366 !important; font-weight: bold !important; }
        button[data-testid="stTextInputPasswordToggle"] { color: #1877f2 !important; }
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
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; margin-top: 0; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 5, 1])
    with col:
        # ส่วนฟอร์ม Login (ปุ่มฟ้าอัตโนมัติจาก Theme)
        with st.form("login_form"):
            u = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            p = st.text_input("รหัสผ่าน", placeholder="Password", type="password")
            # ปุ่มเข้าสู่ระบบ สีฟ้า #1877f2
            login_btn = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            if login_btn:
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        # --- ปุ่มลืมรหัสผ่าน (ไร้กรอบ) ---
        st.markdown("""
            <style>
                .forgot-area div[data-testid="stButton"] > button {
                    border: none !important;
                    background: transparent !important;
                    color: #1877f2 !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                    height: auto !important;
                    min-height: unset !important;
                }
                .forgot-area div[data-testid="stButton"] > button:hover {
                    text-decoration: underline !important;
                    background: transparent !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="forgot-area">', unsafe_allow_html=True)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", use_container_width=True):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        
        # --- ปุ่มสร้างบัญชีใหม่ (สีเขียว) ---
        st.markdown("""
            <style>
                .signup-btn-area div[data-testid="stButton"] > button {
                    background-color: #42b72a !important;
                    color: white !important;
                    border: none !important;
                    font-weight: bold !important;
                    height: 48px !important;
                    border-radius: 8px !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="signup-btn-area">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", use_container_width=True):
            go_to('signup')
        st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 5, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ระบุชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
            
            # ใช้ปุ่มเขียวในหน้านี้ด้วย
            st.markdown("""<style>.signup-btn-area div[data-testid="stButton"] > button { background-color: #42b72a !important; color: white !important; font-weight: bold !important; height: 48px !important; border-radius: 8px !important; }</style>""", unsafe_allow_html=True)
            st.markdown('<div class="signup-btn-area">', unsafe_allow_html=True)
            if st.form_submit_button("ยืนยันการลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("❌ ชื่อนี้มีคนใช้แล้ว")
            st.markdown('</div>', unsafe_allow_html=True)
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
                <div style="background:white; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); border-left: 6px solid {'#42b72a' if is_done else '#1877f2'}; margin-bottom:12px;">
                    <b style="color:#003366; font-size:18px;">{m['title']}</b><br>
                    <small style="color:{'#42b72a' if is_done else '#1877f2'}; font-weight:bold;">
                        {'✅ ส่งแล้ว' if is_done else '🔵 รอดำเนินการ'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    # ปุ่มส่งงานสีเขียว
                    st.markdown("""<style>.signup-btn-area div[data-testid="stButton"] > button { background-color: #42b72a !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }</style>""", unsafe_allow_html=True)
                    st.markdown('<div class="signup-btn-area">', unsafe_allow_html=True)
                    if st.button(f"ยืนยันส่งภารกิจ {m['id']}", key=f"b{m['id']}", use_container_width=True):
                        with st.spinner("กำลังส่งรูป..."):
                            try:
                                meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                                drive_service.files().create(body=meta, media_body=media).execute()
                                supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id']}).execute()
                                st.success("🎉 สำเร็จ!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
        
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
            ut = st.text_input("ระบุ Username")
            if st.form_submit_button("ค้นหารหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("password").eq("username", ut).execute()
                if res.data: st.success(f"🔑 รหัสคือ: {res.data[0]['password']}")
                else: st.error("❌ ไม่พบข้อมูล")
        if st.button("กลับหน้าหลัก", use_container_width=True): go_to('login')
