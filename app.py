import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re
from datetime import datetime

# --- 1. ระบบควบคุมหน้าจอผ่าน URL (Query Params) ---
# ตัวนี้จะทำหน้าที่ดักจับว่าลิงก์ HTML <a> ถูกกดหรือไม่
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 2. ตั้งค่าพื้นฐานและ Session ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

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
    st.error("⚠️ ระบบเชื่อมต่อมีปัญหา")
    st.stop()

# --- 4. CSS ปรับแต่งหน้าตา ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ช่องกรอกข้อมูล */
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }

        /* 🔵 ปุ่มหลัก (เข้าสู่ระบบ) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว (สมัครสมาชิก) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* จัดสไตล์ลิงก์ HTML */
        .html-a-link {
            color: #1877f2 !important;
            text-decoration: underline !important;
            font-size: 15px;
            cursor: pointer;
        }
        .html-a-link:hover { color: #0056b3 !important; }
    </style>
""", unsafe_allow_html=True)

def go_to(page_name):
    st.query_params.clear()
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 5. การแสดงผลแต่ละหน้า ---

# 🔵 หน้า LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 style='text-align: center; color:#1877f2;'>traffic game</h1>", unsafe_allow_html=True)
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
        
        # ✨ ลิงก์ HTML ลืมรหัสผ่าน (อยู่ตรงกลาง ไม่ใช่ปุ่ม)
        st.markdown("""
            <div style="text-align: center; margin-top: -10px; margin-bottom: 15px;">
                <a href="./?page=forgot" target="_self" class="html-a-link">คุณลืมรหัสผ่านใช่ไหม</a>
            </div>
        """, unsafe_allow_html=True)

        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"):
            go_to('signup')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    # --- กรณีหน้ารายชื่อภารกิจ ---
    if st.session_state.selected_mission is None:
        st.markdown(f"<h3 style='text-align: center;'>ภารกิจของคุณ {u['fullname']}</h3>", unsafe_allow_html=True)
        st.write("---")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        for m in missions:
            is_done = m['id'] in done_ids
            status = '<span style="color:#42b72a;">(✅ ส่งแล้ว)</span>' if is_done else '<span style="color:#888;">(⭕ รอดำเนินการ)</span>'
            
            # ✨ ลิงก์ HTML รายชื่อกิจกรรม (ไม่ใช่ปุ่ม)
            st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <a href="./?page=game&m_id={m['id']}" target="_self" class="html-a-link">📍 {m['title']}</a> 
                    {status}
                </div>
            """, unsafe_allow_html=True)
            
    # --- กรณีหน้าทำกิจกรรม ---
    else:
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        st.info(f"💡 **วิธีทำ:** {m_data.get('description', 'ถ่ายรูปกิจกรรมแล้วแนบไฟล์')}")
        
        # เช็คการส่งวันนี้
        today = datetime.now().strftime("%Y-%m-%d")
        sub_check = supabase.table("submissions").select("*").eq("user_username", u['username']).eq("mission_id", m_id).gte("created_at", today).execute().data
        
        if sub_check:
            st.success("✅ วันนี้ส่งกิจกรรมนี้เรียบร้อยแล้ว")
        else:
            f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'])
            if f and st.button("ยืนยันส่งงาน", type="secondary", use_container_width=True):
                # ... (โค้ดอัปโหลด Drive/Supabase เหมือนเดิม) ...
                st.success("🎉 สำเร็จ!"); time.sleep(1); go_to('game')
        
        # ✨ ลิงก์ HTML ย้อนกลับ (ไม่ใช่ปุ่ม)
        st.markdown('<br><a href="./?page=game" target="_self" class="html-a-link">⬅️ กลับไปหน้ารายชื่อกิจกรรม</a>', unsafe_allow_html=True)

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): st.session_state.user = None; go_to('login')

# 🟢 หน้าสมัครสมาชิก / กู้รหัส (ดึงโค้ดเดิมมาใส่ได้เลยครับ)
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    if st.button("ย้อนกลับ", type="secondary", use_container_width=True): go_to('login')

elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    if st.button("ยกเลิก", type="secondary", use_container_width=True): go_to('login')
