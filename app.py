import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. การเชื่อมต่อระบบ ---
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
    st.error(f"⚠️ ระบบเชื่อมต่อมีปัญหา")
    st.stop()

# --- 3. CSS ฉบับลอกคราบปุ่มให้เป็น "ตัวหนังสือคลิกได้" 100% ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูลขาว ชิดซ้าย */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }
        label { color: #003366 !important; font-weight: bold !important; }

        /* 🔵 ปุ่มเข้าสู่ระบบ สีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 ลอกคราบปุ่มให้เป็น "ตัวหนังสือลิงก์" (สำหรับลืมรหัส และ รายชื่อด่าน) */
        .text-link-only button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #1877f2 !important;
            text-decoration: none !important;
            box-shadow: none !important;
            font-size: 16px !important;
            height: auto !important;
            min-height: unset !important;
            text-align: left !important;
        }
        .text-link-only button:hover {
            text-decoration: underline !important;
            background: none !important;
        }
        
        .instruction-box {
            background-color: #e3f2fd; padding: 15px; border-radius: 12px;
            border-left: 6px solid #1877f2; margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 5. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="Username")
            p = st.text_input("Password", placeholder="Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).execute()
                if res.data and res.data[0]['password'] == p:
                    st.session_state.user = res.data[0]
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        # ลิงก์ลืมรหัส (ใช้ CSS ลอกคราบปุ่ม)
        st.markdown('<div class="text-link-only" style="text-align: center; margin-top: -10px;">', unsafe_allow_html=True)
        if st.button("คุณลืมรหัสผ่านใช่ไหม"):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลขเท่านั้น)")
            fullname = st.text_input("ชื่อ-นามสกุล (ไทย)")
            user = st.text_input("Username (6-12 ตัว)")
            phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
            pw = st.text_input("Password", type="password")
            cpw = st.text_input("ยืนยัน Password", type="password")
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                if sid.isdigit() and re.match(r'^[ก-ฮะ-์\s]+$', fullname) and pw == cpw:
                    try:
                        supabase.table("users").insert({"student_id": sid, "fullname": fullname, "username": user, "phone": phone, "password": pw, "role": "player"}).execute()
                        st.success("✅ สมัครสำเร็จ!"); time.sleep(1); go_to('login')
                    except: st.error("❌ ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            u_check = st.text_input("Username")
            s_check = st.text_input("รหัสนักเรียน")
            t_check = st.text_input("เบอร์โทร")
            new_pw = st.text_input("รหัสผ่านใหม่", type="password")
            confirm_pw = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
            if st.form_submit_button("อัปเดตรหัสผ่าน"):
                res = supabase.table("users").select("*").eq("username", u_check).eq("student_id", s_check).eq("phone", t_check).execute()
                if res.data and new_pw == confirm_pw:
                    supabase.table("users").update({"password": new_pw}).eq("username", u_check).execute()
                    st.success("✅ เปลี่ยนรหัสสำเร็จ!"); time.sleep(1); go_to('login')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        if st.button("ยกเลิก", use_container_width=True, type="secondary"): go_to('login')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    # --- กรณีที่ยังไม่เลือกด่าน (โชว์รายชื่อลิงก์) ---
    if st.session_state.selected_mission is None:
        st.markdown(f"<h3 style='text-align: center;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("### 🚦 กิจกรรมวันนี้")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        for m in missions:
            st.markdown('<div class="text-link-only">', unsafe_allow_html=True)
            # ใช้ปุ่มที่ลอกคราบแล้ว แทน HTML Link เพื่อไม่ให้ Session หลุด
            if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                st.session_state.selected_mission = m['id']
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
    # --- กรณีที่เลือกด่านแล้ว (โชว์รายละเอียดด่าน) ---
    else:
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f'<div class="instruction-box"><b>วิธีทำกิจกรรม:</b> {m_data.get("description", "ถ่ายรูปและแนบไฟล์เพื่อทำภารกิจ")}</div>', unsafe_allow_html=True)
        
        # เช็คกฎ 1 ครั้ง/วัน
        today = datetime.now().strftime("%Y-%m-%d")
        sub_check = supabase.table("submissions").select("*").eq("user_username", u['username']).eq("mission_id", m_id).gte("created_at", today).execute().data
        
        if sub_check:
            st.success("✅ วันนี้คุณทำกิจกรรมนี้สำเร็จแล้ว!")
        else:
            f = st.file_uploader("📸 แนบรูปถ่ายกิจกรรม", type=['jpg','png','jpeg'])
            if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
                with st.spinner("กำลังส่ง..."):
                    filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                    meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                    drive_service.files().create(body=meta, media_body=media).execute()
                    supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m_id}).execute()
                    st.success("🎉 สำเร็จ!"); time.sleep(1); st.session_state.selected_mission = None; st.rerun()
        
        if st.button("⬅️ กลับไปหน้ากิจกรรม", use_container_width=True):
            st.session_state.selected_mission = None
            st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): st.session_state.user = None; go_to('login')

# 🛠️ หน้าหลังบ้าน (Admin)
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.user is None or st.session_state.user['role'] != 'admin': go_to('login')
    st.markdown("<h2>Back-End Admin</h2>", unsafe_allow_html=True)
    if st.button("ออกจากระบบ", use_container_width=True): st.session_state.user = None; go_to('login')
