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

# --- 2. Session State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. การเชื่อมต่อระบบ ---
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
        if user_res.data: st.session_state.user = user_res.data[0]
    except: pass

# --- 4. CSS (คงสไตล์เดิม และเพิ่มสไตล์ EXP Card) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* 💳 EXP Card Style */
        .exp-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            border-left: 5px solid #1877f2;
        }
        
        /* 🔵 ปุ่มภารกิจกรอบเขียวจิ๋ว */
        .thin-btn-green div.stButton > button {
            background-color: transparent !important;
            color: #42b72a !important;
            border: 1px solid #42b72a !important;
            padding: 0px 8px !important;
            height: 30px !important;
            font-size: 13px !important;
            border-radius: 5px !important;
        }

        .status-right {
            font-size: 13px !important;
            line-height: 30px;
            text-align: right;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

def go_to(page_name):
    u_val = st.query_params.get("u")
    st.query_params.clear()
    if u_val and page_name != 'login': st.query_params["u"] = u_val
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
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_input).execute()
                if res.data and res.data[0]['password'] == p_input:
                    st.session_state.user = res.data[0]
                    st.query_params["u"] = u_input 
                    go_to('admin_dashboard' if res.data[0]['role'] == 'admin' else 'game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        if st.button("สมัครสมาชิก", use_container_width=True): go_to('signup')

# 🎮 หน้ากิจกรรมหลัก (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: go_to('login')
    u = st.session_state.user
    
    if st.session_state.selected_mission is None:
        # --- ✨ ส่วนใหม่: คำนวณ EXP จากคะแนนที่แอดมินให้ ---
        # สมมติว่าในตาราง submissions มีคอลัมน์ points
        sub_data = supabase.table("submissions").select("points").eq("user_username", u['username']).execute().data
        total_exp = sum(item['points'] for item in sub_data if item['points'])
        level = (total_exp // 100) + 1
        exp_in_level = total_exp % 100

        # --- 💳 แสดง EXP Card ---
        st.markdown(f"""
            <div class="exp-card">
                <h3 style='margin:0; color:#1877f2;'>Lv. {level} | {u['fullname']}</h3>
                <p style='margin:0; color:#666; font-size:14px;'>EXP รวม: {total_exp}</p>
            </div>
        """, unsafe_allow_html=True)
        st.progress(exp_in_level / 100)
        
        st.write("---")
        st.subheader("🚦 ภารกิจของฉัน")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("*").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_dict = {s['mission_id']: s for s in subs}

        for m in missions:
            m_sub = done_dict.get(m['id'])
            c1, c2 = st.columns([0.7, 0.3])
            with c1:
                st.markdown('<div class="thin-btn-green">', unsafe_allow_html=True)
                if st.button(f"📍 {m['title']}", key=f"m_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                if m_sub:
                    pts = m_sub.get('points', 0)
                    status_text = f"✅ {pts} EXP" if pts > 0 else "⭕ รอตรวจ"
                    st.markdown(f'<div class="status-right" style="color:#42b72a;">{status_text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-right" style="color:#888;">⭕ รอยืนยัน</div>', unsafe_allow_html=True)
            
    else:
        # --- หน้าทำภารกิจ ---
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"### {m_data['title']}")
        if st.button("⬅️ ย้อนกลับ"): st.session_state.selected_mission = None; st.rerun()
        
        st.info(f"💡 วิธีทำ: {m_data.get('description', 'ส่งรูปถ่ายกิจกรรม')}")
        f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'])
        
        if f:
            if st.button("ส่งภารกิจ", kind="secondary", use_container_width=True):
                with st.spinner("กำลังส่ง..."):
                    today = datetime.now().strftime("%Y-%m-%d")
                    filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                    meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                    media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                    drive_service.files().create(body=meta, media_body=media).execute()
                    # บันทึกลง Supabase โดยให้ points = 0 และ status = pending
                    supabase.table("submissions").insert({
                        "user_username": u['username'], 
                        "mission_id": m_id,
                        "points": 0,
                        "status": "pending"
                    }).execute()
                    st.success("🎉 ส่งงานแล้ว! รอแอดมินให้คะแนนนะครับ"); time.sleep(1); st.session_state.selected_mission = None; st.rerun()

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')

# 🛠️ หน้าหลังบ้าน (Admin) - สำหรับตรวจงาน
elif st.session_state.page == 'admin_dashboard':
    st.title("👨‍🏫 ระบบหลังบ้านแอดมิน")
    st.write("ภารกิจที่รอการตรวจ:")
    # ดึงงานที่ status = 'pending' มาแสดง
    pending_subs = supabase.table("submissions").select("*, users(fullname)").eq("status", "pending").execute().data
    
    for sub in pending_subs:
        with st.expander(f"งานจาก: {sub['users']['fullname']} (ภารกิจ ID: {sub['mission_id']})"):
            # ในโปรเจกต์จริง พี่สามารถดึงรูปมาโชว์ตรงนี้ได้
            score = st.number_input(f"ให้คะแนน EXP (0-100)", min_value=0, max_value=100, key=f"score_{sub['id']}")
            if st.button(f"ยืนยันคะแนน", key=f"btn_{sub['id']}"):
                supabase.table("submissions").update({"points": score, "status": "approved"}).eq("id", sub['id']).execute()
                st.success("ให้คะแนนสำเร็จ!"); time.sleep(0.5); st.rerun()

    if st.button("ออกจากระบบ"): go_to('login')

# หน้า Signup / Forgot (คงเดิม)
elif st.session_state.page == 'signup':
    if st.button("⬅️ ย้อนกลับ"): go_to('login')
