import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
from datetime import datetime

# --- 1. ตั้งค่าพื้นหลังและ CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        .mission-card {
            background: white; padding: 20px; border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #eee;
            margin-bottom: 20px;
        }
        .status-badge {
            padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

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
    st.error(f"❌ ระบบเชื่อมต่อผิดพลาด")
    st.stop()

# --- 3. ฟังก์ชันจัดการหน้าจอ ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. การแสดงผลหน้ากิจกรรม (Player Page) ---

if st.session_state.page == 'game':
    u = st.session_state.user
    
    # Header: ยินดีต้อนรับ
    st.markdown(f"<h2 style='text-align: center; color: #1877f2;'>ยินดีต้อนรับคุณ {u['fullname']} 👋</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #003366;'>รหัสนักเรียน: {u['student_id']}</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### 🚦 ภารกิจประจำวัน")
    
    _, col, _ = st.columns([1, 6, 1])
    with col:
        # 1. ดึงภารกิจที่เปิดใช้งานอยู่
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        
        # 2. ดึงข้อมูลการส่งงานของวันนี้ (เพื่อเช็คสิทธิ์ 1 ครั้ง/วัน)
        today = datetime.now().strftime("%Y-%m-%d")
        # ค้นหาว่าวันนี้ username นี้ ส่งภารกิจอะไรไปแล้วบ้าง
        subs_today = supabase.table("submissions").select("mission_id")\
            .eq("user_username", u['username'])\
            .gte("created_at", today).execute().data
        
        done_mission_ids = [s['mission_id'] for s in subs_today]

        if not missions:
            st.info("ยังไม่มีภารกิจในขณะนี้")
        
        for m in missions:
            is_done = m['id'] in done_mission_ids
            
            # การแสดงผล Card ภารกิจ
            st.markdown(f"""
                <div class="mission-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b style="color: #003366; font-size: 18px;">{m['title']}</b>
                        <span class="status-badge" style="background: {'#e8f5e9; color: #42b72a;' if is_done else '#e3f2fd; color: #1877f2;'}">
                            {'✅ สำเร็จวันนี้แล้ว' if is_done else '🔵 รอดำเนินการ'}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if not is_done:
                # ระบบแนบรูป (เฉพาะคนที่ยังไม่ได้ส่งวันนี้)
                f = st.file_uploader(f"แนบรูปถ่ายภารกิจ: {m['title']}", type=['jpg','png','jpeg'], key=f"file_{m['id']}")
                
                if f:
                    # ปุ่มส่งงานสีเขียว (kind="secondary")
                    if st.button(f"ยืนยันส่งรูปด่าน {m['id']}", key=f"btn_{m['id']}", use_container_width=True, type="secondary"):
                        with st.spinner("กำลังอัปโหลดรูปภาพ..."):
                            try:
                                # ตั้งชื่อไฟล์: รหัสนักเรียน_ด่าน_วันที่.jpg
                                filename = f"{u['student_id']}_m{m['id']}_{today}.jpg"
                                
                                # อัปโหลดเข้า Google Drive
                                meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
                                media = MediaIoBaseUpload(f, mimetype=f.type, resumable=True)
                                drive_service.files().create(body=meta, media_body=media).execute()
                                
                                # บันทึกลง Supabase
                                supabase.table("submissions").insert({
                                    "user_username": u['username'],
                                    "mission_id": m['id']
                                }).execute()
                                
                                st.success("🎉 ส่งงานสำเร็จ! พบกันใหม่พรุ่งนี้")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.info("💡 คุณส่งภารกิจนี้ไปแล้วในวันนี้ ระบบจะเปิดให้ส่งอีกครั้งในวันพรุ่งนี้ครับ")
                st.write("---")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            go_to('login')
