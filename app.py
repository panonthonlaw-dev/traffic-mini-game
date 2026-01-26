import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ ---
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

# --- 2. CSS คุมโทนสี (แบบไม่ฝืน Layout) ---
st.markdown(f"""
    <style>
        /* 1. พื้นหลังเทาอ่อนเกือบขาว */
        .stApp {{
            background-color: #fcfcfc;
        }}

        /* 2. ช่อง Input: ตัวหนังสือสีฟ้าน้ำเงินเข้ม และชิดซ้าย */
        input {{
            color: #003366 !important;
            text-align: left !important;
        }}
        
        /* 3. ปุ่มเข้าสู่ระบบ (สีฟ้าเดียวกับหัวข้อ) */
        div[data-testid="stFormSubmitButton"] > button {{
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }}

        /* 4. ปุ่มสร้างบัญชีใหม่ (สีเขียว) */
        div.stButton > button[kind="secondary"] {{
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }}

        /* 5. ตัวหนังสือลืมรหัสผ่าน สีฟ้าตัวเล็ก */
        .forgot-link {{
            color: #1877f2;
            font-size: 0.85rem;
            text-align: center;
            display: block;
            margin-top: -15px;
            text-decoration: none;
        }}
        
        .mission-card {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #eee;
            margin-bottom: 10px;
        }}
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. การแสดงผล ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    # หัวข้อกึ่งกลาง
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#666;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)

    # ใช้ columns จัดกึ่งกลาง [ว่าง, เนื้อหา, ว่าง]
    _, col, _ = st.columns([1, 4, 1])
    
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
                else: st.error("ข้อมูลไม่ถูกต้อง")
        
        # ลิงก์ลืมรหัสผ่าน (สีฟ้าตัวเล็ก)
        st.markdown(f'<a href="javascript:void(0)" class="forgot-link">ลืมรหัสผ่านใช่หรือไม่?</a>', unsafe_allow_html=True)
        # หมายเหตุ: Streamlit ไม่รองรับลิงก์รันโค้ดตรงๆ ถ้าพี่อยากให้กดได้จริงๆ ให้ใช้ st.button แบบใสครับ
        if st.button("คลิกเพื่อกู้คืนรหัสผ่าน", type="link"):
            go_to('forgot')
            
        st.write("---")
        
        # ปุ่มสร้างบัญชี (สีเขียว)
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="Username")
            phone = st.text_input("เบอร์โทร", placeholder="Phone")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password")
            if st.form_submit_button("ลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อนี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 5, 1])
    with col:
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
        done_ids = [s['mission_id'] for s in subs]
        
        for m in missions:
            is_done = m['id'] in done_ids
            st.markdown(f"""
                <div class="mission-card" style="border-left: 5px solid {'#42b72a' if is_done else '#1877f2'};">
                    <b>{m['title']}</b><br>
                    <small>{'✅ ส่งแล้ว' if is_done else '🔵 รอดำเนินการ'}</small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    if st.button(f"ยืนยันส่งงาน {m['id']}", key=f"b{m['id']}", use_container_width=True, type="secondary"):
                        with st.spinner("กำลังอัปโหลด..."):
                            try:
                                meta = {'name': f"{u['username']}_m{m['id']}.jpg", 'parents': [DRIVE_FOLDER_ID]}
                                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                                drive_service.files().create(body=meta, media_body=media).execute()
                                supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m['id']}).execute()
                                st.success("สำเร็จ!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

        st.write("---")
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h3 style='text-align: center;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("f"):
            ut = st.text_input("ระบุ Username")
            if st.form_submit_button("ค้นหา", use_container_width=True):
                res = supabase.table("users").select("password").eq("username", ut).execute()
                if res.data: st.success(f"รหัสผ่านคือ: {res.data[0]['password']}")
                else: st.error("ไม่พบข้อมูล")
        if st.button("กลับ", use_container_width=True): go_to('login')
