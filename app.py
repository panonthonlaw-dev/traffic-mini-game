import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อ (เหมือนเดิม) ---
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

# --- 2. CSS ขั้นพื้นฐาน (เน้นสีและชิดซ้าย ไม่ฝืนโครงสร้าง) ---
st.markdown("""
    <style>
        /* จัดข้อความในช่อง Input ให้ชิดซ้ายตามสั่ง */
        input {
            text-align: left !important;
            padding-left: 15px !important;
        }

        /* ปุ่มสร้างบัญชีใหม่ (สีเขียวอ่อน) */
        div[data-testid="stButton"] > button.green-btn {
            background-color: #b9f6ca !important;
            color: #1b5e20 !important;
            border: 1px solid #a5d6a7 !important;
        }
        
        /* ตกแต่ง Card ภารกิจ */
        .mission-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. ฟังก์ชันจัดองค์ประกอบกึ่งกลาง (The Native Way) ---
def centered_content():
    # แบ่งเป็น 3 คอลัมน์ [ซ้ายว่าง, กลางใช้จริง, ขวาว่าง]
    # สัดส่วน 1:4:1 จะทำให้ส่วนกลางดูเด่นเหมือนแอปมือถือครับ
    return st.columns([1, 4, 1])

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    
    _, col, _ = centered_content()
    
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้")
            p = st.text_input("Password", type="password", placeholder="ระบุรหัสผ่าน")
            # ปุ่มกึ่งกลางด้วยระบบ Form (กว้างเต็มพื้นที่ col กลาง)
            login_btn = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if login_btn:
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("ข้อมูลไม่ถูกต้อง")
        
        st.write("") # เว้นวรรค
        # ปุ่มสร้างบัญชีใหม่ (จัดกึ่งกลาง + สีเขียวอ่อน)
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')
        # ใช้สคริปต์เล็กๆ เปลี่ยนสีปุ่มเฉพาะกิจ
        st.markdown('<style>div.stButton > button:nth-of-type(1) { background-color: #b9f6ca !important; color: #1b5e20 !important; }</style>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = centered_content()
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ระบุชื่อจริง")
            user = st.text_input("ชื่อผู้ใช้", placeholder="ระบุชื่อเข้าระบบ")
            phone = st.text_input("เบอร์โทร", placeholder="ระบุเบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
            if st.form_submit_button("ลงทะเบียน", use_container_width=True):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("สำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อนี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True): go_to('login')

# 🎮 หน้าเล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h4 style='text-align: center;'>สวัสดีคุณ {u['fullname']}</h4>", unsafe_allow_html=True)
    
    _, col, _ = centered_content()
    with col:
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
        done_ids = [s['mission_id'] for s in subs]
        
        for m in missions:
            is_done = m['id'] in done_ids
            st.markdown(f"""
                <div class="mission-card" style="border-left: 5px solid {'#2e7d32' if is_done else '#e53935'};">
                    <b>{m['title']}</b><br>
                    <small>{'✅ ส่งแล้ว' if is_done else '🔴 ยังไม่ได้ส่ง'}</small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    if st.button(f"ยืนยันส่งงาน {m['id']}", key=f"b{m['id']}", use_container_width=True):
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
