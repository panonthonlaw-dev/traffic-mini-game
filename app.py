import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและการควบคุมหน้าจอผ่าน URL (Query Params) ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# ดักจับการคลิก HTML Link
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 2. การจัดการ Session State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมของพี่) ---
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
    st.error("⚠️ ระบบเชื่อมต่อมีปัญหา กรุณาตรวจสอบรหัสเชื่อมต่อ")
    st.stop()

# --- 4. CSS ปรับแต่งหน้าตา (จัดลิงก์ HTML ให้อยู่กึ่งกลางและสวยงาม) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }
        label { color: #003366 !important; font-weight: bold !important; }

        /* 🔵 ปุ่มหลัก สีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก/ย้อนกลับ) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 สไตล์ลิงก์ HTML จริงๆ */
        .html-link {
            color: #1877f2 !important;
            text-decoration: underline !important;
            font-size: 15px;
            cursor: pointer;
        }
        .html-link:hover { color: #0056b3 !important; }
        
        .status-text { font-size: 14px; font-weight: bold; }
/* 🔗 เพิ่มตัวนี้ต่อท้ายในช่องหมายเลข 4 ของพี่ครับ */
        .mission-link-btn button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #1877f2 !important;
            text-decoration: underline !important;
            font-size: 18px !important;
            cursor: pointer !important;
            display: inline !important;
            box-shadow: none !important;
            font-weight: normal !important;
        }
        .mission-link-btn button:hover {
            color: #0056b3 !important;
            background: none !important;
        }
    </style>
""", unsafe_allow_html=True)

def go_to(page_name):
    st.query_params.clear()
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้")
            p = st.text_input("Password", placeholder="ระบุรหัสผ่าน", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        # ✨ ลิงก์ HTML "ลืมรหัสผ่าน" (อยู่กึ่งกลาง ไม่ใช่ปุ่ม)
        st.markdown("""
            <div style="text-align: center; margin-top: -10px; margin-bottom: 15px;">
                <a href="./?page=forgot" target="_self" class="html-link">คุณลืมรหัสผ่านใช่ไหม</a>
            </div>
        """, unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก (กลับมาครบแล้ว!)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center; color: #003366;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลขเท่านั้น)")
            fullname = st.text_input("ชื่อ-นามสกุล (ภาษาไทย)")
            username = st.text_input("ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
            password = st.text_input("รหัสผ่าน (6-12 ตัว)", type="password")
            confirm_pw = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password")
            
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                if sid.isdigit() and re.match(r'^[ก-ฮะ-์\s]+$', fullname) and password == confirm_pw:
                    try:
                        supabase.table("users").insert({
                            "student_id": sid, "fullname": fullname, "username": username,
                            "phone": phone, "password": password, "role": "player"
                        }).execute()
                        st.success("✅ สมัครสมาชิกสำเร็จ!"); time.sleep(1.5); go_to('login')
                    except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                else: st.error("❌ ข้อมูลไม่ถูกต้องตามเงื่อนไข")
        
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"):
            go_to('login')

# 🔑 หน้าลืมรหัสผ่าน (กลับมาครบแล้ว!)
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            u_check = st.text_input("ระบุ Username")
            s_check = st.text_input("ระบุรหัสนักเรียน")
            t_check = st.text_input("ระบุเบอร์โทรศัพท์")
            new_pw = st.text_input("ตั้งรหัสผ่านใหม่", type="password")
            confirm_new_pw = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
            
            if st.form_submit_button("อัปเดตรหัสผ่าน", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_check).eq("student_id", s_check).eq("phone", t_check).execute()
                if res.data and new_pw == confirm_new_pw:
                    supabase.table("users").update({"password": new_pw}).eq("username", u_check).execute()
                    st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!"); time.sleep(1.5); go_to('login')
                else: st.error("❌ ข้อมูลยืนยันตัวตนไม่ถูกต้อง")
        
        # ✨ ลิงก์ HTML ย้อนกลับ
        st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <a href="./?page=login" target="_self" class="html-link">ยกเลิกและย้อนกลับ</a>
            </div>
        """, unsafe_allow_html=True)

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    if st.session_state.selected_mission is None:
        st.markdown(f"<h3 style='text-align: center;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("### 🚦 เลือกกิจกรรมประจำวัน")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        for m in missions:
            is_done = m['id'] in done_ids
            status = '<span style="color:#42b72a;">(✅ ส่งแล้ว)</span>' if is_done else '<span style="color:#888;">(⭕ รอดำเนินการ)</span>'
            
            # --- แก้ไขจากตรงนี้ ---
            # ใช้ st.button ที่แต่งให้เหมือนลิงก์ เพื่อไม่ให้ Session หลุดตอนเปลี่ยนหน้า
            st.markdown('<div class="mission-link-btn">', unsafe_allow_html=True)
            if st.button(f"📍 {m['title']}", key=f"m_link_{m['id']}"):
                st.session_state.selected_mission = m['id']
                st.rerun() # สั่งรีรันภายในแอป (เบราว์เซอร์ไม่รีเฟรช ข้อมูล Login ไม่หาย)
            st.markdown(f' {status} </div>', unsafe_allow_html=True)
            # ---------------------
            
    else:
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        st.info(f"💡 **วิธีทำกิจกรรม:** {m_data.get('description', 'ถ่ายรูปกิจกรรมแล้วแนบไฟล์ผ่านระบบ')}")
        
        today = datetime.now().strftime("%Y-%m-%d")
        sub_check = supabase.table("submissions").select("*").eq("user_username", u['username']).eq("mission_id", m_id).gte("created_at", today).execute().data
        
        if sub_check:
            st.success("✅ วันนี้คุณส่งกิจกรรมนี้เรียบร้อยแล้ว!")
        else:
            f = st.file_uploader("📸 แนบรูปถ่ายกิจกรรม (JPG/PNG)", type=['jpg','png','jpeg'])
            if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
                with st.spinner("กำลังส่ง..."):
                    filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                    meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                    drive_service.files().create(body=meta, media_body=media).execute()
                    supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m_id}).execute()
                    st.success("🎉 สำเร็จ!"); time.sleep(1.5); go_to('game')
        
        # ✨ ลิงก์ HTML ย้อนกลับ
        st.markdown('<br><a href="./?page=game" target="_self" class="html-link">⬅️ กลับไปหน้ารายชื่อกิจกรรม</a>', unsafe_allow_html=True)

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        go_to('login')

# 🛠️ หน้าหลังบ้าน (Admin)
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.user is None or st.session_state.user['role'] != 'admin': go_to('login')
    st.markdown("<h2>ระบบจัดการหลังบ้าน (Admin)</h2>", unsafe_allow_html=True)
    st.write(f"ผู้ดูแล: {st.session_state.user['fullname']}")
    # ที่นี่จะเป็นที่สำหรับดึงข้อมูลมาโชว์แอดมิน
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        go_to('login')
