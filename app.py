import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและการรับค่าจากลิงก์ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# รับค่ารหัสภารกิจจาก URL
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

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
    st.error("❌ ระบบเชื่อมต่อผิดพลาด")
    st.stop()

# --- 3. CSS ฉบับเนียนกริ๊บ ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        
        /* ลิงก์รายชื่อภารกิจ */
        .mission-link {
            font-size: 18px; color: #1877f2; text-decoration: none;
            display: block; padding: 12px; border-bottom: 1px solid #eee;
            background: white; margin-bottom: 5px; border-radius: 8px;
        }
        .mission-link:hover { background-color: #f0f7ff; text-decoration: underline; }
        
        /* กล่องคำแนะนำกิจกรรม */
        .instruction-box {
            background-color: #e3f2fd; padding: 20px; border-radius: 12px;
            border-left: 6px solid #1877f2; margin-bottom: 20px; color: #003366;
        }

        /* ปุ่มสีฟ้า (เข้าสู่ระบบ) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* ปุ่มสีเขียว (ส่งงาน / ย้อนกลับ) */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
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
    
    # ถ้ายังไม่ได้เลือกภารกิจ -> โชว์รายชื่อเป็นลิงก์ตัวหนังสือ
    if st.session_state.selected_mission is None:
        st.markdown(f"<h2 style='text-align: center; color: #1877f2;'>ภารกิจของ {u['fullname']}</h2>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("### 🚦 เลือกกิจกรรมที่ต้องการทำ")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        if not missions:
            st.info("ยังไม่มีกิจกรรมในขณะนี้")
        else:
            for m in missions:
                st.markdown(f'<a href="./?page=game&m_id={m["id"]}" target="_self" class="mission-link">📍 {m["title"]}</a>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')

    # ถ้าเลือกภารกิจแล้ว -> เข้าหน้าทำกิจกรรม
    else:
        m_id = st.session_state.selected_mission
        # ดึงข้อมูลภารกิจนั้นๆ
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        
        st.markdown(f"<h2 style='color: #1877f2;'>{m_data['title']}</h2>", unsafe_allow_html=True)
        
        # 📝 ส่วนบอกว่ากิจกรรมวันนี้ให้ทำอย่างไร (ดึงจากคอลัมน์ description)
        st.markdown(f"""
            <div class="instruction-box">
                <b>วิธีทำกิจกรรม:</b><br>
                {m_data.get('description', 'ถ่ายรูปเพื่อยืนยันการทำภารกิจและอัปโหลดไฟล์ผ่านระบบ')}
            </div>
        """, unsafe_allow_html=True)

        # เช็คว่าวันนี้ส่งไปยัง (กฎ 1 ครั้ง/วัน)
        today = datetime.now().strftime("%Y-%m-%d")
        sub_check = supabase.table("submissions").select("*")\
            .eq("user_username", u['username'])\
            .eq("mission_id", m_id)\
            .gte("created_at", today).execute().data
        
        if sub_check:
            st.success("✅ วันนี้คุณทำกิจกรรมนี้สำเร็จเรียบร้อยแล้ว!")
            st.info("ระบบจะเปิดให้ส่งภาพอีกครั้งในวันพรุ่งนี้")
        else:
            # 📸 ปุ่มแนบรูป
            st.write("### 📸 แนบรูปถ่ายกิจกรรม")
            f = st.file_uploader("เลือกไฟล์รูปภาพ (JPG/PNG)", type=['jpg','png','jpeg'])
            
            if f:
                if st.button("ยืนยันการส่งรูปถ่าย", use_container_width=True, type="secondary"):
                    with st.spinner("กำลังอัปโหลดข้อมูล..."):
                        try:
                            # 1. อัปโหลดเข้า Google Drive
                            filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                            meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                            media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                            drive_service.files().create(body=meta, media_body=media).execute()
                            
                            # 2. บันทึกลง Supabase
                            supabase.table("submissions").insert({
                                "user_username": u['username'],
                                "mission_id": m_id
                            }).execute()
                            
                            st.success("🎉 ส่งกิจกรรมสำเร็จ! เก่งมากครับ")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {e}")
        
        # ปุ่มย้อนกลับ
        if st.button("⬅️ กลับไปหน้ารายชื่อกิจกรรม", use_container_width=True):
            st.session_state.selected_mission = None
            st.query_params.clear()
            st.rerun()
