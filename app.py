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
    st.error("⚠️ ระบบเชื่อมต่อมีปัญหา")
    st.stop()

# --- 3. CSS ฉบับ "ถอดรูปปุ่มให้เป็นลิงก์ตัวหนังสือ" ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูลขาว ชิดซ้าย */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }
        label { color: #003366 !important; font-weight: bold !important; }

        /* 🔵 ปุ่มเข้าสู่ระบบ สีฟ้า (คงไว้เป็นปุ่มหลัก) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 🛑 หัวใจหลัก: ล้างคราบปุ่มให้เหลือแต่ตัวหนังสือลิงก์ 100% */
        .pure-html-link button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #1877f2 !important;
            text-decoration: underline !important;
            box-shadow: none !important;
            font-size: 15px !important;
            height: auto !important;
            min-height: unset !important;
            cursor: pointer !important;
            display: inline !important;
            font-weight: normal !important;
        }
        .pure-html-link button:hover {
            color: #0056b3 !important;
            background: none !important;
        }
        
        /* สไตล์สถานะกิจกรรม */
        .status-badge { font-size: 13px; font-weight: bold; margin-left: 10px; }
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
        
        # ✨ ลิงก์ลืมรหัสผ่าน (ตัวหนังสือตรงกลาง ไม่ใช่ปุ่ม)
        st.markdown('<div class="pure-html-link" style="text-align: center; margin-top: -10px;">', unsafe_allow_html=True)
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
    
    if st.session_state.selected_mission is None:
        st.markdown(f"<h3 style='text-align: center;'>สวัสดีคุณ {u['fullname']} 👋</h3>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("### 🚦 รายการกิจกรรม")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        for m in missions:
            is_done = m['id'] in done_ids
            # ✨ รายชื่อด่าน (ตัวหนังสือลิงก์ ไม่ใช่ปุ่ม)
            st.markdown('<div class="pure-html-link" style="margin-bottom: 15px;">', unsafe_allow_html=True)
            status_text = '<span style="color:#42b72a;"> (✅ ส่งแล้ว)</span>' if is_done else '<span style="color:#888;"> (⭕ รอดำเนินการ)</span>'
            
            if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                st.session_state.selected_mission = m['id']
                st.rerun()
            st.markdown(f'{status_text}</div>', unsafe_allow_html=True)
            
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
        
        # ✨ ย้อนกลับแบบตัวหนังสือลิงก์
        st.markdown('<div class="pure-html-link" style="margin-top:20px;">', unsafe_allow_html=True)
        if st.button("⬅️ กลับไปหน้ารายชื่อกิจกรรม", key="back_link"):
            st.session_state.selected_mission = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): st.session_state.user = None; go_to('login')

# 🟢 หน้า Signup / Forgot (ใช้ Logic เดิมที่พี่มี)
elif st.session_state.page == 'signup':
    # ... (ส่วน Signup ที่พี่มีอยู่)
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): go_to('login')

elif st.session_state.page == 'forgot':
    # ... (ส่วน Forgot ที่พี่มีอยู่)
    st.markdown("<h2 style='text-align: center;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    if st.button("ยกเลิก", use_container_width=True, type="secondary"): go_to('login')
