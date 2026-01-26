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

# --- 2. ประกาศตัวแปร Session State (ต้องทำก่อนเพื่อกัน Error) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. ระบบจดจำสถานะผ่าน URL (กันเด้งตอนรีเฟรช) ---
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 4. การเชื่อมต่อระบบ (Supabase & Google Drive) ---
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
    st.error("⚠️ ระบบเชื่อมต่อมีปัญหา กรุณาตรวจสอบรหัสเชื่อมต่อใน Secrets")
    st.stop()

# กู้คืน Session ผู้ใช้จาก URL
if "u" in st.query_params and st.session_state.user is None:
    u_url = st.query_params["u"]
    try:
        user_res = supabase.table("users").select("*").eq("username", u_url).execute()
        if user_res.data:
            st.session_state.user = user_res.data[0]
    except:
        pass

# --- 5. CSS ปรับแต่งหน้าตา (จัดปุ่มเขียวจิ๋วและสถานะ) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }
        label { color: #003366 !important; font-weight: bold !important; }

        /* 🔵 ปุ่มหลัก สีฟ้า (ในฟอร์ม) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก/ยืนยัน) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 ลิงก์ HTML */
        .html-link { color: #1877f2 !important; text-decoration: underline !important; font-size: 15px; cursor: pointer; }

        /* 🎨 🛑 ปุ่มจิ๋วขอบเขียวบาง (ตามที่พี่สั่ง) */
        .thin-btn-green div.stButton > button {
            background-color: transparent !important;
            color: #42b72a !important;
            border: 1px solid #42b72a !important;
            padding: 0px 8px !important;
            height: 30px !important;
            min-height: unset !important;
            font-size: 13px !important;
            border-radius: 5px !important;
            font-weight: normal !important;
            width: auto !important;
        }
        .thin-btn-green div.stButton > button:hover {
            background-color: #42b72a !important;
            color: white !important;
        }

        /* สไตล์ตัวหนังสือสถานะชิดขวา */
        .status-right {
            font-size: 13px !important;
            line-height: 30px; /* ให้สูงเท่าปุ่มพอดี */
            text-align: right;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันเปลี่ยนหน้า
def go_to(page_name):
    current_u = st.query_params.get("u")
    st.query_params.clear()
    if current_u and page_name != 'login':
        st.query_params["u"] = current_u
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 6. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2; margin-bottom:0;'>traffic game</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #003366; font-weight: bold;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("Username", placeholder="Username")
            p_input = st.text_input("Password", placeholder="Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_input).execute()
                if res.data and res.data[0]['password'] == p_input:
                    st.session_state.user = res.data[0]
                    st.query_params["u"] = u_input 
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        st.markdown('<div style="text-align: center; margin-top: -10px;"><a href="./?page=forgot" target="_self" class="html-link">คุณลืมรหัสผ่านใช่ไหม</a></div>', unsafe_allow_html=True)
        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"): go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลข)")
            fname = st.text_input("ชื่อ-นามสกุล")
            uname = st.text_input("Username")
            phone = st.text_input("เบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password")
            cpw = st.text_input("ยืนยันรหัสผ่าน", type="password")
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                if pw == cpw and sid.isdigit():
                    try:
                        supabase.table("users").insert({"student_id": sid, "fullname": fname, "username": uname, "phone": phone, "password": pw, "role": "player"}).execute()
                        st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                    except: st.error("❌ Username นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            fu = st.text_input("Username")
            fs = st.text_input("รหัสนักเรียน")
            fp = st.text_input("เบอร์โทรศัพท์")
            np = st.text_input("รหัสผ่านใหม่", type="password")
            if st.form_submit_button("อัปเดตรหัสผ่าน"):
                res = supabase.table("users").select("*").eq("username", fu).eq("student_id", fs).eq("phone", fp).execute()
                if res.data:
                    supabase.table("users").update({"password": np}).eq("username", fu).execute()
                    st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        if st.button("ยกเลิก", use_container_width=True, type="secondary"): go_to('login')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    if st.session_state.selected_mission is None:
        st.markdown(f"### สวัสดีคุณ {u['fullname']} 👋")
        st.write("---")
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        for m in missions:
            is_done = m['id'] in done_ids
            # 🏁 แบ่งคอลัมน์: ซ้าย 75% (ปุ่มจิ๋ว) | ขวา 25% (สถานะ)
            c1, c2 = st.columns([0.75, 0.25])
            with c1:
                st.markdown('<div class="thin-btn-green">', unsafe_allow_html=True)
                if st.button(f"📍 {m['title']}", key=f"m_btn_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                status_color = "#42b72a" if is_done else "#888"
                status_text = "✅ ส่งแล้ว" if is_done else "⭕ รอยืนยัน"
                st.markdown(f'<div class="status-right" style="color:{status_color};">{status_text}</div>', unsafe_allow_html=True)
            
    else:
        # หน้าทำภารกิจ
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        
        st.markdown('<div class="thin-btn-green">', unsafe_allow_html=True)
        if st.button("⬅️ ย้อนกลับ", key="back"): st.session_state.selected_mission = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info(f"💡 วิธีทำ: {m_data.get('description', 'ส่งรูปถ่ายกิจกรรม')}")
        f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'])
        if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
            with st.spinner("กำลังอัปโหลด..."):
                today = datetime.now().strftime("%Y-%m-%d")
                filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                drive_service.files().create(body=meta, media_body=media).execute()
                supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m_id}).execute()
                st.success("🎉 สำเร็จ!"); time.sleep(1); st.session_state.selected_mission = None; st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')

# 🛠️ หน้า Admin Dashboard
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.user is None or st.session_state.user['role'] != 'admin': go_to('login')
    st.markdown("<h2>ระบบจัดการหลังบ้าน (Admin)</h2>", unsafe_allow_html=True)
    st.write(f"สวัสดีแอดมิน: {st.session_state.user['fullname']}")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')
