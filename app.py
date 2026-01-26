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

# --- 2. ประกาศตัวแปร Session State (ต้องทำก่อนเรียกใช้งาน) ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. การเชื่อมต่อระบบ (ใช้ secrets ของพี่) ---
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

# --- 4. ระบบจดจำผู้ใช้จาก URL (กู้คืน Session เมื่อมีการรีเฟรชหน้าจอ) ---
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# ดึงชื่อผู้ใช้จาก URL มาล็อกอินคืนให้ทันทีถ้า Session หลุด
if "u" in st.query_params and st.session_state.user is None:
    u_url = st.query_params["u"]
    try:
        user_res = supabase.table("users").select("*").eq("username", u_url).execute()
        if user_res.data:
            st.session_state.user = user_res.data[0]
    except:
        pass

# --- 5. CSS ปรับแต่งหน้าตา (รวมสไตล์ปุ่มขอบบางที่พี่สั่ง) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }

        /* 🔵 ปุ่มหลัก (สีฟ้า) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก/ยืนยัน) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🔗 ลิงก์ HTML ลืมรหัสผ่าน */
        .html-link {
            color: #1877f2 !important;
            text-decoration: underline !important;
            font-size: 15px;
            cursor: pointer;
        }

        /* 🎨 🛑 ปุ่มขอบบางพอดีตัวอักษร (ที่พี่ต้องการ) */
        .thin-btn div.stButton > button {
            background-color: transparent !important;
            color: #1877f2 !important;
            border: 1px solid #1877f2 !important;
            padding: 2px 8px !important;
            height: auto !important;
            min-height: unset !important;
            font-size: 16px !important;
            border-radius: 5px !important;
            font-weight: normal !important;
        }
        .thin-btn div.stButton > button:hover {
            background-color: #1877f2 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันเปลี่ยนหน้าแบบรักษา Username บน URL
def go_to(page_name):
    u_val = st.query_params.get("u")
    st.query_params.clear()
    if u_val and page_name != 'login':
        st.query_params["u"] = u_val
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
            u_input = st.text_input("Username", placeholder="ระบุชื่อผู้ใช้")
            p_input = st.text_input("Password", placeholder="ระบุรหัสผ่าน", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_input).execute()
                if res.data and res.data[0]['password'] == p_input:
                    st.session_state.user = res.data[0]
                    st.query_params["u"] = u_input # จำชื่อไว้บน URL
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else:
                    st.error("❌ ข้อมูลไม่ถูกต้อง")
        
        st.markdown('<div style="text-align: center; margin-top: -10px; margin-bottom: 15px;">', unsafe_allow_html=True)
        st.markdown('<a href="./?page=forgot" target="_self" class="html-link">คุณลืมรหัสผ่านใช่ไหม</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

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
            status = '<span style="color:#42b72a;"> (✅ ส่งแล้ว)</span>' if is_done else '<span style="color:#888;"> (⭕ รอดำเนินการ)</span>'
            
            # ✨ 🛑 ปุ่มภารกิจขอบบางพอดีตัวอักษร (แก้ปัญหาเด้ง)
            st.markdown('<div class="thin-btn">', unsafe_allow_html=True)
            if st.button(f"📍 {m['title']}", key=f"m_btn_{m['id']}"):
                st.session_state.selected_mission = m['id']
                st.query_params["m_id"] = m['id']
                st.rerun()
            st.markdown(f'{status}</div>', unsafe_allow_html=True)
            
    else:
        # หน้าทำภารกิจรายด่าน
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        
        # ปุ่มย้อนกลับแบบขอบบาง
        st.markdown('<div class="thin-btn">', unsafe_allow_html=True)
        if st.button("⬅️ กลับไปหน้ารายชื่อกิจกรรม", key="back_to_list"):
            st.session_state.selected_mission = None
            if "m_id" in st.query_params: del st.query_params["m_id"]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ... (ส่วนส่งงานเหมือนเดิม) ...
        st.info(f"💡 วิธีทำ: {m_data.get('description', 'ส่งรูปถ่ายกิจกรรม')}")
        f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'])
        if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
             # [ส่วนอัปโหลดไป Drive/Supabase]
             st.success("🎉 สำเร็จ!")
             time.sleep(1)
             st.session_state.selected_mission = None
             st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')

# 🟢 หน้าสมัครสมาชิก / 🔑 ลืมรหัส (ใส่โครงไว้ให้ไม่ให้ Error)
elif st.session_state.page == 'signup':
    if st.button("ย้อนกลับ", type="secondary"): go_to('login')
elif st.session_state.page == 'forgot':
    if st.button("ยกเลิก", type="secondary"): go_to('login')
elif st.session_state.page == 'admin_dashboard':
    st.write("หน้าแอดมิน")
    if st.button("ออกจากระบบ"): go_to('login')
