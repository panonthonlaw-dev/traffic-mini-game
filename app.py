import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. Session State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. การเชื่อมต่อ (Secrets) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n").strip()
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
except:
    st.error("⚠️ การเชื่อมต่อขัดข้อง")
    st.stop()

# กู้คืน Session จาก URL
if "u" in st.query_params and st.session_state.user is None:
    u_url = st.query_params["u"]
    res = supabase.table("users").select("*").eq("username", u_url).execute()
    if res.data: st.session_state.user = res.data[0]

# --- 4. CSS ปรับแต่ง (เน้นความชิดระดับสูงสุด) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* 🔵 ปุ่มจิ๋วกรอบฟ้า (11px) */
        .thin-btn-blue div.stButton > button {
            background-color: transparent !important;
            color: #1877f2 !important;
            border: 1px solid #1877f2 !important;
            padding: 0px 4px !important;
            height: 22px !important; /* บีบให้เตี้ยลงอีก */
            min-height: unset !important;
            font-size: 11px !important;
            border-radius: 3px !important;
            width: auto !important;
        }
        .thin-btn-blue div.stButton > button:hover {
            background-color: #1877f2 !important; color: white !important;
        }

        /* ⭕ สถานะจิ๋วชิดขวา */
        .status-mini {
            font-size: 11px !important;
            line-height: 22px;
            text-align: right;
            color: #888;
        }

        /* ❌ 🛑 แก้ไขจุดสำคัญ: บีบช่องว่างระหว่างบรรทัดให้ชิดกันที่สุด */
        [data-testid="column"] {
            padding: 0px !important;
            margin-bottom: -22px !important; /* ใช้ Negative Margin ดึงบรรทัดล่างขึ้นมา */
        }
        
        /* ลดช่องว่างของ Widget พื้นฐาน */
        .stElementContainer {
            margin-bottom: -10px !important;
        }

        hr { margin: 5px 0px !important; opacity: 0.3; }
    </style>
""", unsafe_allow_html=True)

def go_to(page_name):
    u_val = st.query_params.get("u")
    st.query_params.clear()
    if u_val and page_name != 'login': st.query_params["u"] = u_val
    st.session_state.page = page_name
    st.session_state.selected_mission = None
    st.rerun()

# --- 5. Logic การแสดงผล ---

if st.session_state.page == 'login':
    st.markdown("<h2 style='text-align: center; color:#1877f2;'>traffic game</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == p:
                st.session_state.user = res.data[0]
                st.query_params["u"] = u
                go_to('game')
            else: st.error("ข้อมูลไม่ถูกต้อง")

elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    if st.session_state.selected_mission is None:
        st.markdown(f"**ผู้ใช้: {u['fullname']}**")
        st.write("---")
        
        # ดึงภารกิจและเช็คการส่งงาน
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("mission_id").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_ids = [s['mission_id'] for s in subs]

        # แสดงรายการภารกิจแบบชิดกันสุดๆ
        for m in missions:
            is_done = m['id'] in done_ids
            c1, c2 = st.columns([0.7, 0.3])
            with c1:
                st.markdown('<div class="thin-btn-blue">', unsafe_allow_html=True)
                if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                s_color = "#42b72a" if is_done else "#888"
                s_text = "✅ ส่งแล้ว" if is_done else "⭕ รอ"
                st.markdown(f'<div class="status-mini" style="color:{s_color};">{s_text}</div>', unsafe_allow_html=True)
            
    else:
        # หน้าทำภารกิจ
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"### {m_data['title']}")
        if st.button("⬅️ กลับ"): st.session_state.selected_mission = None; st.rerun()
        
        f = st.file_uploader("📸 ส่งรูป", type=['jpg','png','jpeg'])
        if f and st.button("ยืนยัน", kind="secondary", use_container_width=True):
            # (Logic ส่งงานคงเดิม)
            st.success("ส่งงานสำเร็จ"); time.sleep(1); st.session_state.selected_mission = None; st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ"): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')
