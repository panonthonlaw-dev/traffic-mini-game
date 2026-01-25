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

# --- 3. CSS แต่งสีปุ่ม (แยกประเภทชัดเจน) ---
st.markdown("""
    <style>
        /* จัด Layout กึ่งกลาง */
        .block-container {
            max-width: 400px;
            padding-top: 3rem;
            margin: auto;
        }

        /* 1. ปุ่ม "เข้าสู่ระบบ" (ใน Form) -> สีฟ้าเข้ม */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
            width: 100% !important; /* กึ่งกลางเต็มจอ */
            border-radius: 6px !important;
            font-size: 16px !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #166fe5 !important;
        }

        /* 2. ปุ่ม "สร้างบัญชีใหม่" (Primary Button นอก Form) -> สีเขียว */
        div.stButton > button[kind="primary"] {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
            width: 100% !important; /* กึ่งกลางเต็มจอ */
            border-radius: 6px !important;
            font-size: 16px !important;
            margin-top: 10px !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #36a420 !important;
        }

        /* 3. ปุ่ม "ลืมรหัสผ่าน" & "ยกเลิก" (Secondary Button) -> ตัวหนังสือเล็กๆ */
        div.stButton > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #1877f2 !important;
            font-size: 14px !important;
            margin-top: -10px !important;
            width: 100% !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            color: #0d4f9e !important;
            text-decoration: underline !important;
        }

        /* จัด Input ให้สวยงาม */
        input { text-align: center; }
        
        /* ซ่อนลูกตาในช่องรหัสผ่าน */
        button[aria-label="Show password"] { display: none !important; }

        /* หัวข้อ */
        .main-logo { color: #1877f2; font-size: 50px; font-weight: bold; text-align: center; margin-bottom: 0; line-height: 1; }
        .sub-logo { color: #000000; font-size: 20px; text-align: center; margin-bottom: 20px; }

    </style>
""", unsafe_allow_html=True)

# --- 4. ระบบจัดการหน้า (State) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. จัดหน้าจอให้อยู่ตรงกลาง ---
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
            
            # [ปุ่มสีฟ้า] เข้าสู่ระบบ (Form Submit)
            submitted = st.form_submit_button("เข้าสู่ระบบ")
            
            if submitted:
                try:
                    res = supabase.table("users").select("*").eq("username", username).execute()
                    if res.data:
                        if res.data[0]["password"] == password:
                            st.success(f"ยินดีต้อนรับคุณ {res.data[0]['fullname']}")
                            # ใส่โค้ดเปลี่ยนหน้าไปเกมตรงนี้
                        else:
                            st.error("รหัสผ่านไม่ถูกต้อง")
                    else:
                        st.error("ไม่พบชื่อผู้ใช้นี้")
                except Exception as e:
                    st.error(f"Error: {e}")

        # [ตัวหนังสือเล็ก] ลืมรหัสผ่าน
        if st.button("ลืมรหัสผ่านใช่หรือไม่?", type="secondary", use_container_width=True):
            go_to('forgot')

        st.markdown("<hr>", unsafe_allow_html=True)

        # [ปุ่มสีเขียว] สร้างบัญชีใหม่
        # ใช้ type="primary" แล้วเราเอา CSS ไปย้อมสีเขียวให้แล้ว
        if st.button("สร้างบัญชีใหม่", type="primary", use_container_width=True):
            go_to('signup')

    # ==========================================
    # 🟢 SIGNUP (สมัครสมาชิก)
    # ==========================================
    elif st.session_state.page == 'signup':
        st.markdown("<h2 style='text-align: center; color: #1c1e21;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 14px; color: #606770;'>ง่ายและรวดเร็ว</p>", unsafe_allow_html=True)

        with st.form("signup_form"):
            reg_name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อ-นามสกุล")
            reg_user = st.text_input("ชื่อผู้ใช้", placeholder="ภาษาอังกฤษ/ตัวเลข 6-12 ตัว")
            reg_phone = st.text_input("เบอร์โทรศัพท์", placeholder="เบอร์โทร 10 หลัก", max_chars=10)
            reg_pass = st.text_input("รหัสผ่าน", type="password", placeholder="รหัสผ่าน 6-13 ตัว")
            reg_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", placeholder="ยืนยันรหัสผ่าน")
            
            # Hack: ย้อมสีปุ่ม Submit ในหน้านี้ให้เป็นสีเขียวด้วย
            st.markdown("""<style>div[data-testid="stFormSubmitButton"] > button { background-color: #42b72a !important; }</style>""", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("สมัครสมาชิก")
            
            if submitted:
                # Validation Logic
                u_user = reg_user.strip()
                errors = []
                if not reg_name: errors.append("กรุณากรอกชื่อ-นามสกุล")
                if " " in u_user: errors.append("ชื่อผู้ใช้ห้ามเว้นวรรค")
                if not (6 <= len(u_user) <= 12): errors.append("ชื่อผู้ใช้ต้อง 6-12 ตัว")
                if len(reg_phone) != 10 or not reg_phone.isdigit(): errors.append("เบอร์โทรต้องเลข 10 หลัก")
                if not (6 <= len(reg_pass) <= 13): errors.append("รหัสผ่านต้อง 6-13 ตัว")
                if reg_pass != reg_confirm: errors.append("รหัสผ่านไม่ตรงกัน")

                if errors:
                    for err in errors: st.error(err)
                else:
                    try:
                        # เช็คชื่อซ้ำและบันทึก
                        check = supabase.table("users").select("username").eq("username", u_user).execute()
                        if check.data:
                            st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                        else:
                            supabase.table("users").insert({
                                "fullname": reg_name, "username": u_user, "phone": reg_phone, "password": reg_pass
                            }).execute()
                            st.success("สมัครสำเร็จ!")
                            st.balloons()
                            time.sleep(2)
                            go_to('login')
                    except Exception as e:
                        st.error(f"System Error: {e}")

        # ปุ่มย้อนกลับ (ตัวหนังสือเล็ก)
        if st.button("มีบัญชีอยู่แล้ว? เข้าสู่ระบบ", type="secondary", use_container_width=True):
            go_to('login')

    # ==========================================
    # 🟡 FORGOT (ลืมรหัส)
    # ==========================================
    elif st.session_state.page == 'forgot':
        st.markdown("<h3 style='text-align: center;'>ค้นหาบัญชีของคุณ</h3>", unsafe_allow_html=True)
        
        with st.form("forgot_form"):
            find_user = st.text_input("ชื่อผู้ใช้", placeholder="กรอกชื่อผู้ใช้")
            submitted = st.form_submit_button("ค้นหา")
            
            if submitted:
                try:
                    res = supabase.table("users").select("password").eq("username", find_user).execute()
                    if res.data:
                        st.success(f"รหัสผ่านของคุณคือ: {res.data[0]['password']}")
                    else:
                        st.error("ไม่พบข้อมูลผู้ใช้")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.button("ยกเลิก", type="secondary", use_container_width=True):
            go_to('login')
