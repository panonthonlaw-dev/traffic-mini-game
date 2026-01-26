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

# --- 2. การเชื่อมต่อระบบ (ใช้ข้อมูลเดิมของพี่) ---
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

# --- 3. CSS ฉบับ "ฆ่าปุ่มให้เป็นลิงก์" ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูลขาว ชิดซ้าย */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }

        /* 🔵 ปุ่มเข้าสู่ระบบ สีฟ้า (อันนี้คงไว้เพราะเป็นปุ่มหลัก) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 ลอกคราบปุ่มให้เป็น "ตัวหนังสือลิงก์" 100% */
        .html-link button {
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
        .html-link button:hover {
            text-decoration: underline !important;
            background: none !important;
        }
        
        .status-done { color: #42b72a; font-weight: bold; font-size: 14px; }
        .status-pending { color: #888; font-size: 14px; }
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
        
        # ลิงก์ลืมรหัส (ตัวหนังสือเพียวๆ)
        st.markdown('<div class="html-link" style="text-align: center; margin-top: -10px;">', unsafe_allow_html=True)
        if st.button("คุณลืมรหัสผ่านใช่ไหม", key="forgot_link"):
            go_to('forgot')
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    # --- กรณีหน้าเลือกด่าน ---
    if st.session_state.selected_mission is None:
        st.markdown(f"<h3 style='text-align: center;'>กิจกรรมของคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("### 🚦 รายการกิจกรรมวันนี้")
        
        # ดึงภารกิจและเช็คสถานะการส่งของวันนี้
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        for m in missions:
            is_done = m['id'] in done_ids
            col1, col2 = st.columns([0.7, 0.3])
            
            with col1:
                st.markdown('<div class="html-link">', unsafe_allow_html=True)
                # ลิงก์ตัวหนังสือชื่อกิจกรรม
                if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # แสดงสถานะ
                if is_done: st.markdown('<p class="status-done">✅ ส่งแล้ว</p>', unsafe_allow_html=True)
                else: st.markdown('<p class="status-pending">⭕ รอดำเนินการ</p>', unsafe_allow_html=True)
            
    # --- กรณีหน้าทำกิจกรรม ---
    else:
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        st.info(f"💡 **วิธีทำ:** {m_data.get('description', 'ถ่ายรูปกิจกรรมและแนบไฟล์')}")
        
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
        
        # ลิงก์ย้อนกลับ (ตัวหนังสือ)
        st.markdown('<div class="html-link">', unsafe_allow_html=True)
        if st.button("⬅️ กลับไปหน้ารายชื่อกิจกรรม", key="back_to_list"):
            st.session_state.selected_mission = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): st.session_state.user = None; go_to('login')

# 🟢 หน้า Signup / Forgot (ดึงโค้ดเดิมมาใส่ได้เลยครับ ผมละไว้เพื่อความกระชับ)
# ... [ใส่โค้ด Signup และ Forgot ของเดิมลงไปได้เลยครับ] ...
