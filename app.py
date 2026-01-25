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
    st.error("❌ เชื่อมต่อฐานข้อมูลไม่ได้ เช็ค Secrets ด่วน")
    st.stop()

# --- 3. CSS แต่งสีปุ่ม (ตามสั่ง) ---
st.markdown("""
    <style>
        /* จัดกึ่งกลางคอนเทนต์ */
        .block-container {
            max-width: 400px;
            padding-top: 2rem;
            margin: auto;
        }

        /* 1. ปุ่ม "เข้าสู่ระบบ" (Form Submit) -> สีฟ้าเข้ม */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1877f2 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
            font-size: 16px !important;
            width: 100% !important;
            border-radius: 6px !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #166fe5 !important;
        }

        /* 2. ปุ่ม "สมัครสมาชิก" (Regular Button) -> สีเขียว */
        div.stButton > button:not([kind="secondary"]) {
            background-color: #42b72a !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
            font-size: 16px !important;
            width: 100% !important;
            border-radius: 6px !important;
            margin-top: 10px !important;
        }
        div.stButton > button:not([kind="secondary"]):hover {
            background-color: #36a420 !important;
        }

        /* 3. ปุ่ม "ลืมรหัสผ่าน" & "ยกเลิก" (Secondary) -> ทำเป็นตัวหนังสือเล็กๆ หรือปุ่มขาว */
        div.stButton > button[kind="secondary"] {
            border: none !important;
            background: transparent !important;
            color: #1877f2 !important;
            font-size: 14px !important;
            height: auto !important;
            padding: 0 !important;
            margin-top: 5px !important;
            text-decoration: none !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            color: #0d4f9e !important;
            text-decoration: underline !important;
        }
        
        /* จัด Input ให้ตัวหนังสืออยู่ตรงกลาง */
        input { text-align: center; }
        
        /* ซ่อนลูกตาในช่องรหัสผ่าน */
        button[aria-label="Show password"] { display: none !important; }
        
    </style>
""", unsafe_allow_html=True)

# --- 4. ระบบจัดการหน้า (State) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 5. Layout ---
col1, col2, col3 = st.columns([1, 10, 1]) # บีบข้างนิดหน่อยเพื่อให้ดูแน่นขึ้น

with col2:
    # ==========================================
    # 🔵 ส่วนหน้าจอ: เข้าสู่ระบบ (Login)
    # ==========================================
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align: center; color: #1877f2; margin-bottom: 0;'>traffic game</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; margin-top: 0;'>เล่นเปลี่ยนรอด</p>", unsafe_allow_html=True)
        
        # กล่อง Login (ใช้ Form เพื่อให้กด Enter ได้)
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้", label_visibility="collapsed", placeholder="ชื่อผู้ใช้")
            password = st.text_input("รหัสผ่าน", type="password", label_visibility="collapsed", placeholder="รหัสผ่าน")
            
            # [ปุ่มสีฟ้าเข้ม]
            submitted = st.form_submit_button("เข้าสู่ระบบ")
            
            if submitted:
                # --- Login Logic ---
                try:
                    res = supabase.table("users").select("*").eq("username", username).execute()
                    if res.data:
                        user_data = res.data[0]
                        if user_data["password"] == password:
                            st.success(f"ยินดีต้อนรับคุณ {user_data['fullname']}")
                            # ตรงนี้ใส่โค้ดไปหน้าเกมต่อได้เลย
                        else:
                            st.error("รหัสผ่านไม่ถูกต้อง")
                    else:
                        st.error("ไม่พบชื่อผู้ใช้นี้")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

        # [ตัวหนังสือเล็กๆ ล่างปุ่มเข้าสู่ระบบ]
        # ใช้ columns จัดให้ปุ่มอยู่ตรงกลางเป๊ะๆ
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("ลืมรหัสผ่านใช่หรือไม่?", type="secondary", use_container_width=True):
                go_to('forgot')

        st.markdown("---") # เส้นคั่น
        
        # [ปุ่มสีเขียว]
        if st.button("สร้างบัญชีใหม่", use_container_width=True):
            go_to('signup')

    # ==========================================
    # 🟢 ส่วนหน้าจอ: สมัครสมาชิก (Signup)
    # ==========================================
    elif st.session_state.page == 'signup':
        st.markdown("<h2 style='text-align: center;'>สมัครสมาชิก</h2>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            reg_name = st.text_input("ชื่อ-นามสกุล", placeholder="ชื่อ-นามสกุล")
            reg_user = st.text_input("ชื่อผู้ใช้", placeholder="ภาษาอังกฤษ/ตัวเลข 6-12 ตัว")
            reg_phone = st.text_input("เบอร์โทรศัพท์", placeholder="ตัวเลข 10 หลัก", max_chars=10)
            reg_pass = st.text_input("รหัสผ่าน", type="password", placeholder="6-13 ตัวอักษร")
            reg_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", placeholder="ยืนยันรหัสผ่าน")
            
            # ปุ่มใน Form จะเป็นสีฟ้าตาม CSS Submit (ถ้าอยากได้สีเขียว ต้องแก้ CSS หรือย้ายออก)
            # แต่เพื่อให้ Flow สมัครเป็นสีเขียว ผมขออนุญาตใช้ CSS Hack ให้ปุ่ม Submit ในหน้านี้เป็นสีเขียวด้วย
            st.markdown("""<style>div[data-testid="stFormSubmitButton"] > button { background-color: #42b72a !important; }</style>""", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("สมัครสมาชิก")
            
            if submitted:
                # Validation & Supabase Insert (Logic เดิมที่พี่ชอบ)
                u_user = reg_user.strip()
                errors = []
                if not reg_name: errors.append("กรุณากรอกชื่อ-นามสกุล")
                if " " in u_user: errors.append("ชื่อผู้ใช้ห้ามมีเว้นวรรค")
                if not (6 <= len(u_user) <= 12): errors.append("ชื่อผู้ใช้ต้อง 6-12 ตัว")
                if len(reg_phone) != 10: errors.append("เบอร์โทรต้อง 10 หลัก")
                if not (6 <= len(reg_pass) <= 13): errors.append("รหัสผ่านต้อง 6-13 ตัว")
                if reg_pass != reg_confirm: errors.append("รหัสผ่านไม่ตรงกัน")

                if errors:
                    for err in errors: st.error(err)
                else:
                    try:
                        check = supabase.table("users").select("username").eq("username", u_user).execute()
                        if check.data:
                            st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                        else:
                            supabase.table("users").insert({
                                "fullname": reg_name, "username": u_user, "phone": reg_phone, "password": reg_pass
                            }).execute()
                            st.success("สมัครสมาชิกสำเร็จ!")
                            st.balloons()
                            time.sleep(2)
                            go_to('login')
                    except Exception as e:
                        st.error(f"Error: {e}")

        # ปุ่มย้อนกลับ (ตัวหนังสือเล็ก)
        if st.button("มีบัญชีอยู่แล้ว? เข้าสู่ระบบ", type="secondary", use_container_width=True):
            go_to('login')

    # ==========================================
    # 🟡 ส่วนหน้าจอ: ลืมรหัสผ่าน (Forgot)
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
                        st.error("ไม่พบชื่อผู้ใช้นี้ในระบบ")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.button("ยกเลิก", type="secondary", use_container_width=True):
            go_to('login')
