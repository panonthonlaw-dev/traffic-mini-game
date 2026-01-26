import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมที่พี่ตั้งค่าไว้) ---
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

# --- 2. CSS ปรับแต่งตามคำขอของพี่ ---
st.markdown("""
    <style>
        /* บีบหน้าแอปให้เล็กลงเหมือนมือถือและจัดกึ่งกลาง */
        .block-container {
            max-width: 400px !important;
            padding-top: 3rem !important;
            margin: auto !important;
        }

        /* จัดปุ่มทั้งหมดให้อยู่กึ่งกลาง (กว้างเต็มกรอบที่อยู่กึ่งกลาง) */
        .stButton button {
            display: block !important;
            margin: 0 auto !important;
            width: 100% !important;
            border-radius: 12px !important;
            height: 50px !important;
            font-weight: bold !important;
        }

        /* ปุ่มเข้าสู่ระบบ (สีฟ้า) */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
        }

        /* ปุ่มสร้างบัญชีใหม่ (สีเขียวอ่อน) */
        .signup-btn button {
            background-color: #b9f6ca !important; /* สีเขียวอ่อน */
            color: #1b5e20 !important; /* ตัวหนังสือสีเขียวเข้มเพื่อให้ชัดเจน */
            border: 1px solid #a5d6a7 !important;
        }

        /* ช่องกรอกข้อมูล: ตัวหนังสือชิดซ้าย (ทั้งที่พิมพ์และตัวหนังสือเทาๆ) */
        input {
            text-align: left !important;
            padding-left: 15px !important;
            border-radius: 10px !important;
            height: 45px !important;
        }

        /* ตกแต่ง Card ภารกิจให้ดูสบายตา */
        .mission-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. ส่วนการแสดงผลแต่ละหน้า ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>ระบบรายงานภารกิจจราจร</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        # ช่องชื่อผู้ใช้และรหัสผ่าน ตัวหนังสือจะชิดซ้ายตามสั่งครับ
        u = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้")
        p = st.text_input("Password", type="password", placeholder="ระบุรหัสผ่าน")
        
        # ปุ่มเข้าสู่ระบบอยู่กึ่งกลาง
        login_btn = st.form_submit_button("เข้าสู่ระบบ")
        
        if login_btn:
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                go_to('game')
            else: st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            
    st.markdown("<hr style='border-top: 1px solid #eee; margin: 25px 0;'>", unsafe_allow_html=True)
    
    # ปุ่มสร้างบัญชีใหม่ กึ่งกลาง + สีเขียวอ่อน
    st.markdown('<div class="signup-btn">', unsafe_allow_html=True)
    if st.button("สร้างบัญชีใหม่"):
        go_to('signup')
    st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    with st.form("signup_form"):
        name = st.text_input("ชื่อ-นามสกุล", placeholder="ระบุชื่อจริง")
        user = st.text_input("ชื่อผู้ใช้", placeholder="ระบุชื่อสำหรับเข้าระบบ")
        phone = st.text_input("เบอร์โทร", placeholder="ระบุเบอร์โทรศัพท์")
        pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
        
        st.markdown('<div class="signup-btn">', unsafe_allow_html=True)
        if st.form_submit_button("ยืนยันลงทะเบียน"):
            try:
                supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                st.success("ลงทะเบียนสำเร็จ!"); time.sleep(1); go_to('login')
            except: st.error("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว")
        st.markdown('</div>', unsafe_allow_html=True)
    if st.button("ย้อนกลับหน้าหลัก"): go_to('login')

# 🎮 หน้าหลัก/เล่นเกม
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center;'>ยินดีต้อนรับคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
    subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
    done_ids = [s['mission_id'] for s in subs]
    
    for m in missions:
        is_done = m['id'] in done_ids
        st.markdown(f"""
            <div class="mission-card" style="background:{'#f1f8e9' if is_done else 'white'}">
                <b style="font-size: 18px;">{m['title']}</b><br>
                <span style="color:{'#2e7d32' if is_done else '#e53935'}; font-weight:bold;">
                    {'✅ ส่งภารกิจแล้ว' if is_done else '🔴 ยังไม่ได้ส่ง'}
                </span><br>
                <small>{m['description']}</small>
            </div>
        """, unsafe_allow_html=True)
        
        if not is_done:
            f = st.file_uploader(f"เลือกรูปภาพ: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
            if f:
                st.markdown('<div class="signup-btn">', unsafe_allow_html=True)
                if st.button(f"ส่งภารกิจ {m['id']}", key=f"b{m['id']}"):
                    with st.spinner("กำลังอัปโหลดรูปภาพ..."):
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
    if st.button("ออกจากระบบ"):
        st.session_state.user = None
        go_to('login')
