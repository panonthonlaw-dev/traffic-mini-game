import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import re
from datetime import datetime
import io
import requests
import base64
import io



# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")

# --- 2. ประกาศตัวแปร Session State ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 3. ระบบจดจำสถานะผ่าน URL ---
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    st.session_state.selected_mission = int(st.query_params["m_id"])

# --- 4. การเชื่อมต่อระบบ (Supabase & Google Drive) ---
# --- 4. การเชื่อมต่อระบบ (ฉบับปรับปรุง) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    
    # ดึงข้อมูล GCP
    gcp_info = dict(st.secrets["gcp_service_account"])
    gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n").strip()
    
    # แนะนำให้ใช้สิทธิ์ 'drive' แบบเต็มถ้าส่งรูปเข้าโฟลเดอร์ที่สร้างมือไม่ได้
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive'] 
    )
    drive_service = build('drive', 'v3', credentials=creds)
    DRIVE_FOLDER_ID = st.secrets["general"]["DRIVE_FOLDER_ID"]
    
except Exception as e:
    st.error(f"⚠️ ระบบเชื่อมต่อมีปัญหา: {e}") # พ่น Error จริงออกมาดูเลยครับพี่
    st.stop()

# กู้คืน Session ผู้ใช้จาก URL
if "u" in st.query_params and st.session_state.user is None:
    u_url = st.query_params["u"]
    try:
        user_res = supabase.table("users").select("*").eq("username", u_url).execute()
        if user_res.data:
            st.session_state.user = user_res.data[0]
    except:
        pass

# --- 5. CSS ปรับแต่งหน้าตา (อิงตามโทนเดิมของพี่) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; }
        div[data-testid="stTextInput"] > div { background-color: white !important; border-radius: 10px !important; }
        input { color: #003366 !important; text-align: left !important; }
        label { color: #003366 !important; font-weight: bold !important; }

        /* 🔵 ปุ่มหลัก สีฟ้า */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        /* 🟢 ปุ่มสีเขียว */
        div.stButton > button[kind="secondary"] {
            background-color: #42b72a !important; color: white !important;
            font-weight: bold !important; height: 50px !important; border-radius: 10px !important;
        }

        .html-link { color: #1877f2 !important; text-decoration: underline !important; font-size: 15px; cursor: pointer; }

        .thin-btn-green div.stButton > button {
            background-color: transparent !important;
            color: #42b72a !important;
            border: 1px solid #42b72a !important;
            padding: 0px 8px !important;
            height: 30px !important;
            min-height: unset !important;
            font-size: 13px !important;
            border-radius: 5px !important;
            font-weight: normal !important;
            width: auto !important;
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
    current_u = st.query_params.get("u")
    st.query_params.clear()
    if current_u and page_name != 'login':
        st.query_params["u"] = current_u
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
            u_input = st.text_input("Username", placeholder="Username")
            p_input = st.text_input("Password", placeholder="Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_input).execute()
                if res.data and res.data[0]['password'] == p_input:
                    st.session_state.user = res.data[0]
                    st.query_params["u"] = u_input 
                    if st.session_state.user.get('role') == 'admin': go_to('admin_dashboard')
                    else: go_to('game')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        st.markdown('<div style="text-align: center; margin-top: -10px;"><a href="./?page=forgot" target="_self" class="html-link">คุณลืมรหัสผ่านใช่ไหม</a></div>', unsafe_allow_html=True)
        st.write("---")
        if st.button("สร้างบัญชีใหม่", use_container_width=True, type="secondary"): go_to('signup')

# 🟢 หน้าสมัครสมาชิก
elif st.session_state.page == 'signup':
    st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("signup_form"):
            sid = st.text_input("รหัสนักเรียน (ตัวเลข)")
            fname = st.text_input("ชื่อ-นามสกุล")
            uname = st.text_input("Username")
            phone = st.text_input("เบอร์โทรศัพท์")
            pw = st.text_input("รหัสผ่าน", type="password")
            cpw = st.text_input("ยืนยันรหัสผ่าน", type="password")
            if st.form_submit_button("ยืนยันลงทะเบียน", use_container_width=True):
                if pw == cpw and sid.isdigit():
                    try:
                        supabase.table("users").insert({"student_id": sid, "fullname": fname, "username": uname, "phone": phone, "password": pw, "role": "player"}).execute()
                        st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                    except: st.error("❌ Username นี้มีคนใช้แล้ว")
        if st.button("ย้อนกลับ", use_container_width=True, type="secondary"): go_to('login')

# 🔑 หน้าลืมรหัสผ่าน
elif st.session_state.page == 'forgot':
    st.markdown("<h2 style='text-align: center;'>กู้คืนรหัสผ่าน</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 4, 1])
    with col:
        with st.form("forgot_form"):
            fu = st.text_input("Username")
            fs = st.text_input("รหัสนักเรียน")
            fp = st.text_input("เบอร์โทรศัพท์")
            np = st.text_input("รหัสผ่านใหม่", type="password")
            if st.form_submit_button("อัปเดตรหัสผ่าน"):
                res = supabase.table("users").select("*").eq("username", fu).eq("student_id", fs).eq("phone", fp).execute()
                if res.data:
                    supabase.table("users").update({"password": np}).eq("username", fu).execute()
                    st.success("✅ สำเร็จ!"); time.sleep(1); go_to('login')
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
        if st.button("ยกเลิก", use_container_width=True, type="secondary"): go_to('login')

# 🎮 หน้ากิจกรรม (Player)
elif st.session_state.page == 'game':
    if st.session_state.user is None: 
        go_to('login')
        
    u = st.session_state.user 

    if st.session_state.selected_mission is None:
        # --- 1. Logic ดึงคะแนน (ทำแค่รอบเดียวพอ) ---
        try:
            points_res = supabase.table("submissions").select("points").eq("user_username", u['username']).execute().data
            total_exp = sum(p['points'] for p in points_res if p.get('points'))
        except:
            total_exp = 0

        # --- 2. คำนวณ Rank ---
        if total_exp <= 100:
            rank, progress = "Beginner", total_exp / 100
        elif total_exp <= 300:
            rank, progress = "Pro", (total_exp - 100) / 200
        elif total_exp <= 600:
            rank, progress = "Expert", (total_exp - 300) / 300
        elif total_exp <= 999:
            rank, progress = "Guardian", (total_exp - 600) / 399
        else:
            rank, progress = "Legendary", 1.0

        # --- 3. แสดงผล Header (Rank ซ้าย | Username ขวา) ---
        c_t, c_u = st.columns([0.6, 0.4])
        with c_t:
            st.markdown(f"### 🏆 {rank}")
        with c_u:
            st.markdown(f"<p style='text-align: right; margin-top: 10px;'>👤 <b>{u['username']}</b></p>", unsafe_allow_html=True)
        
        # --- 4. แสดงแถบ EXP และเส้นคั่น ---
        st.write(f"EXP รวม: {total_exp}")
        st.progress(min(progress, 1.0))
        st.write("---")

        # --- 5. รายการภารกิจ (เริ่มดึงข้อมูลต่อจากนี้) ---
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("*").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_dict = {s['mission_id']: s for s in subs}

        for m in missions:
            # (โค้ดแสดงปุ่มภารกิจของพี่ด้านล่างนี้...)
            m_sub = done_dict.get(m['id'])
            # ... ก๊อปโค้ดส่วนแสดงผลปุ่มมาวางต่อได้เลยครับ ...
            is_done = m['id'] in done_dict
            c1, c2 = st.columns([0.75, 0.25])
            with c1:
                st.markdown('<div class="thin-btn-green">', unsafe_allow_html=True)
                if st.button(f"📍 {m['title']}", key=f"m_btn_{m['id']}"):
                    st.session_state.selected_mission = m['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                if m_sub and m_sub.get('status') == 'approved':
                    status_color = "#42b72a"
                    status_text = f"✅ +{m_sub['points']} EXP"
                elif is_done:
                    status_color = "#42b72a"
                    status_text = "✅ รอตรวจ"
                else:
                    status_color = "#888"
                    status_text = "⭕ ยังไม่ส่ง"
                
                st.markdown(f'<div class="status-right" style="color:{status_color};">{status_text}</div>', unsafe_allow_html=True)
            
    else:
        # --- หน้าทำภารกิจ ---
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.markdown(f"<h2>{m_data['title']}</h2>", unsafe_allow_html=True)
        
        if st.button("⬅️ ย้อนกลับ", key="back"): st.session_state.selected_mission = None; st.rerun()
        
        st.info(f"💡 {m_data.get('description', 'กรุณาถ่ายรูปเพื่อยืนยันภารกิจ')}")
        
        # 1. ต้องสร้าง f ตรงนี้ก่อนครับ! 🛑
        f = st.file_uploader("📸 แนบรูปถ่ายหลักฐาน", type=['jpg','png','jpeg'])
        
        # 2. แล้วค่อยเช็ก if f: 
        if f is not None:
            if st.button("🚀 ยืนยันส่งภารกิจ", type="primary", use_container_width=True):
                with st.spinner("กำลังส่งรูปเข้า Drive 2TB..."):
                    try:
                        import requests
                        import base64
                        import io
                        
                        # เตรียมข้อมูลส่ง Apps Script
                        today = datetime.now().strftime("%Y-%m-%d")
                        filename = f"{u['student_id']}_m{m_id}_{today}.jpg"
                        base64_img = base64.b64encode(f.getvalue()).decode('utf-8')
                        
                        web_app_url = "https://script.google.com/macros/s/AKfycbyizcX69XMBeDCp1oyGR3hLuJ2i_n4YyBFhukyRT8399-R4FePPLS4kA5CwYrl1-yne/exec"
                        
                        payload = {
                            "filename": filename,
                            "mimetype": f.type,
                            "base64": base64_img
                        }
                        
                        response = requests.post(web_app_url, json=payload)
                        result = response.json()

                        if result.get('status') == 'success':
                            # บันทึกข้อมูลลง Supabase
                            supabase.table("submissions").insert({
                                "user_username": u['username'],
                                "mission_id": m_id,
                                "status": "pending",
                                "points": 0,
                                "image_url": result['fileId'] # เก็บ ID ไฟล์ไว้ดูในหน้าแอดมิน
                            }).execute()

                            st.success("🎉 ส่งงานเรียบร้อย! ใช้พื้นที่ 2TB ของพี่คุ้มแน่นอน")
                            time.sleep(1.5)
                            st.session_state.selected_mission = None
                            st.rerun()
                        else:
                            st.error(f"🚨 Google บ่นว่า: {result.get('message')}")

                    except Exception as e:
                        st.error(f"🚨 ระบบส่งงานขัดข้อง: {e}")
    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')

# 🛠️ หน้า Admin Dashboard
elif st.session_state.page == 'admin_dashboard':
    # 1. ระบบรักษาความปลอดภัย: เช็กว่าเป็น Admin จริงไหม
    if st.session_state.user is None or st.session_state.user.get('role') != 'admin': 
        st.session_state.page = 'login'
        st.rerun()
    
    st.title("👨‍🏫 แผงควบคุมผู้ดูแลระบบ")
    st.info(f"สวัสดีครับคุณครู **{st.session_state.user['fullname']}** | วันนี้มีงานให้ตรวจเพียบเลย!")

    # ใช้ Tabs เพื่อแยกส่วนการตรวจงานและการสร้างภารกิจ
    tab1, tab2 = st.tabs(["📥 ตรวจงานนักเรียน", "➕ เพิ่มภารกิจใหม่"])

    # ---------------------------------------------------------
    # TAB 1: ตรวจงานและให้คะแนน (อัปเดต Rank ทันที)
    # ---------------------------------------------------------
    with tab1:
        try:
            # ดึงงานที่ค้างตรวจ (Status = pending)
            pending_subs = supabase.table("submissions") \
                .select("*, users(fullname, student_id, total_exp), missions(title)") \
                .eq("status", "pending") \
                .order("created_at") \
                .execute().data
        except Exception as e:
            st.error(f"❌ ดึงข้อมูลไม่สำเร็จ: {e}")
            pending_subs = []

        st.subheader(f"รายการรอการตรวจสอบ ({len(pending_subs)} งาน)")

        if not pending_subs:
            st.success("✨ ยอดเยี่ยม! ตอนนี้ไม่มีงานค้างตรวจแล้วครับ")
        else:
            for sub in pending_subs:
                # แสดงงานแต่ละชิ้นในรูปแบบ Expander
                with st.expander(f"📌 {sub['users']['fullname']} (รหัส: {sub['users']['student_id']})"):
                    col1, col2 = st.columns([0.6, 0.4])
                    
                    with col1:
                        # 🖼️ แสดงรูปจาก Google Drive (ดึงผ่าน image_url ที่เป็น File ID)
                        file_id = sub.get('image_url')
                        if file_id:
                            st.image(f"https://drive.google.com/thumbnail?id={file_id}&sz=w800", caption="หลักฐานจากนักเรียน")
                        else:
                            st.warning("⚠️ ไม่พบรหัสรูปภาพในฐานข้อมูล")
                        st.caption(f"ส่งเมื่อ: {sub['created_at']}")

                    with col2:
                        st.markdown("### 📝 ให้คะแนนภารกิจ")
                        st.write(f"**ภารกิจ:** {sub['missions']['title']}")
                        
                        # ระบุคะแนน (Default ตามที่ตั้งไว้ในภารกิจ หรือตั้งเอง)
                        score = st.number_input(f"ระบุ EXP ที่ได้", 0, 1000, 10, key=f"score_{sub['id']}")
                        
                        if st.button("✅ อนุมัติและให้คะแนน", key=f"btn_{sub['id']}", use_container_width=True):
                            try:
                                with st.spinner("กำลังอัปเดตคะแนน..."):
                                    # จังหวะที่ 1: อัปเดตตาราง submissions
                                    supabase.table("submissions").update({
                                        "points": score,
                                        "status": "approved"
                                    }).eq("id", sub['id']).execute()
                                    
                                    # จังหวะที่ 2: บวกคะแนนเข้า total_exp ในตาราง users
                                    current_exp = sub['users'].get('total_exp', 0)
                                    new_exp = (current_exp if current_exp else 0) + score
                                    
                                    supabase.table("users").update({
                                        "total_exp": new_exp
                                    }).eq("username", sub['user_username']).execute()
                                    
                                    st.success(f"🌟 อนุมัติสำเร็จ! {sub['users']['fullname']} ได้แต้มรวม {new_exp} EXP")
                                    time.sleep(1)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ บันทึกผิดพลาด: {e}")

    # ---------------------------------------------------------
    # TAB 2: ระบบสร้างภารกิจใหม่
    # ---------------------------------------------------------
    with tab2:
        st.subheader("🆕 สร้างภารกิจใหม่ให้เด็ก ๆ")
        with st.form("new_mission_form", clear_on_submit=True):
            m_title = st.text_input("ชื่อภารกิจ", placeholder="เช่น ถ่ายรูปคู่กับไฟจราจรแยกโรงเรียน")
            m_desc = st.text_area("รายละเอียด/เงื่อนไขการส่งงาน")
            m_point_goal = st.number_input("คะแนนที่จะได้รับ (โชว์หลอกเด็ก)", 0, 500, 50)
            
            submit_btn = st.form_submit_button("🚀 ประกาศภารกิจ", use_container_width=True)
            
            if submit_btn:
                if m_title and m_desc:
                    try:
                        supabase.table("missions").insert({
                            "title": m_title,
                            "description": m_desc,
                            "points": m_point_goal
                        }).execute()
                        st.success(f"✅ ประกาศภารกิจ '{m_title}' สำเร็จ!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ ไม่สามารถสร้างภารกิจได้: {e}")
                else:
                    st.warning("กรุณากรอกข้อมูลให้ครบถ้วนก่อนส่งครับ")

    st.write("---")
    if st.button("🚪 ออกจากระบบแอดมิน", use_container_width=True, key="admin_logout"): 
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')
