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

# --- 3. ระบบจัดการหน้า (State Management) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 4. จัด Layout ให้ดูกึ่งกลาง (ใช้ Native Columns ไม่ใช้ CSS Hack) ---
# แบ่งหน้าจอเป็น 3 ส่วน ซ้าย(1)-กลาง(2)-ขวา(1) แล้ววางเนื้อหาตรงกลาง
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # ==========================================
    # 🔵 ส่วนหน้าจอ: เข้าสู่ระบบ (Login)
    # ==========================================
    if st.session_state.page == 'login':
        st.title("🚦 Traffic Game")
        st.subheader("เข้าสู่ระบบ")
        
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้")
            password = st.text_input("รหัสผ่าน", type="password")
            
            # ปุ่ม Submit ใน Form
            submitted = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if submitted:
                # เดี๋ยวมาทำระบบเช็ค Login ตรงนี้
                st.info(f"กำลังตรวจสอบ: {username}")
        
        st.markdown("---") # เส้นคั่นสวยๆ ของ Streamlit
        
        # ปุ่มไปหน้าสมัครสมาชิก
        if st.button("ยังไม่มีบัญชี? สมัครสมาชิก", use_container_width=True):
            go_to('signup')
            
        # ปุ่มลืมรหัส
        if st.button("ลืมรหัสผ่าน", type="secondary", use_container_width=True):
            go_to('forgot')

    # ==========================================
    # 🟢 ส่วนหน้าจอ: สมัครสมาชิก (Signup)
    # ==========================================
    elif st.session_state.page == 'signup':
        st.title("📝 ลงทะเบียน")
        
        with st.form("signup_form"):
            st.write("กรอกข้อมูลเพื่อสร้างบัญชีใหม่")
            
            reg_name = st.text_input("ชื่อ-นามสกุล (ไทย/อังกฤษ)")
            reg_user = st.text_input("ชื่อผู้ใช้ (ภาษาอังกฤษ/ตัวเลข 6-12 ตัว)")
            reg_phone = st.text_input("เบอร์โทรศัพท์ (ตัวเลข 10 หลัก)", max_chars=10)
            reg_pass = st.text_input("รหัสผ่าน (6-13 ตัว)", type="password")
            reg_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")
            
            # ปุ่มยืนยันสมัคร
            submitted = st.form_submit_button("ยืนยันการสมัคร", type="primary", use_container_width=True)
            
            if submitted:
                # 1. Validation Logic (ตรวจสอบเงื่อนไข)
                u_user = reg_user.strip()
                errors = []

                if not reg_name: errors.append("กรุณากรอกชื่อ-นามสกุล")
                if " " in u_user: errors.append("ชื่อผู้ใช้ห้ามมีเว้นวรรค")
                if not (6 <= len(u_user) <= 12): errors.append("ชื่อผู้ใช้ต้องมี 6-12 ตัวอักษร")
                if not reg_phone.isdigit() or len(reg_phone) != 10: errors.append("เบอร์โทรต้องเป็นเลข 10 หลัก")
                if not (6 <= len(reg_pass) <= 13): errors.append("รหัสผ่านต้องมี 6-13 ตัวอักษร")
                if reg_pass != reg_confirm: errors.append("รหัสผ่านไม่ตรงกัน")

                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    # 2. Supabase Logic (บันทึกจริง)
                    try:
                        # เช็คชื่อซ้ำ
                        check = supabase.table("users").select("username").eq("username", u_user).execute()
                        if check.data:
                            st.error(f"❌ ชื่อผู้ใช้ '{u_user}' มีคนใช้แล้ว")
                        else:
                            # บันทึก
                            data = {
                                "fullname": reg_name,
                                "username": u_user,
                                "phone": reg_phone,
                                "password": reg_pass
                            }
                            supabase.table("users").insert(data).execute()
                            
                            st.success("✅ สมัครสมาชิกสำเร็จ!")
                            st.balloons()
                            time.sleep(2)
                            go_to('login')
                            
                    except Exception as e:
                        st.error(f"⚠️ ระบบขัดข้อง: {e}")

        # ปุ่มย้อนกลับ
        if st.button("⬅️ กลับไปหน้าเข้าสู่ระบบ", use_container_width=True):
            go_to('login')

    # ==========================================
    # 🟡 ส่วนหน้าจอ: ลืมรหัสผ่าน (Forgot)
    # ==========================================
    elif st.session_state.page == 'forgot':
        st.title("🔑 ลืมรหัสผ่าน")
        
        with st.form("forgot_form"):
            find_user = st.text_input("กรอกชื่อผู้ใช้ของคุณ")
            submitted = st.form_submit_button("ตรวจสอบบัญชี", type="primary", use_container_width=True)
            
            if submitted:
                st.info("ระบบกู้คืนรหัสผ่านกำลังมา...")
        
        if st.button("ยกเลิก", use_container_width=True):
            go_to('login')
