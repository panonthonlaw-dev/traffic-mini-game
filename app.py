import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและการรับค่าจากลิงก์ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# รับค่าจากลิงก์เพื่อเลือกภารกิจ
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 2. การเชื่อมต่อระบบ (คงเดิม) ---
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
    st.error("❌ ระบบเชื่อมต่อผิดพลาด")
    st.stop()

# --- 3. CSS ปรับแต่งลิงก์และช่องกรอก ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* สไตล์ลิงก์ภารกิจ */
        .mission-link {
            font-size: 18px;
            color: #1877f2;
            text-decoration: none;
            display: block;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .mission-link:hover { text-decoration: underline; }
        
        /* กรอบขาวของช่อง Upload */
        div[data-testid="stFileUploader"] {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #dcdfe3;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

def go_to(page_name):
    st.query_params.clear()
    st.session_state.selected_mission = None
    st.session_state.page = page_name
    st.rerun()

# --- 5. การแสดงผลหน้ากิจกรรม ---

if st.session_state.page == 'game':
    u = st.session_state.user
    st.markdown(f"<h2 style='text-align: center; color: #1877f2;'>สวัสดีคุณ {u['fullname']} 👋</h2>", unsafe_allow_html=True)
    st.write("---")

    # ส่วนแสดงรายชื่อภารกิจ (โชว์แค่ตัวหนังสือลิงก์)
    if st.session_state.selected_mission is None:
        st.markdown("### 🚦 เลือกภารกิจประจำวัน")
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        
        if not missions:
            st.info("ขณะนี้ยังไม่มีภารกิจ")
        else:
            for m in missions:
                # สร้างลิงก์ HTML โดยส่งค่า m_id ไปบน URL
                st.markdown(f'<a href="./?page=game&m_id={m["id"]}" target="_self" class="mission-link">🔹 {m["title"]}</a>', unsafe_allow_html=True)
    
    # ส่วนแสดงรายละเอียดและที่ส่งรูป (เมื่อกดเลือกภารกิจแล้ว)
    else:
        m_id = st.session_state.selected_mission
        mission = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        
        # เช็คว่าวันนี้ส่งไปยัง (กฎ 1 ครั้ง/วัน)
        today = datetime.now().strftime("%Y-%m-%d")
        sub_check = supabase.table("submissions").select("*")\
            .eq("user_username", u['username'])\
            .eq("mission_id", m_id)\
            .gte("created_at", today).execute().data
        
        st.markdown(f"### 📍 {mission['title']}")
        
        if sub_check:
            st.success("✅ คุณทำภารกิจนี้สำเร็จแล้วในวันนี้")
            st.info("กรุณากลับมาเล่นใหม่ในวันพรุ่งนี้ครับ")
        else:
            st.write("ถ่ายรูปและแนบไฟล์เพื่อยืนยันการทำภารกิจ")
            f = st.file_uploader("เลือกรูปภาพ", type=['jpg','png','jpeg'])
            
            if f:
                if st.button("ยืนยันการส่งภารกิจ", use_container_width=True, type="secondary"):
                    with st.spinner("กำลังส่งงาน..."):
                        try:
                            # อัปโหลด Drive
                            filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                            meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                            media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                            drive_service.files().create(body=meta, media_body=media).execute()
                            
                            # บันทึก Supabase
                            supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m_id}).execute()
                            
                            st.success("🎉 ส่งภารกิจสำเร็จ!")
                            time.sleep(2)
                            go_to('game')
                        except Exception as e:
                            st.error(f"ผิดพลาด: {e}")
        
        # ปุ่มย้อนกลับไปรายชื่อภารกิจ
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ ย้อนกลับไปรายชื่อภารกิจ", use_container_width=True):
            st.session_state.selected_mission = None
            st.query_params.clear()
            st.rerun()

    # ปุ่มออกจากระบบ (วางไว้ล่างสุด)
    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True):
        st.session_state.user = None
        go_to('login')
