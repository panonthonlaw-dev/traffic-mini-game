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

# --- 2. ประกาศตัวแปร Session State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. ระบบจดจำสถานะผ่าน URL (กันเด้ง) ---
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 4. การเชื่อมต่อระบบ (ใช้ secrets ของพี่) ---
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

# กู้คืน Session จาก URL
if "u" in st.query_params and st.session_state.user is None:
    u_url = st.query_params["u"]
    try:
        user_res = supabase.table("users").select("*").eq("username", u_url).execute()
        if user_res.data:
            st.session_state.user = user_res.data[0]
    except:
        pass

# --- 5. CSS ปรับแต่ง (เน้นภารกิจฟ้าจิ๋ว และชิดกัน) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* 🔵 ปุ่มหลักในฟอร์ม */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 45px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียวรอง */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 45px !important; border-radius: 10px !important;
        }

        /* 🎨 🛑 ปุ่มจิ๋วกรอบฟ้า (แก้ไขสีและขนาดตามสั่ง) */
        .thin-btn-blue div.stButton > button {
            background-color: transparent !important;
            color: #1877f2 !important; /* สีฟ้าโทนเรา */
            border: 1px solid #1877f2 !important; /* กรอบฟ้าบาง 1px */
            padding: 0px 4px !important;
            height: 24px !important; /* จิ๋วลงกว่าเดิม */
            min-height: unset !important;
            font-size: 11px !important; /* ตัวหนังสือเล็กพิเศษ */
            border-radius: 4px !important;
            width: auto !important;
            margin: 0 !important;
        }
        .thin-btn-blue div.stButton > button:hover {
            background-color: #1877f2 !important; color: white !important;
        }

        /* สถานะชิดขวาตัวจิ๋ว */
        .status-mini {
            font-size: 11px !important;
            line-height: 24px;
            text-align: right;
            font-weight: normal;
        }

        /* ❌ ลบช่องว่างระหว่างบรรทัดให้ชิดกันที่สุด */
        [data-testid="column"] {
            padding: 0px !important;
            margin: -8px 0px !important; 
        }
        
        hr { margin: 5px 0px !important; }
    </style>
""", unsafe_allow_html=True)

def go_to(page_name):
    u_val = st.query_params.get("u")
    st.query_params.clear()
    if u_val and page_name != 'login': st.query_params["u"] = u_val
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 6. การแสดงผลหน้าจอ ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_input).execute()
                if res.data and res.data[0]['password'] == p_input:
                    st.session_state.user = res.data[0]
                    st.query_params["u"] = u_input 
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"): go_to('signup')

# 🟢 หน้าสมัครสมาชิก / 🔑 ลืมรหัสผ่าน
elif st.session_state.page == 'signup':
    st.subheader("สมัครสมาชิก")
    # ... ส่วน Signup เดิมของพี่ ...
    if st.button("⬅️ กลับ", type="secondary"): go_to('login')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    if st.session_state.selected_mission is None:
        st.markdown(f"**สวัสดีคุณ {u['fullname']}**")
        st.write("---")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        # วนลูปภารกิจ
        for m in missions:
            is_done = m['id'] in done_ids
            # แบ่งคอลัมน์ 75:25
            c1, c2 = st.columns([0.75, 0.25])
            with c1:
                st.markdown('<div class="thin-btn-blue">', unsafe_allow_html=True)
                if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                col_s = "#42b72a" if is_done else "#888"
                txt_s = "✅ ส่งแล้ว" if is_done else "⭕ รอยืนยัน"
                st.markdown(f'<div class="status-mini" style="color:{col_s};">{txt_s}</div>', unsafe_allow_html=True)
            
    else:
        # --- หน้าทำภารกิจ ---
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"### {m_data['title']}")
        if st.button("⬅️ ย้อนกลับ", key="back"): st.session_state.selected_mission = None; st.rerun()
        
        f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'])
        if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
             # [ส่วนอัปโหลดเหมือนเดิม]
             st.success("🎉 สำเร็จ!"); time.sleep(1); st.session_state.selected_mission = None; st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ"): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')

# 🛠️ Admin Dashboard
elif st.session_state.page == 'admin_dashboard':
    st.write("ระบบจัดการหลังบ้าน")
    if st.button("ออกจากระบบ"): go_to('login')
