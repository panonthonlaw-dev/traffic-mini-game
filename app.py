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

# =========================================================
# 🎮 [โซนที่ 1] หน้ากิจกรรมหลักของผู้เล่น (Player Dashboard)
# =========================================================
elif st.session_state.page == 'game':
    # --- 👮 1. ด่านตรวจสิทธิ์ (Security Guard) ---
    if st.session_state.user is None: 
        st.session_state.page = 'login'; st.rerun()
    
    # ถ้า Admin หลงเข้าหน้านี้ ให้ดีดไปหน้า Admin ทันที
    if st.session_state.user.get('role') == 'admin':
        st.session_state.page = 'admin_dashboard'; st.rerun()

    # --- 2. Injection CSS (ปรับแต่ง UI ให้พรีเมียม) ---
    st.markdown("""
        <style>
            .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00c6ff, #0072ff) !important; height: 10px !important; }
            div[data-testid="stHorizontalBlock"] .stButton > button {
                border-radius: 15px !important; height: 60px !important; font-weight: bold !important;
                background: rgba(255, 255, 255, 0.8) !important; border: 1px solid #ddd !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Sync ข้อมูลล่าสุด
    u = supabase.table("users").select("*").eq("username", st.session_state.user['username']).single().execute().data
    st.session_state.user = u
    
    total_exp = u.get('total_exp', 0)
    level = (total_exp // 500) + 1

    # --- 3. หน้าเมนูหลักผู้เล่น ---
    if st.session_state.selected_mission is None:
        # 💎 แสดง Profile แบบ Premium (ไม่มีกรอบ)
        hc, ht = u.get('helmet_color', '#31333F'), u.get('helmet_type', 'half')
        sc, fc, bc = u.get('shirt_color', '#FFFFFF'), u.get('shoes_color', '#333333'), u.get('bike_color', '#1877f2')
        h_css = "border-radius:50% 50% 20% 20%; height:32px;" if ht=='full' else "border-radius:50% 50% 0 0; height:22px;"

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); padding: 25px; border-radius: 25px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="background: white; padding: 15px; border-radius: 20px;">
                        <div style="display: flex; justify-content: center; align-items: flex-end; gap: 8px;">
                            <div style="position: relative; font-size: 50px;">
                                👤
                                <div style="position: absolute; top: -2px; left: 50%; transform: translateX(-50%); background: {hc}; width: 38px; {h_css} border: 2px solid #333; z-index: 10;"></div>
                                <div style="position: absolute; top: 32px; left: 50%; transform: translateX(-50%); background: {sc}; width: 26px; height: 18px; border: 2px solid #333; border-radius: 3px; z-index: 5;"></div>
                            </div>
                            <div style="font-size: 45px; position: relative;">🏍️<div style="position: absolute; bottom: 8px; left: 10%; width: 80%; height: 6px; background: {bc}; border-radius: 5px; z-index: -1; filter: blur(2px);"></div></div>
                        </div>
                    </div>
                    <div>
                        <h2 style="margin: 0;">{u['fullname']}</h2>
                        <p style="margin: 0; color: #666;">⭐ Level {level} | 🔥 {total_exp} EXP</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.progress(min((total_exp % 500) / 500, 1.0))

        # ปุ่มเมนูหลัก
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎮 เล่นเกม", key="p_btn", use_container_width=True): 
                st.session_state.page = 'bonus_game'; st.rerun()
        with c2:
            if st.button("👕 แต่งตัว", key="d_btn", use_container_width=True): 
                st.session_state.page = 'dressing_room'; st.rerun()

        st.write("---")
        st.subheader("📍 ภารกิจวันนี้")
        
        missions = supabase.table("missions").select("*").eq("is_active", True).execute().data
        today = datetime.now().strftime("%Y-%m-%d")
        subs = supabase.table("submissions").select("*").eq("user_username", u['username']).gte("created_at", today).execute().data
        done_dict = {s['mission_id']: s for s in subs}

        for m in missions:
            m_sub = done_dict.get(m['id'])
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                if st.button(f"🏁 {m['title']}", key=f"m_list_{m['id']}", use_container_width=True):
                    st.session_state.selected_mission = m['id']; st.rerun()
            with col2:
                status = "✅ ตรวจแล้ว" if m_sub and m_sub['status'] == 'approved' else "⏳ รอตรวจ" if m['id'] in done_dict else "⭕ ว่าง"
                st.markdown(f"<p style='text-align:center; padding-top:10px;'>{status}</p>", unsafe_allow_html=True)

        st.write(" ")
        if st.button("🚪 ออกจากระบบ", key="lo_p", use_container_width=True):
            st.session_state.user = None; st.session_state.page = 'login'; st.rerun()

    # --- 4. หน้าทำภารกิจ (Uploader) ---
    else:
        m_id = st.session_state.selected_mission
        m_data = supabase.table("missions").select("*").eq("id", m_id).single().execute().data
        st.subheader(f"ภารกิจ: {m_data['title']}")
        if st.button("⬅️ ย้อนกลับ", key="back_to_g"): 
            st.session_state.selected_mission = None; st.rerun()
        
        st.info(f"💡 {m_data.get('description', 'กรุณาอัปโหลดรูปหลักฐาน')}")
        f = st.file_uploader("📸 แนบรูปถ่าย", type=['jpg','png','jpeg'], key="up_mission_f")
        
        if f and st.button("🚀 ยืนยันส่งงาน", type="primary", use_container_width=True):
            with st.spinner("กำลังส่ง..."):
                try:
                    import requests, base64
                    base64_img = base64.b64encode(f.getvalue()).decode('utf-8')
                    web_url = "https://script.google.com/macros/s/AKfycbyizcX69XMBeDCp1oyGR3hLuJ2i_n4YyBFhukyRT8399-R4FePPLS4kA5CwYrl1-yne/exec"
                    res = requests.post(web_url, json={"filename": f"{u['username']}_{m_id}.jpg", "mimetype": f.type, "base64": base64_img}).json()
                    
                    if res.get('status') == 'success':
                        supabase.table("submissions").insert({"user_username": u['username'], "mission_id": m_id, "status": "pending", "image_url": res['fileId']}).execute()
                        st.success("ส่งงานสำเร็จ!"); time.sleep(2); st.session_state.selected_mission = None; st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# =========================================================
# 👨‍🏫 [โซนที่ 2] หน้า Admin Dashboard (แยกขาดถาวร)
# =========================================================
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.user is None or st.session_state.user.get('role') != 'admin': 
        st.session_state.page = 'login'; st.rerun()
    
    st.title("👨‍🏫 Game Master Control")
    
    # 🆕 สร้าง Tabs (ต้องประกาศตรงนี้ถึงจะไม่มี NameError)
    tab1, tab2, tab3 = st.tabs(["📋 ตรวจงาน", "🛠️ จัดการภารกิจ", "📊 สถิตินักเรียน"])

    with tab1:
        st.subheader("รายการรอตรวจ")
        pending_subs = supabase.table("submissions").select("*, users(fullname)").eq("status", "pending").execute().data
        if not pending_subs: st.info("ไม่มีงานค้าง")
        else:
            for s in pending_subs:
                with st.expander(f"📌 จาก: {s['users']['fullname']}"):
                    st.image(f"https://drive.google.com/uc?id={s['image_url']}", use_container_width=True)
                    pts = st.number_input("ให้คะแนน", 0, 100, 50, key=f"p_{s['id']}")
                    if st.button("อนุมัติ", key=f"ap_{s['id']}"):
                        supabase.table("submissions").update({"status": "approved", "points": pts}).eq("id", s['id']).execute()
                        # บวก EXP ให้เด็ก
                        curr_exp = supabase.table("users").select("total_exp").eq("username", s['user_username']).single().execute().data['total_exp']
                        supabase.table("users").update({"total_exp": curr_exp + pts}).eq("username", s['user_username']).execute()
                        st.success("เรียบร้อย!"); st.rerun()

    with tab2:
        st.subheader("➕ เพิ่มภารกิจ")
        with st.form("new_m"):
            t = st.text_input("หัวข้อ")
            d = st.text_area("รายละเอียด")
            if st.form_submit_button("ประกาศ"):
                supabase.table("missions").insert({"title": t, "description": d, "is_active": True}).execute()
                st.success("สร้างแล้ว!"); st.rerun()

    with tab3:
        st.subheader("รายชื่อนักเรียน")
        st.table(supabase.table("users").select("fullname, total_exp").eq("role", "player").order("total_exp", desc=True).execute().data)

    if st.sidebar.button("🚪 ออกจากระบบ", key="lo_adm"):
        st.session_state.user = None; st.session_state.page = 'login'; st.rerun()
# =========================================================
# 🎮 หน้า BONUS GAME: เกมเปิดป้าย (ฉบับแก้ไข AttributeError)
# =========================================================
elif st.session_state.page == 'bonus_game':
    u = st.session_state.user
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # --- 1. ตรวจสอบโควตา (ส่ง 1 งาน = 3 สิทธิ์) ---
    try:
        m_res = supabase.table("submissions").select("id", count="exact")\
            .eq("user_username", u['username'])\
            .gte("created_at", today_str).execute()
        m_today = m_res.count if m_res.count else 0
        
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

    st.markdown("<h2 style='text-align: center; color:#1877f2;'>🪖 เกมเปิดป้ายลุ้น EXP</h2>", unsafe_allow_html=True)
    
    # --- 🆕 2. แก้ไขจุดนี้: ระบบเตรียมตัวแปร (Initialization) แบบปลอดภัย ---
    if 'tiles' not in st.session_state:
        pool = [5, 5, 5, 10, 10, 10, 20, 20]
        rare_item = random.choices([50, 100], weights=[90, 10], k=1)[0]
        final_tiles = pool + [rare_item]
        random.shuffle(final_tiles)
        st.session_state.tiles = final_tiles

    # เช็กตัวแปรแยกกัน เพื่อป้องกัน AttributeError
    if 'opened' not in st.session_state:
        st.session_state.opened = []
    if 'round_win' not in st.session_state:
        st.session_state.round_win = 0

    # แสดงโควตา
    st.info(f"🎫 สิทธิ์สุ่มวันนี้คงเหลือ: {max(0, available_quota)} / {max_quota} ครั้ง")

    if available_quota > 0:
       # --- 3. แสดงตารางป้าย ---
        cols = st.columns(3)
        for i in range(9):
            with cols[i % 3]:
                if i in st.session_state.opened:
                    # ✅ ป้ายที่เปิดไปแล้ว: แสดงคะแนนที่ได้
                    st.button(f"✨ {st.session_state.tiles[i]}", key=f"btn_{i}", disabled=True, use_container_width=True)
                else:
                    # ✅ ป้ายที่ยังไม่ได้เปิด
                    if len(st.session_state.opened) < 3:
                        if st.button("❓", key=f"btn_{i}", use_container_width=True):
                            # 1. ดึงแต้มที่ซ่อนอยู่หลังป้าย
                            win_val = st.session_state.tiles[i]
                            
                            # 2. คำนวณ EXP ใหม่ (ดึงจาก Session ล่าสุด)
                            current_exp = st.session_state.user.get('total_exp', 0)
                            new_exp = current_exp + win_val
                            
                            try:
                                # 3. บันทึกลง Supabase (ออนไลน์)
                                supabase.table("users").update({"total_exp": new_exp}).eq("username", u['username']).execute()
                                
                                # 4. บันทึกลง Session (เพื่อให้หน้าแรกเห็นเลขใหม่ทันที)
                                st.session_state.user['total_exp'] = new_exp
                                
                                # 5. บันทึกประวัติในรอบนี้
                                st.session_state.opened.append(i)
                                st.session_state.round_win += win_val
                                
                                st.toast(f"🎉 ได้รับ +{win_val} EXP", icon="⭐")
                                time.sleep(0.5)
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"🚨 บันทึกคะแนนไม่ได้: {e}")
                    else:
                        # ✅ ถ้าเปิดครบ 3 ใบแล้ว: ล็อคป้ายที่เหลือ (ตัด else ส่วนเกินออกแล้ว)
                        st.button("🔒", key=f"btn_{i}", disabled=True, use_container_width=True)

        # --- 4. สรุปผลรอบการเล่น ---
        if len(st.session_state.opened) >= 3:
            st.success(f"🎊 จบรอบ! ได้รับรวม {st.session_state.round_win} EXP")
            if st.button("🏁 ยืนยันผลและหักโควตา 1 ครั้ง", type="primary", use_container_width=True):
                # หักสิทธิ์เล่น
                new_played = daily_played + 1
                supabase.table("users").update({"daily_played_count": new_played}).eq("username", u['username']).execute()
                st.session_state.user['daily_played_count'] = new_played
                
                # ล้างตัวแปรเพื่อเริ่มรอบใหม่
                del st.session_state.tiles
                del st.session_state.opened
                del st.session_state.round_win
                st.rerun()
    else:
        st.warning("🚫 โควตาวันนี้หมดแล้ว! ส่งงานชิ้นใหม่เพื่อเล่นต่อ")

    if st.button("⬅️ กลับหน้าหลัก", use_container_width=True):
        # ล้างขยะก่อนออก
        for key in ['tiles', 'opened', 'round_win']:
            if key in st.session_state: del st.session_state[key]
        st.session_state.page = 'game'
        st.rerun()
# 👗 หน้าแต่งตัว (Dressing Room) - Fixed Preview & Full Set
# =========================================================
elif st.session_state.page == 'dressing_room':
    u = st.session_state.user
    user_exp = u.get('total_exp', 0)
    level = (user_exp // 500) + 1

    # --- 1. เตรียมตัวแปรชั่วคราว (ถ้าไม่มีให้สร้าง) ---
    if 'temp_h_color' not in st.session_state: st.session_state.temp_h_color = u.get('helmet_color', '#31333F')
    if 'temp_h_type' not in st.session_state: st.session_state.temp_h_type = u.get('helmet_type', 'half')
    if 'temp_s_color' not in st.session_state: st.session_state.temp_s_color = u.get('shirt_color', '#FFFFFF')
    if 'temp_f_color' not in st.session_state: st.session_state.temp_f_color = u.get('shoes_color', '#333333')
    if 'temp_b_color' not in st.session_state: st.session_state.temp_b_color = u.get('bike_color', '#1877f2')

    # --- 🆕 ฉีด CSS บังคับปุ่มแอ็กชันด้านล่างให้เท่ากัน ---
    st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] .stButton > button {
                width: 100% !important; height: 50px !important;
                border-radius: 12px !important; font-weight: bold !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; color: #1877f2;'>🏁 แต่งตัว & ปรับแต่งรถ</h2>", unsafe_allow_html=True)

    # --- 2. 📺 ส่วน Preview (แสดงผลรวม) ---
    # คำนวณทรงหมวก
    h_style = "border-radius: 50% 50% 20% 20%; height: 35px;" if st.session_state.temp_h_type == 'full' else "border-radius: 50% 50% 0 0; height: 25px;"
    
    st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 20px; text-align: center; border: 2px solid #1877f2; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: center; align-items: flex-end; gap: 15px;">
                <div style="position: relative; font-size: 60px;">
                    👤
                    <div style="position: absolute; top: -5px; left: 50%; transform: translateX(-50%); background: {st.session_state.temp_h_color}; width: 48px; {h_style} border: 2px solid #333; z-index: 10;"></div>
                    <div style="position: absolute; top: 38px; left: 50%; transform: translateX(-50%); background: {st.session_state.temp_s_color}; width: 32px; height: 22px; border: 2px solid #333; border-radius: 4px; z-index: 5;"></div>
                    <div style="position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); display: flex; gap: 10px;">
                        <div style="background: {st.session_state.temp_f_color}; width: 12px; height: 6px; border: 1px solid #333; border-radius: 2px;"></div>
                        <div style="background: {st.session_state.temp_f_color}; width: 12px; height: 6px; border: 1px solid #333; border-radius: 2px;"></div>
                    </div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 65px; position: relative;">
                        🏍️
                        <div style="position: absolute; bottom: 10px; left: 10%; width: 80%; height: 8px; background: {st.session_state.temp_b_color}; border-radius: 10px; z-index: -1; filter: blur(1px);"></div>
                    </div>
                </div>
            </div>
            <p style="margin-top:10px; font-size: 14px; font-weight:bold; color:#1877f2;">สไตล์ที่คุณกำลังลองแต่ง</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. 🛍️ ตู้เลือกไอเทมแยกหมวด (Tabs) ---
    tab1, tab2, tab3, tab4 = st.tabs(["🪖 หมวก", "👕 เสื้อ", "👟 รองเท้า", "🏍️ รถ"])

    # ฟังก์ชันช่วยวาดตู้ไอเทม
    def draw_item_grid(item_list, session_key, type_key=None):
        for i in range(0, len(item_list), 3):
            cols = st.columns(3)
            for j, item in enumerate(item_list[i:i+3]):
                with cols[j]:
                    is_locked = level < item['lv']
                    bg = "#ffffff" if not is_locked else "#f5f5f5"
                    filter_s = "" if not is_locked else "filter: grayscale(100%); opacity: 0.4;"
                    
                    st.markdown(f"""
                        <div style="background: {bg}; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #ddd; {filter_s} height: 80px;">
                            <div style="font-size: 25px;">{item['icon']}</div>
                            <div style="font-size: 10px; font-weight: bold;">{item['name']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if is_locked:
                        st.button(f"🔒 Lv.{item['lv']}", key=f"l_{session_key}_{item['name']}", disabled=True, use_container_width=True)
                    else:
                        if st.button("เลือก", key=f"s_{session_key}_{item['name']}", use_container_width=True):
                            st.session_state[session_key] = item['color']
                            if type_key: st.session_state[type_key] = item.get('type', 'half')
                            st.rerun()

    with tab1:
        draw_item_grid([
            {"name": "แดง", "color": "#FF4B4B", "lv": 1, "icon": "🔴", "type": "half"},
            {"name": "ดำ", "color": "#31333F", "lv": 1, "icon": "⚫", "type": "half"},
            {"name": "เขียว", "color": "#28A745", "lv": 2, "icon": "🟢", "type": "half"},
            {"name": "เต็มใบดำ", "color": "#111111", "lv": 3, "icon": "👺", "type": "full"},
            {"name": "เต็มใบขาว", "color": "#FFFFFF", "lv": 4, "icon": "⚪", "type": "full"},
            {"name": "ทอง", "color": "#FFD700", "lv": 5, "icon": "👑", "type": "full"},
        ], 'temp_h_color', 'temp_h_type')

    with tab2:
        draw_item_grid([
            {"name": "ขาว", "color": "#FFFFFF", "lv": 1, "icon": "⬜"},
            {"name": "ดำ", "color": "#111111", "lv": 2, "icon": "⬛"},
            {"name": "น้ำเงิน", "color": "#0D47A1", "lv": 3, "icon": "🧥"},
            {"name": "สะท้อนแสง", "color": "#CCFF00", "lv": 4, "icon": "🦺"},
        ], 'temp_s_color')

    with tab3:
        draw_item_grid([
            {"name": "ผ้าใบดำ", "color": "#333333", "lv": 1, "icon": "👟"},
            {"name": "แดง", "color": "#D32F2F", "lv": 2, "icon": "👠"},
            {"name": "บูทซิ่ง", "color": "#000000", "lv": 4, "icon": "👢"},
        ], 'temp_f_color')

    with tab4:
        draw_item_grid([
            {"name": "ฟ้า", "color": "#1877f2", "lv": 1, "icon": "🛵"},
            {"name": "แดงซิ่ง", "color": "#FF0000", "lv": 2, "icon": "🚀"},
            {"name": "เหลือง", "color": "#FFD600", "lv": 3, "icon": "⚡"},
            {"name": "ดำดุ", "color": "#000000", "lv": 5, "icon": "🔥"},
        ], 'temp_b_color')

    st.write("---")
    
    # --- 4. 💾 ปุ่มแอ็กชัน (ขนาดเท่ากัน 50/50) ---
    c_save, c_back = st.columns(2)
    with c_save:
        if st.button("💾 บันทึกชุดนี้", type="primary", use_container_width=True):
            try:
                supabase.table("users").update({
                    "helmet_color": st.session_state.temp_h_color,
                    "helmet_type": st.session_state.temp_h_type,
                    "shirt_color": st.session_state.temp_s_color,
                    "shoes_color": st.session_state.temp_f_color,
                    "bike_color": st.session_state.temp_b_color
                }).eq("username", u['username']).execute()
                
                # อัปเดต Session หลักเพื่อให้หน้าอื่นๆ เปลี่ยนตาม
                st.session_state.user['helmet_color'] = st.session_state.temp_h_color
                st.session_state.user['helmet_type'] = st.session_state.temp_h_type
                st.session_state.user['shirt_color'] = st.session_state.temp_s_color
                st.session_state.user['shoes_color'] = st.session_state.temp_f_color
                st.session_state.user['bike_color'] = st.session_state.temp_b_color
                
                st.success("บันทึกสำเร็จ!")
                time.sleep(1)
                go_to('game')
            except Exception as e:
                st.error(f"Error: {e}")
                
    with c_back:
        if st.button("⬅️ ย้อนกลับ", use_container_width=True):
            # ล้างค่า temp ทิ้ง
            for k in ['temp_h_color','temp_h_type','temp_s_color','temp_f_color','temp_b_color']:
                if k in st.session_state: del st.session_state[k]
            go_to('game')
