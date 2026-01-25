import streamlit as st
from supabase import create_client
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Traffic Game", page_icon="🚦")

# --- 2. เชื่อมต่อ Supabase ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("❌ เชื่อมต่อ Supabase ไม่ได้ เช็ค Secrets ด่วน")
    st.stop()

# --- 3. CSS แต่งสวย (เหมือนเดิม) ---
st.markdown("""
    <style>
        .block-container { max-width: 400px; padding-top: 2rem; margin: auto; }
        
        /* ปุ่มเข้าสู่ระบบ (ฟ้าเข้ม) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important; color: white !important; border: none !important;
            font-weight: bold !important; height: 45px !important; width: 100% !important; border-radius: 6px !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover { background-color: #166fe5 !important; }

        /* ปุ่มสร้างบัญชี (เขียว) */
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important; color: white !important; border: none !important;
            font-weight: bold !important; height: 45px !important; width: 100% !important; border-radius: 6px !important; margin-top: 10px !important;
        }
        
        /* ปุ่มรอง (ตัวหนังสือเล็ก) */
        div.stButton > button[kind="secondary"] {
            background: transparent !important; border: none !important; color: #1877f2 !important;
            font-size: 14px !important; margin-top: -10px !important; width: 100% !important;
        }
        
        input { text-align: center; }
        button[aria-label="Show password"] { display: none !important; }
        .main-logo { color: #1877f2; font-size: 50px; font-weight: bold; text-align: center; margin-bottom: 0; line-height: 1; }
        .sub-logo { color: #000000; font-size: 20px; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. ระบบจัดการหน้า (State) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user' not in st.session_state:
    st.session_state.user = None

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. จัด Layout ---
col1, col2, col3 = st.columns([1, 8, 1])

with col2:
    # ==========================================
    # 🔵 LOGIN (หน้าแรก)
    # ==========================================
    if st.session_state.page == 'login':
        st.markdown('<div class="main-logo">traffic game</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-logo">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้", label_visibility="collapsed", placeholder="ชื่อผู้ใช้")
            password = st.text_input("รหัสผ่าน", type="password", label_visibility="collapsed", placeholder="รหัสผ่าน")
            
            submitted = st.form_submit_button("เข้าสู่ระบบ")
            
            if submitted:
                try:
                    # เช็ค Login จาก Supabase
                    res = supabase.table("users").select("*").eq("username", username).execute()
                    if res.data:
                        user_data = res.data[0]
                        if user_data["password"] == password:
                            # ✅ ล็อกอินผ่าน! บันทึกข้อมูลคนเล่น แล้วไปหน้าเกม
                            st.session_state.user = user_data
                            st.success(f"ยินดีต้อนรับ {user_data['fullname']}")
                            time.sleep(1)
                            go_to('game') # <--- สั่งเด้งไปหน้าเกมตรงนี้ครับ
                        else:
                            st.error("❌ รหัสผ่านไม่ถูกต้อง")
                    else:
                        st.error("❌ ไม่พบชื่อผู้ใช้นี้")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("ลืมรหัสผ่านใช่หรือไม่?", type="secondary", use_container_width=True):
            go_to('forgot')

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("สร้างบัญชีใหม่", type="primary", use_container_width=True):
            go_to('signup')

    # ==========================================
    # 🎮 GAME PAGE (หน้าเกมหลังล็อกอิน)
    # ==========================================
    elif st.session_state.page == 'game':
        # ดึงชื่อคนเล่นมาโชว์
        current_user = st.session_state.user
        
        st.markdown(f"<h2 style='text-align: center;'>สวัสดีคุณ {current_user['fullname']} 👋</h2>", unsafe_allow_html=True)
        st.info(f"เบอร์โทร: {current_user['phone']}")
        
        st.markdown("---")
        st.subheader("🚦 เริ่มต้นภารกิจ")
        st.write("เลือกด่านที่คุณต้องการเล่น:")
        
        if st.button("ด่านที่ 1: สัญญาณจราจร", use_container_width=True):
            st.warning("กำลังเข้าสู่เกม...")
        
        if st.button("ด่านที่ 2: ทางม้าลาย", use_container_width=True):
            st.warning("กำลังเข้าสู่เกม...")
            
        st.markdown("---")
        
        # ปุ่มออกจากระบบ (Logout) -> เป็นสีแดง
        st.markdown("""<style>div.stButton > button[kind="secondaryForm"] { background-color: #ff4b4b !important; color: white !important; }</style>""", unsafe_allow_html=True)
        
        if st.button("ออกจากระบบ", type="primary", use_container_width=True):
            st.session_state.user = None
            go_to('login')

    # ==========================================
    # 🟢 SIGNUP (หน้าเดิม)
    # ==========================================
    elif st.session_state.page == 'signup':
        st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
        with st.form("signup_form"):
            reg_name = st.text_input("ชื่อ-นามสกุล")
            reg_user = st.text_input("ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)")
            reg_phone = st.text_input("เบอร์โทร (10 หลัก)", max_chars=10)
            reg_pass = st.text_input("รหัสผ่าน (6-13 ตัว)", type="password")
            reg_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")
            
            st.markdown("""<style>div[data-testid="stFormSubmitButton"] > button { background-color: #42b72a !important; }</style>""", unsafe_allow_html=True)
            if st.form_submit_button("สมัครสมาชิก"):
                # (Logic สมัครสมาชิกเดิม...)
                try:
                    if not reg_name or not reg_user or not reg_pass:
                        st.error("กรอกข้อมูลให้ครบ")
                    else:
                        supabase.table("users").insert({
                            "fullname": reg_name, "username": reg_user, "phone": reg_phone, "password": reg_pass
                        }).execute()
                        st.success("สำเร็จ!")
                        time.sleep(1)
                        go_to('login')
                except Exception as e: st.error(f"Error: {e}")

        if st.button("กลับไปหน้าเข้าสู่ระบบ", type="secondary", use_container_width=True):
            go_to('login')

    # ==========================================
    # 🟡 FORGOT (หน้าเดิม)
    # ==========================================
    elif st.session_state.page == 'forgot':
        st.markdown("<h3 style='text-align: center;'>ลืมรหัสผ่าน</h3>", unsafe_allow_html=True)
        with st.form("forgot_form"):
            find_user = st.text_input("ชื่อผู้ใช้")
            if st.form_submit_button("ค้นหา"):
                try:
                    res = supabase.table("users").select("password").eq("username", find_user).execute()
                    if res.data: st.success(f"รหัสคือ: {res.data[0]['password']}")
                    else: st.error("ไม่พบข้อมูล")
                except: st.error("Error")
        
        if st.button("ยกเลิก", type="secondary", use_container_width=True):
            go_to('login')
