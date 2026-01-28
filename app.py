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
import random

# --- 1. ตั้งค่าหน้าเว็บ (ต้องอยู่บนสุดของคำสั่ง Streamlit ทั้งหมด) ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦", layout="centered")
# --- 🆕 โค้ดซ่อน Topbar และ Footer ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppHeader {display: none;} /* สำหรับ Streamlit เวอร์ชั่นใหม่ๆ */
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. การเชื่อมต่อระบบ (ต้องประกาศ supabase ก่อนจะเอาไปใช้เช็ก Login) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"เชื่อมต่อฐานข้อมูลไม่ได้: {e}")

# --- 3. ประกาศตัวแปร Session State พื้นฐาน ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'selected_mission' not in st.session_state: st.session_state.selected_mission = None

# --- 4. ระบบ Auto-Login (ดึงค่าจาก URL กลับมา) ---
# ในหน้า Login พี่ใช้คำว่า "u" ดังนั้นตรงนี้ต้องใช้ "u" เหมือนกันครับ
q_user = st.query_params.get("u") 

if st.session_state.user is None and q_user:
    try:
        # ตอนนี้ supabase ถูกประกาศไว้ข้างบนแล้ว จะรันบรรทัดนี้ผ่านครับ!
        res = supabase.table("users").select("*").eq("username", q_user).execute()
        if res.data:
            st.session_state.user = res.data[0]
            # ย้ายไปหน้าตามสิทธิ์
            if st.session_state.user.get('role') == 'admin':
                st.session_state.page = 'admin_dashboard'
            else:
                st.session_state.page = 'game'
    except:
        pass

# --- 5. ระบบจดจำหน้าปัจจุบันผ่าน URL ---
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
if "m_id" in st.query_params:
    try:
        st.session_state.selected_mission = int(st.query_params["m_id"])
    except:
        pass

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

       # --- 3. คำนวณ Level และดึงข้อมูลแต่งตัว ---
        level = (total_exp // 500) + 1
        h_color = u.get('helmet_color', '#31333F')
        h_type = u.get('helmet_type', 'half')
        h_style = "border-radius: 50% 50% 20% 20%; height: 40px;" if h_type == 'full' else "border-radius: 50% 50% 0 0; height: 28px;"

        # --- 4. แสดงผล Header แบบ Compact (ชิดซ้ายและเป็นระเบียบ) ---
        # ปรับสัดส่วน Column ให้ Avatar เล็กลงและชิดซ้ายมากขึ้น
        col_avatar, col_details = st.columns([0.25, 0.75])
        
        with col_avatar:
            # Avatar ชิดซ้ายในวงกลม
            st.markdown(f"""
                <div style="background: white; padding: 5px; border-radius: 50%; width: 75px; height: 75px; text-align: center; border: 2px solid #1877f2; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    <div style="position: relative; display: inline-block; font-size: 45px; margin-top: 5px;">
                        👤
                        <div style="
                            position: absolute; 
                            top: -2px; left: 50%; transform: translateX(-50%);
                            background: {h_color}; 
                            width: 38px; 
                            {h_style}
                            border: 2px solid #333;
                            z-index: 10;
                        ">
                            <div style="background: rgba(255,255,255,0.3); width: 70%; height: 4px; margin: 3px auto; border-radius: 2px;"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_details:
            # ข้อมูลชื่อและ Rank จัดวางแบบบรรทัดชิดกัน
            st.markdown(f"""
                <div style='margin-top: -5px;'>
                    <h3 style='margin: 0; color: #003366;'>{u['fullname']}</h3>
                    <p style='margin: 0; color: #666; font-size: 14px;'>🎖️ <b>{rank}</b> | Level {level}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # ย้ายแถบ EXP มาไว้ในคอลัมน์นี้ด้วย เพื่อให้มันอยู่ชิดกับข้อมูลด้านบน
            st.write(f"🔥 {total_exp} EXP")
            st.progress(min(progress, 1.0))

        st.write("---") # เส้นคั่นก่อนเริ่มปุ่มเมนู
        

        # สร้าง 2 คอลัมน์เพื่อให้ปุ่มวางคู่กันครับ
        col_play, col_dress = st.columns(2)

        with col_play:
            if st.button("🎮 เล่นมินิเกม", use_container_width=True):
                st.session_state.page = 'bonus_game'
                st.rerun()

        with col_dress:
            if st.button("👕 แต่งตัวละคร", use_container_width=True):
                st.session_state.page = 'dressing_room'
                st.rerun()

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
                with st.spinner("กำลังส่งภารกิจ นักผจญภัยกรุณารอสักครู"):
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

                            st.success("🎉 ภารกิจถูกส่งแล้วรอตรวจสอบโดยGameMaster")
                            time.sleep(1.5)
                            st.session_state.selected_mission = None
                            st.rerun()
                        else:
                            st.error(f"🚨 Google บ่นว่า: {result.get('message')}")

                    except Exception as e:
                        st.error(f"🚨 ระบบส่งงานขัดข้อง: {e}")
    st.write("---")
    if st.button("🚪 ออกจากระบบ", use_container_width=True):
        # 👇 บรรทัดพวกนี้ต้อง "เยื้อง" เข้ามาให้ตรงกันแบบนี้ครับ
        st.session_state.user = None
        # ล้างชื่อผู้ใช้ใน URL ทิ้งเพื่อให้ Refresh แล้วไม่ Login กลับมาเอง
        st.query_params.clear() 
        st.session_state.page = 'login'
        st.rerun()

elif st.session_state.page == 'admin_dashboard':
    # --- 1. ระบบความปลอดภัย (Security) ---
    if st.session_state.user is None or st.session_state.user.get('role') != 'admin': 
        st.session_state.page = 'login'
        st.rerun()
    
    st.title("👨‍🏫 ระบบตรวจภาจกิจและมอบหมายภารกิจ (Guild")
    st.markdown(f"Game Master: **{st.session_state.user['fullname']}**")
    st.write("---")

    # แยกส่วนการทำงานเป็น 2 Tabs
    tab1, tab2 = st.tabs(["📥 ตรวจงานและให้คะแนน", "📝 จัดการภารกิจ"])

    # ---------------------------------------------------------
    # TAB 1: ตรวจงานนักเรียน (Update EXP ทันที + ปุ่ม Refresh)
    # ---------------------------------------------------------
    with tab1:
        # ส่วนหัวและปุ่มดึงข้อมูลใหม่
        col_title, col_ref = st.columns([0.7, 0.3])
        with col_title:
            st.subheader("ภารกิจที่รอตรวจสอบ")
        with col_ref:
            if st.button("🔄 ดึงข้อมูลล่าสุด", use_container_width=True):
                st.rerun()

        try:
            # ดึงข้อมูลงานที่ค้างตรวจ (Status = pending) เรียงจากใหม่ไปเก่า
            pending_subs = supabase.table("submissions") \
                .select("*, users(username, fullname, student_id, total_exp), missions(title)") \
                .eq("status", "pending") \
                .order("created_at", desc=True) \
                .execute().data
        except Exception as e:
            st.error(f"❌ ไม่สามารถดึงข้อมูลได้: {e}")
            pending_subs = []

        if not pending_subs:
            st.info("✨ ภารกิจตรวจสอบครบแล้ว")
        else:
            st.write(f"พบทั้งหมด {len(pending_subs)} รายการ")
            for sub in pending_subs:
                with st.expander(f"📌 {sub['users']['fullname']} (รหัส: {sub['users']['student_id']})"):
                    c1, c2 = st.columns([0.6, 0.4])
                    
                    with c1:
                        # 🖼️ ดึงรูปจาก Drive 2TB ผ่าน File ID
                        file_id = sub.get('image_url')
                        if file_id:
                            st.image(f"https://drive.google.com/thumbnail?id={file_id}&sz=w800", caption="หลักฐานการส่งงาน")
                        else:
                            st.warning("⚠️ ไม่พบ ID รูปภาพในระบบ")
                        st.caption(f"ส่งเมื่อ: {sub['created_at']}")

                    with c2:
                        st.markdown("### 🏆 ให้คะแนน EXP")
                        st.write(f"**ภารกิจ:** {sub['missions']['title']}")
                        score = st.number_input(f"ระบุคะแนน", 0, 1000, 10, key=f"score_{sub['id']}")
                        
                        if st.button("✅ ยืนยันและให้คะแนน", key=f"btn_{sub['id']}", use_container_width=True):
                            try:
                                with st.spinner("กำลังอัปเดตคะแนน..."):
                                    # จังหวะที่ 1: อัปเดตตาราง submissions เป็น approved
                                    supabase.table("submissions").update({
                                        "points": score,
                                        "status": "approved"
                                    }).eq("id", sub['id']).execute()
                                    
                                    # จังหวะที่ 2: บวกคะแนนเข้า total_exp ของเด็กในตาราง users
                                    current_total = sub['users'].get('total_exp', 0)
                                    new_total = (current_total if current_total else 0) + score
                                    
                                    supabase.table("users").update({
                                        "total_exp": new_total
                                    }).eq("username", sub['user_username']).execute()
                                    
                                    st.success(f"อัปเดตเรียบร้อย! {sub['users']['fullname']} ได้แต้มสะสม {new_total}")
                                    time.sleep(1)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"เกิดข้อผิดพลาด: {e}")

    # ---------------------------------------------------------
    # TAB 2: จัดการภารกิจ (สร้าง/ดู/ลบ)
    # ---------------------------------------------------------
    with tab2:
        # 1. ฟอร์มสร้างภารกิจใหม่
        st.subheader("➕ ประกาศภารกิจใหม่")
        with st.form("mission_form_admin", clear_on_submit=True):
            m_title = st.text_input("หัวข้อภารกิจ", placeholder="เช่น ถ่ายรูปคู่กับป้ายจราจร")
            m_desc = st.text_area("รายละเอียดวิธีทำ")
            m_pts = st.number_input("คะแนนเป้าหมาย (EXP)", 0, 500, 50)
            
            if st.form_submit_button("🚀 ยืนยันการประกาศภารกิจ", use_container_width=True):
                if m_title and m_desc:
                    try:
                        supabase.table("missions").insert({
                            "title": m_title,
                            "description": m_desc,
                            "points": m_pts
                        }).execute()
                        st.success(f"ประกาศภารกิจ '{m_title}' สำเร็จ!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"สร้างภารกิจไม่ได้: {e}")
                else:
                    st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

        st.write("---")
        
        # 2. แสดงรายการภารกิจที่ประกาศไปแล้ว
        st.subheader("📋 ภารกิจที่ประกาศแล้วในระบบ")
        try:
            m_list = supabase.table("missions").select("*").order("created_at", desc=True).execute().data
            if not m_list:
                st.info("ยังไม่มีการสร้างภารกิจ")
            else:
                for m in m_list:
                    with st.expander(f"📍 {m['title']} ({m.get('points', 0)} EXP)"):
                        st.write(f"**รายละเอียด:** {m['description']}")
                        st.caption(f"สร้างเมื่อ: {m['created_at'][:10]}")
                        if st.button("🗑️ ลบภารกิจนี้", key=f"del_m_{m['id']}", type="secondary"):
                            supabase.table("missions").delete().eq("id", m['id']).execute()
                            st.warning("ลบภารกิจเรียบร้อยแล้ว")
                            time.sleep(1)
                            st.rerun()
        except Exception as e:
            st.error(f"โหลดภารกิจล้มเหลว: {e}")

    # --- ปุ่มออกจากระบบ ---
    st.write("---")
    if st.button("🚪 ออกจากระบบ", use_container_width=True, key="admin_logout_main"):
        st.session_state.user = None
        st.query_params.clear()
        go_to('login')# =========================================================
# =========================================================
# 🎮 หน้า BONUS GAME: เกมเปิดป้าย (สิทธิ์ x3 และระบบรางวัลแบบยาก)
# =========================================================
elif st.session_state.page == 'bonus_game':
    u = st.session_state.user
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # --- 1. ตรวจสอบโควตา (ส่ง 1 งานวันนี้ = เล่นได้ 3 ครั้ง) ---
    try:
        m_res = supabase.table("submissions").select("id", count="exact")\
            .eq("user_username", u['username'])\
            .gte("created_at", today_str).execute()
        m_today = m_res.count if m_res.count else 0
        
        # ตรวจสอบเพื่อรีเซ็ตยอดเล่นรายวัน
        if str(u.get('last_game_date')) != today_str:
            daily_played = 0
            supabase.table("users").update({"daily_played_count": 0, "last_game_date": today_str}).eq("username", u['username']).execute()
            st.session_state.user['daily_played_count'] = 0
        else:
            daily_played = u.get('daily_played_count', 0)
            
        max_quota = m_today * 3
        available_quota = max_quota - daily_played
    except:
        max_quota, daily_played, available_quota = 0, 0, 0

    st.markdown("<h2 style='text-align: center; color:#1877f2;'>🪖 เกมเปิดป้ายลุ้น EXP x3</h2>", unsafe_allow_html=True)
    
    # ส่วนแสดงโควตา
    st.markdown(f"""
        <div style='background: white; padding: 15px; border-radius: 15px; border: 2px solid #1877f2; text-align: center; margin-bottom: 20px;'>
            <p style='margin:0; color:#666;'>สิทธิ์การเล่นวันนี้ (เหลือ {max(0, available_quota)} / {max_quota} ครั้ง)</p>
            <h2 style='margin:0; color:#1877f2;'>🎟️ {max(0, available_quota)} ใบ</h2>
            <small>ส่งงานวันนี้ {m_today} ชิ้น (1 งาน = 3 สิทธิ์)</small>
        </div>
    """, unsafe_allow_html=True)

    if available_quota > 0:
        # --- 2. เตรียมข้อมูลป้าย (อัตราสุ่มของยาก) ---
        if 'tiles' not in st.session_state:
            # รางวัลปกติ 8 ใบ
            pool = [5, 5, 5, 10, 10, 10, 20, 20] 
            # รางวัลใหญ่ 1 ใบ (สุ่มว่าจะเป็น 50 หรือ 100 โดยให้ 100 ออกยากมาก)
            rare_item = random.choices([50, 100], weights=[90, 10], k=1)[0]
            
            final_tiles = pool + [rare_item]
            random.shuffle(final_tiles)
            
            st.session_state.tiles = final_tiles
            st.session_state.opened = []
            st.session_state.round_win = 0

        # --- 3. แสดงตารางป้าย 3x3 ---
        cols = st.columns(3)
        for i in range(9):
            with cols[i % 3]:
                if i in st.session_state.opened:
                    st.button(f"✨ {st.session_state.tiles[i]}", key=f"t_{i}", disabled=True, use_container_width=True)
                else:
                    if len(st.session_state.opened) < 3: # เปิดได้ 3 ใบต่อรอบ
                        if st.button("❓", key=f"t_{i}", use_container_width=True):
                            win_amount = st.session_state.tiles[i]
                            
                            # อัปเดต Database ทันที
                            new_total_exp = (u.get('total_exp', 0)) + win_amount
                            supabase.table("users").update({"total_exp": new_total_exp}).eq("username", u['username']).execute()
                            
                            # อัปเดต Session ให้หน้าจอเปลี่ยน
                            st.session_state.user['total_exp'] = new_total_exp
                            st.session_state.opened.append(i)
                            st.session_state.round_win += win_amount
                            st.toast(f"ได้รับ +{win_amount} EXP!", icon="🎉")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.button("🔒", key=f"t_{i}", disabled=True, use_container_width=True)

        # --- 4. เมื่อเล่นจบรอบ ---
        if len(st.session_state.opened) >= 3:
            st.success(f"🎊 จบรอบ! ได้รับรวม {st.session_state.round_win} EXP")
            if st.button("🏁 ยืนยันจบเกมและหักสิทธิ์เล่น", type="primary", use_container_width=True):
                # หักสิทธิ์เล่นจริงตอนกดปุ่มนี้
                new_played = daily_played + 1
                supabase.table("users").update({"daily_played_count": new_played}).eq("username", u['username']).execute()
                st.session_state.user['daily_played_count'] = new_played
                
                # ล้างค่าเพื่อเริ่มใหม่
                del st.session_state.tiles
                del st.session_state.opened
                del st.session_state.round_win
                st.rerun()
    else:
        st.warning("🚫 วันนี้คุณใช้สิทธิ์เล่นครบแล้ว! ส่งงานเพิ่มเพื่อรับสิทธิ์ใหม่ (1 งาน = 3 สิทธิ์)")

    if st.button("⬅️ กลับหน้าหลัก", use_container_width=True):
        if 'tiles' in st.session_state:
            del st.session_state.tiles
        st.session_state.page = 'game'
        st.rerun()
# 👗 หน้าแต่งตัว (Dressing Room) - วางล่างสุดของไฟล์
# =========================================================
elif st.session_state.page == 'dressing_room':
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>👕 ห้องแต่งตัวนักบิด</h2>", unsafe_allow_html=True)
    
    # ดึงข้อมูลผู้ใช้ล่าสุดจาก session
    user_exp = st.session_state.user.get('total_exp', 0)
    level = (user_exp // 500) + 1
    
    st.markdown(f"""
        <div style='text-align: center; background: #e1f5fe; padding: 10px; border-radius: 10px; margin-bottom: 20px;'>
            <h4 style='margin:0; color: #01579b;'>Level {level}</h4>
            <p style='margin:0;'>สะสมได้ {user_exp} EXP</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 🎒 ระบบปลดล็อกไอเทมตาม Level ---
    colors = {"🔴 แดง (Basic)": "#FF4B4B", "⚫ ดำ (Basic)": "#31333F"}
    if level >= 2: colors["🟢 เขียว (Pro)"] = "#28A745"
    if level >= 3: colors["🔵 น้ำเงิน (Pro)"] = "#007BFF"
    if level >= 5: colors["🟡 ทอง (Legend)"] = "#FFD700"

    types = {"หมวกครึ่งใบ": "half"}
    if level >= 4: types["หมวกเต็มใบ (High Tech)"] = "full"

    # --- 🎨 ส่วนแสดงผลและการเลือก ---
    col_preview, col_control = st.columns([0.5, 0.5])
    
    with col_control:
        st.subheader("เลือกสไตล์ของคุณ")
        sel_color_name = st.selectbox("เลือกสีหมวก", list(colors.keys()))
        sel_type_name = st.selectbox("เลือกทรงหมวก", list(types.keys()))
        
        current_color = colors[sel_color_name]
        current_type = types[sel_type_name]

    with col_preview:
        # ระบบวาดตัวละครด้วย CSS (Responsive)
        h_style = "border-radius: 50% 50% 20% 20%; height: 50px;" if current_type == 'full' else "border-radius: 50% 50% 0 0; height: 35px;"
        
        st.markdown(f"""
            <div style="background: #ffffff; padding: 20px; border-radius: 15px; text-align: center; border: 2px dashed #ccc;">
                <div style="position: relative; display: inline-block; font-size: 70px; margin-top: 10px;">
                    👤
                    <div style="
                        position: absolute; 
                        top: -5px; left: 50%; transform: translateX(-50%);
                        background: {current_color}; 
                        width: 60px; 
                        {h_style}
                        border: 3px solid #333;
                        z-index: 10;
                    ">
                        <div style="background: rgba(255,255,255,0.3); width: 70%; height: 8px; margin: 5px auto; border-radius: 5px;"></div>
                    </div>
                </div>
                <p style="margin-top:10px; color:#666;">โฉมหน้าปัจจุบัน</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("---")
    if st.button("💾 บันทึกรูปลักษณ์ใหม่", use_container_width=True, type="primary"):
        try:
            supabase.table("users").update({
                "helmet_color": current_color,
                "helmet_type": current_type
            }).eq("username", st.session_state.user['username']).execute()
            
            # อัปเดตในเครื่องทันที
            st.session_state.user['helmet_color'] = current_color
            st.session_state.user['helmet_type'] = current_type
            st.success("✨ ว้าว! คุณดูเท่ขึ้นเป็นกอง บันทึกเรียบร้อยครับ")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    if st.button("⬅️ กลับหน้าหลัก", use_container_width=True):
        st.session_state.page = 'game'
        st.rerun()
