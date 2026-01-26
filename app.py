import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time

# --- 1. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมของพี่) ---
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

# --- 2. CSS คุมโทนทั้งเวป (จัดเต็มตามคำขอพี่) ---
st.markdown("""
    <style>
        /* 1. พื้นหลังเวปสีเทาอ่อนเกือบขาว */
        .stApp {
            background-color: #f8f9fa !important;
        }

        /* 2. จัดการช่อง Input (Username / Password) */
        input {
            text-align: left !important;
            padding-left: 15px !important;
            color: #1c3d5a !important; /* สีน้ำเงินเข้ม */
            background-color: white !important;
            border: 1px solid #dcdfe3 !important;
            border-radius: 8px !important;
        }
        
        /* เปลี่ยนสีตัวหนังสือเทาๆ (Placeholder) ให้เป็นสีน้ำเงินจางๆ */
        input::placeholder {
            color: #1c3d5a !important;
            opacity: 0.6;
        }

        /* 3. ปุ่มเข้าสู่ระบบ สีฟ้า #1877f2 */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            border-radius: 8px !important;
        }

        /* 4. ปุ่มสร้างบัญชีใหม่ บังคับเป็นสีเขียว #42b72a (กันสีดำแทรกแซง) */
        .green-btn button {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            border-radius: 8px !important;
        }

        /* 5. ลิงก์ลืมรหัสผ่าน (ไม่มีปุ่ม เป็นแค่ตัวหนังสือสีฟ้า) */
        .forgot-link button {
            background: transparent !important;
            border: none !important;
            color: #1877f2 !important;
            font-size: 14px !important;
            text-decoration: none !important;
            padding: 0 !important;
            margin-top: -10px !important;
        }
        .forgot-link button:hover {
            text-decoration: underline !important;
        }

        /* ตกแต่ง Card ภารกิจ */
        .mission-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 15px;
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

# --- 4. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #1c3d5a; margin-top: 0; font-weight: 500;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    # แบ่งคอลัมน์เพื่อจัดกึ่งกลาง
    _, col, _ = st.columns([1, 6, 1])
    
    with col:
        with st.form("login_form"):
            # ตัวหนังสือในช่องนี้จะเป็นสีฟ้าน้ำเงินเข้ม ชิดซ้ายครับ
            u = st.text_input("Username", placeholder="ชื่อผู้ใช้", label_visibility="collapsed")
            p = st.text_input("Password", placeholder="รหัสผ่าน", type="password", label_visibility="collapsed")
            login_btn = st.form_submit_button("เข้าสู่ระบบ")
            
            if login_btn:
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    go_to('game')
                else: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        
        # ลิงก์ลืมรหัสผ่าน (ตัวหนังสือสีฟ้าใต้ปุ่ม)
        st.markdown('<div class="forgot-link">', unsafe_allow_html=True)
        if st.button("ลืมรหัสผ่านใช่หรือไม่?"):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<hr style='border-top: 1px solid #ddd; margin: 20px 0;'>", unsafe_allow_html=True)
        
        # ปุ่มสร้างบัญชีใหม่ (สีเขียว กึ่งกลาง)
        st.markdown('<div class="green-btn">', unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่"):
            go_to('signup')
        st.markdown('</div>', unsafe_allow_html=True)

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color:#1c3d5a;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 6, 1])
    with col:
        with st.form("signup_form"):
            name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อจริงของคุณ")
            user = st.text_input("ชื่อผู้ใช้", placeholder="ใช้สำหรับเข้าระบบ")
            phone = st.text_input("เบอร์โทร", placeholder="ระบุเบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กำหนดรหัสผ่าน")
            
            st.markdown('<div class="green-btn">', unsafe_allow_html=True)
            if st.form_submit_button("ยืนยันการลงทะเบียน"):
                try:
                    supabase.table("users").insert({"fullname":name,"username":user,"phone":phone,"password":pw}).execute()
                    st.success("✅ ลงทะเบียนสำเร็จ!"); time.sleep(1); go_to('login')
                except: st.error("ชื่อนี้มีคนใช้แล้ว")
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("ย้อนกลับ"): go_to('login')

# 🎮 หน้าหลัก/ภารกิจ
elif st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h3 style='text-align: center; color:#1c3d5a;'>สวัสดีคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 6, 1])
    with col:
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).execute().data
        done_ids = [s['mission_id'] for s in subs]
        
        for m in missions:
            is_done = m['id'] in done_ids
            st.markdown(f"""
                <div class="mission-card" style="border-left: 5px solid {'#42b72a' if is_done else '#1877f2'};">
                    <b style="color:#1c3d5a; font-size: 18px;">{m['title']}</b><br>
                    <span style="color:{'#42b72a' if is_done else '#1877f2'}; font-weight:bold;">
                        {'✅ ส่งสำเร็จแล้ว' if is_done else '🔵 รอการส่งงาน'}
                    </span><br>
                    <small style="color:#666;">{m['description']}</small>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_done:
                f = st.file_uploader(f"ส่งรูป: {m['title']}", type=['jpg','png'], key=f"f{m['id']}")
                if f:
                    st.markdown('<div class="green-btn">', unsafe_allow_html=True)
                    if st.button(f"ส่งภารกิจด่านที่ {m['id']}", key=f"b{m['id']}"):
                        with st.spinner("กำลังอัปโหลด..."):
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
    st.markdown("<h3 style='text-align: center; color:#1c3d5a;'>กู้คืนรหัสผ่าน</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 6, 1])
    with col:
        with st.form("forgot_form"):
            user_target = st.text_input("ระบุ Username")
            if st.form_submit_button("ค้นหารหัสผ่าน"):
                res = supabase.table("users").select("password").eq("username", user_target).execute()
                if res.data: st.success(f"🔑 รหัสผ่านของคุณคือ: {res.data[0]['password']}")
                else: st.error("ไม่พบข้อมูล")
        if st.button("กลับสู่หน้าหลัก"): go_to('login')
